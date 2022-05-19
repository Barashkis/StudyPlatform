from aiogram import types
from aiogram.dispatcher import FSMContext

from keyboards import student_kb, education_program_kb, homework_kb, send_homework_kb, student_cd
from loader import dp, db


@dp.callback_query_handler(student_cd.filter(feature="faq"))
async def faq(call: types.CallbackQuery):
    await call.answer()
    await call.message.edit_text("❓ FAQ\n\n"
                                 "Вопрос №1. Можно, не сдавая домашнее задание, перейти к следующему занятию?\n"
                                 "Ответ. Нет, нужно обязательно сдать домашнее задание\n\n"
                                 "Вопрос №2. Все ли задания являются обязательными для выполнения?\n"
                                 "Ответ. Да. Чтобы получить зачет, нужно сдать все. Потом кураторы просуммируют "
                                 "баллы за каждое занятие и сформируют итоговую оценку\n\n"
                                 "Вопрос №3. Будет ли куратор писать мне по поводу домашнего задания?\n"
                                 "Ответ. Да. У кураторов есть функция, позволяющая отправлять сообщения студентам "
                                 "через бота, так что не выключайте уведомления и ожидайте проверок твоих домашек!",
                                 reply_markup=student_kb)


@dp.callback_query_handler(student_cd.filter(feature="check_marks"))
async def check_marks(call: types.CallbackQuery):
    chat_id = call.from_user.id
    user = await db.get_user("Students", chat_id)
    lessons = await db.get_lessons()

    await call.answer()
    await call.message.edit_text(f"📈 СТАТИСТИКА ПРОЙДЕННЫХ ЗАНЯТИЙ\n\n"
                                 f"Процент пройденных занятий: {int(user['passed_homeworks'] / len(lessons) * 100)}%",
                                 reply_markup=student_kb)


@dp.callback_query_handler(student_cd.filter(feature="connect_curator"))
async def connect_curator(call: types.CallbackQuery):
    curators = await db.get_users("Curators")

    if curators:
        text = [
            str(curator[0]) + ". " + f"{curator[1]['full_name']} - @{curator[1]['username']}" if curator[1]['username']
            else f"{curator[0]}. {curator[1]['full_name']} - {curator[1]['full_name_tg']}"
            for curator in enumerate(curators, start=1)]
        text.insert(0, "👨‍💻 КОНТАКТЫ КУРАТОРОВ\n")
    else:
        text = ["В системе пока нет кураторов..."]

    await call.answer()
    await call.message.edit_text("\n".join(text),
                                 reply_markup=student_kb)


@dp.callback_query_handler(student_cd.filter(feature="education_program"))
async def education_program(call: types.CallbackQuery):
    chat_id = call.from_user.id

    current_lesson = await db.get_current_lesson(chat_id)

    if current_lesson["homework_id"]:
        kb = education_program_kb()
    else:
        kb = education_program_kb(False)

    await call.answer()
    await call.message.edit_text(f"🎓 ОБРАЗОВАТЕЛЬНАЯ ПРОГРАММА\n\n"
                                 f"Урок №{current_lesson['id']}. {current_lesson['title']}\n\n"
                                 f"{current_lesson['text']}",
                                 reply_markup=kb)


@dp.callback_query_handler(student_cd.filter(feature="next_lesson"))
async def display_next_lesson(call: types.CallbackQuery):
    chat_id = call.from_user.id
    user = await db.get_user("Students", chat_id)
    lessons = await db.get_lessons()

    if user["passed_homeworks"] == user["current_lesson_id"] == len(lessons):
        await call.answer("Наши поздравления! Ты закончил все уроки!👏\n"
                          "Теперь дело за кураторами: они просуммируют баллы за твои ответы "
                          "и выставят итоговую оценку",
                          show_alert=True)
    elif user["passed_homeworks"] == user["current_lesson_id"]:
        await db.update_current_lesson_id(chat_id)

        current_lesson = await db.get_current_lesson(chat_id)

        if current_lesson["homework_id"]:
            kb = education_program_kb()
        else:
            await db.pass_homework(chat_id)
            kb = education_program_kb(False)

        await call.answer()
        await call.message.edit_text(f"🎓 ОБРАЗОВАТЕЛЬНАЯ ПРОГРАММА\n\n"
                                     f"Урок №{current_lesson['id']}. {current_lesson['title']}\n\n"
                                     f"{current_lesson['text']}",
                                     reply_markup=kb)
    else:
        await call.answer("Необходимо сдать домашнее задание, чтобы получить доступ к следующему уроку!",
                          show_alert=True)


@dp.callback_query_handler(student_cd.filter(feature="homework"))
async def open_homework(call: types.CallbackQuery):
    chat_id = call.from_user.id
    user = await db.get_user("Students", chat_id)

    if user["passed_homeworks"] == user["current_lesson_id"]:
        await call.answer("Ты уже сдал это домашнее задание!",
                          show_alert=True)
    else:
        homework = await db.get_current_homework(chat_id)

        await call.message.edit_text(f"✍ ДОМАШНЕЕ ЗАДАНИЕ №{homework['homework_id']}\n\n"
                                     f"{homework['text']}",
                                     reply_markup=homework_kb)


@dp.callback_query_handler(student_cd.filter(feature="input_homework"))
async def input_homework(call: types.CallbackQuery, state: FSMContext):
    await call.message.edit_reply_markup()
    await call.message.answer("Напиши свой ответ")

    await state.set_state("input_answer")


@dp.message_handler(state="input_answer")
async def last_chance_homework(message: types.Message, state: FSMContext):
    await state.finish()

    async with state.proxy() as data:
        data["answer"] = message.text

    await message.answer("Ты точно уверен в своем ответе? Дальше ты никак не сможешь изменить его",
                         reply_markup=send_homework_kb)


@dp.callback_query_handler(student_cd.filter(feature="send_homework"))
async def send_homework(call: types.CallbackQuery, state: FSMContext):
    await state.set_state("input_answer")

    data = await state.get_data()
    answer = data["answer"]

    await state.finish()

    chat_id = call.from_user.id
    homework = await db.get_current_homework(chat_id)
    homework_id = homework["homework_id"]

    await db.add_answer(chat_id, answer, homework_id)
    await db.pass_homework(chat_id)

    user = await db.get_user("Students", chat_id)
    current_lesson_id = user["current_lesson_id"]

    current_lesson = await db.get_current_lesson(chat_id)

    if current_lesson["homework_id"]:
        kb = education_program_kb()
    else:
        kb = education_program_kb(False)

    await call.message.edit_text(f"🎓 ОБРАЗОВАТЕЛЬНАЯ ПРОГРАММА\n\n"
                                 f"Урок №{current_lesson_id}. {current_lesson['title']}\n\n"
                                 f"{current_lesson['text']}",
                                 reply_markup=kb)


@dp.callback_query_handler(student_cd.filter(feature="menu"))
async def back_to_student_menu(call: types.CallbackQuery):
    await call.message.edit_text("Выбери раздел, который тебя интересует",
                                 reply_markup=student_kb)
