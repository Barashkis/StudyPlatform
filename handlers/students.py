from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.utils.markdown import hbold
from aiogram.utils.exceptions import MessageTextIsEmpty

from keyboards import student_kb, education_program_kb, homework_kb, send_homework_kb, student_cd, archive_lessons_kb
from loader import dp, db


@dp.callback_query_handler(student_cd.filter(feature="faq"))
async def faq(call: types.CallbackQuery):
    await call.answer()
    await call.message.edit_text("❓ FAQ\n\n"
                                 "Привет! Рассказываем о функционале чат-бота:\n"
                                 "Чтобы получить материалы урока, нажми "
                                 f"на кнопку {hbold('«Прохождение программы обучения»')}\n\n"
                                 f"После просмотра материала нажми на кнопку {hbold('«Домашнее задание»')}, "
                                 f"чтобы получить задание\n\n"
                                 f"Когда будешь готов, нажимай на кнопку {hbold('«Сдать»')} и "
                                 "отправляй боту подготовленные материалы: текст или файл. Задание автоматически будет "
                                 "добавлено твоему куратору на проверку\n\n"
                                 f"Если тебе придёт сообщение со словом {hbold('«РЕЦЕНЗИЯ»')} — это ответ твоего "
                                 f"куратора на твоё домашнее задание. Куратор также может присылать "
                                 f"тебе пуш-сообщения с важными новостями\n\n"
                                 f"При желании обсудить домашнее задание, ты можешь нажать "
                                 f"на кнопку {hbold('«Связь в куратором»')} и получить контактные "
                                 f"данные для связи с твоим "
                                 f"куратором. Также ты можешь познакомиться со своей группой, "
                                 f"для этого просто нажми на кнопку «Моя группа»\n\n"
                                 f"Все пройденные задания хранятся в архиве, ты можешь получить к ним доступ, нажав на "
                                 f"кнопку {hbold('«Архив»')}. Здесь ты можешь "
                                 f"вернуться к любому уроку и повторить материал\n\n"
                                 "Обрати внимание, что ты не можешь перейти к следующему уроку, пока домашнее задание "
                                 "к предыдущему уроку не отправлено на проверку куратору\n\n"
                                 "Удачи!",
                                 reply_markup=student_kb)


@dp.callback_query_handler(student_cd.filter(feature="check_marks"))
async def check_marks(call: types.CallbackQuery):
    chat_id = call.from_user.id
    user = await db.get_user("Students", chat_id)
    lessons = await db.get_lessons()

    await call.answer()
    await call.message.edit_text(f"📈 СТАТИСТИКА ПРОЙДЕННЫХ ЗАНЯТИЙ\n\n"
                                 f"Процент пройденных занятий: {int(user['passed_lessons'] / len(lessons) * 100)}%",
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
        kb = education_program_kb(has_homework=False)

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

    if user["passed_lessons"] == user["current_lesson_id"] == len(lessons):
        await call.answer("Наши поздравления! Ты закончил все уроки👏\n"
                          "Теперь дело за кураторами: они проверят все "
                          "работы и вскоре ты получишь долгожданную награду!",
                          show_alert=True)
    elif user["passed_lessons"] == user["current_lesson_id"]:
        await db.update_current_lesson_id(chat_id)

        current_lesson = await db.get_current_lesson(chat_id)

        if current_lesson["homework_id"]:
            kb = education_program_kb()
        else:
            await db.pass_homework(chat_id)
            kb = education_program_kb(has_homework=False)

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

    if user["passed_lessons"] == user["current_lesson_id"]:
        await call.answer("Ты уже сдал это домашнее задание!",
                          show_alert=True)
    else:
        homework = await db.get_current_homework(chat_id)

        await call.message.edit_text(f"✍ ДОМАШНЕЕ ЗАДАНИЕ №{homework['id']}\n\n"
                                     f"{homework['text']}",
                                     reply_markup=homework_kb)


@dp.callback_query_handler(student_cd.filter(feature="input_homework"))
async def input_homework(call: types.CallbackQuery, state: FSMContext):
    await call.message.edit_reply_markup()
    await call.message.answer("Твой ответ")

    await state.set_state("input_answer")


@dp.message_handler(state="input_answer", content_types=types.ContentTypes.TEXT | types.ContentTypes.PHOTO |
                    types.ContentTypes.VIDEO | types.ContentTypes.DOCUMENT)
async def last_chance_homework(message: types.Message, state: FSMContext):
    await state.reset_state(with_data=False)

    answer = {
        "text": None,
        "photo": None,
        "video": None,
        "document": None
    }
    try:
        answer["text"] = message.caption
    except MessageTextIsEmpty:
        pass

    if message.content_type == "text":
        answer["text"] = message.text
    elif message.content_type == "photo":
        answer["photo"] = message.photo[-1].file_id
    elif message.content_type == "video":
        answer["video"] = message.video.file_id
    else:
        answer["document"] = message.document.file_id

    async with state.proxy() as data:
        data["answer"] = answer

    await message.answer("Ты точно уверен в своем ответе? Дальше ты никак не сможешь изменить его",
                         reply_markup=send_homework_kb)


@dp.message_handler(state="input_answer", content_types=types.ContentType.ANY)
async def last_chance_homework_any(message: types.Message):
    await message.answer("Я не поддерживаю данный тип сообщений для сдачи домашнего задания. Ты можешь отправлять "
                         "мне текст, видео, фото или документ (1 шт.)")


@dp.callback_query_handler(student_cd.filter(feature="send_homework"))
async def send_homework(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    answer = data["answer"]
    text = answer["text"]
    photo = answer["photo"]
    video = answer["video"]
    document = answer["document"]

    chat_id = call.from_user.id
    homework = await db.get_current_homework(chat_id)
    homework_id = homework["id"]

    await db.add_answer(chat_id, text, photo, video, document, homework_id)
    await db.pass_homework(chat_id)

    user = await db.get_user("Students", chat_id)
    current_lesson_id = user["current_lesson_id"]

    current_lesson = await db.get_current_lesson(chat_id)

    kb = education_program_kb()

    await call.message.edit_text(f"🎓 ОБРАЗОВАТЕЛЬНАЯ ПРОГРАММА\n\n"
                                 f"Урок №{current_lesson_id}. {current_lesson['title']}\n\n"
                                 f"{current_lesson['text']}",
                                 reply_markup=kb)


@dp.callback_query_handler(student_cd.filter(feature="menu"))
async def back_to_student_menu(call: types.CallbackQuery):
    await call.message.edit_text("Выбери раздел, который тебя интересует",
                                 reply_markup=student_kb)


@dp.callback_query_handler(student_cd.filter())
async def display_archive(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    feature = callback_data["feature"]

    if feature == "archive":
        async with state.proxy() as data:
            if data.get("archive_lesson_id") is None:
                data["archive_lesson_id"] = 1
    elif feature == "next_archive":
        async with state.proxy() as data:
            data["archive_lesson_id"] += 1
    else:
        async with state.proxy() as data:
            data["archive_lesson_id"] -= 1

    data = await state.get_data()
    archive_lesson_id = data["archive_lesson_id"]

    archive_lesson = await db.get_lesson(archive_lesson_id)

    chat_id = call.from_user.id
    current_lesson = await db.get_current_lesson(chat_id)
    current_lesson_id = current_lesson["id"]

    archive_kb = archive_lessons_kb(archive_lesson_id, current_lesson_id)

    await call.answer()
    await call.message.edit_text(f"📦 АРХИВ\n\n"
                                 f"Урок №{archive_lesson['id']}. {archive_lesson['title']}\n\n"
                                 f"{archive_lesson['text']}",
                                 reply_markup=archive_kb)
