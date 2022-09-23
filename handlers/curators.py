from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.utils.markdown import hbold
from aiogram.utils.exceptions import BotBlocked

from keyboards import curator_kb, curator_cd, homework_cd, send_message_kb, homeworks_to_check_kb, send_feedback_kb
from loader import dp, db, bot


async def students_list_message():
    students = await db.get_users("Students")

    if not len(students):
        await types.CallbackQuery.get_current().answer()
        await types.CallbackQuery.get_current().message.edit_text("В системе пока нет студентов...",
                                                                  reply_markup=curator_kb)

        return

    text = [f"{student[0]}. {student[1]['full_name']}, email - {student[1]['email']} (остановил бота)" if student[1]["leave"]
            else f"{student[0]}. {student[1]['full_name']}"
            for student in enumerate(students, start=1)]

    return text


@dp.callback_query_handler(curator_cd.filter(feature="faq"))
async def faq(call: types.CallbackQuery):
    await call.answer()
    await call.message.edit_text("❓ FAQ\n\n"
                                 "Как работать с чат-ботом\n\n"
                                 f"Чтобы увидеть, кто находится в вашей группе, нажмите на кнопку {hbold('«Моя группа»')}. "
                                 "Здесь отобразится список ваших студентов и их контакты, а также сведения, на каком "
                                 "уроке находятся пользователи\n\n"
                                 "Чтобы связаться с одним или всеми студентами Вашей группы, нажмите на кнопку "
                                 f"{hbold('«Связаться со студентами»')}. Далее выберите одного "
                                 f"студента или всех студентов, чтобы отправить сообщение в чат-боте\n\n"
                                 "Студенты присылают вам домашние задания на проверку. Чтобы приступить к проверке "
                                 f"заданий, нажмите на кнопку {hbold('«Проверка заданий»')}. "
                                 f"Укажите номер задания, которое хотите "
                                 "проверить, и отправьте обратную связь по домашнему заданию\n\n",
                                 reply_markup=curator_kb)


@dp.callback_query_handler(curator_cd.filter(feature="students_list"))
async def group_list(call: types.CallbackQuery, state: FSMContext):
    text = await students_list_message()

    if not text:
        return

    text.insert(0, "📋 СПИСОК ГРУППЫ\n")

    await call.message.edit_text("\n".join(text))
    await call.message.answer(f"Введите {hbold('номер студента')}, информацию о котором необходимо узнать\n\n"
                              f"Чтобы узнать информацию о нескольких студентах,"
                              f" введите их {hbold('номера через пробел')} (например, 1 3 7)\n\n"
                              f"Чтобы выбрать всех, напишите: {hbold('all')}")

    await state.set_state("choose_students_info")


@dp.message_handler(state="choose_students_info")
async def show_students(message: types.Message, state: FSMContext):
    await state.reset_state(with_data=False)

    text = message.text
    selected_id = set(text.split())
    students = await db.get_users("Students")
    edge = len(students)
    lessons = await db.get_lessons()
    result_message = []

    if text == "all":
        for student in enumerate(students, start=1):
            chat_id = student[1]['chat_id']
            lesson = await db.get_current_lesson(chat_id)

            result_message.append(f"{student[0]}. {student[1]['full_name']}\n"
                                  f"Сейчас изучает урок №{lesson['id']} - \'{lesson['title']}\'\n"
                                  f"Прогресс - {int(student[1]['passed_lessons'] / len(lessons) * 100)}%\n"
                                  f"Имя в Телеграме - {student[1]['full_name_tg']}\n")

        result_message.insert(0, "📋 ИНФОРМАЦИЯ О СТУДЕНТАХ\n")

        await message.answer("\n".join(result_message),
                             reply_markup=curator_kb)
    else:
        selected_id = list(map(int, selected_id))
        list_is_correct_id = map(lambda x: 1 <= x <= edge, selected_id)

        if all(list_is_correct_id):
            for student_id in enumerate(selected_id, start=1):
                chat_id = students[student_id[1] - 1]['chat_id']
                lesson = await db.get_current_lesson(chat_id)

                result_message.append(f"{student_id[0]}. {students[student_id[1] - 1]['full_name']}\n"
                                      f"Сейчас изучает урок №{lesson['id']} - \'{lesson['title']}\'\n"
                                      f"Прогресс - {int(students[student_id[1] - 1]['passed_lessons'] / len(lessons) * 100)}%\n"
                                      f"Имя в Телеграме - {students[student_id[1] - 1]['full_name_tg']}\n")

            result_message.insert(0, "📋 ИНФОРМАЦИЯ О СТУДЕНТАХ\n")

            await message.answer("\n".join(result_message),
                                 reply_markup=curator_kb)
        else:
            raise ValueError


@dp.callback_query_handler(curator_cd.filter(feature="connect_student"))
async def connect_student(call: types.CallbackQuery, state: FSMContext):
    text = await students_list_message()

    if not text:
        return

    text.insert(0, "🤝 СВЯЗАТЬСЯ СО СТУДЕНТОМ\n")

    await call.message.edit_text("\n".join(text))
    await call.message.answer(f"Введите {hbold('номер студента')}, которому необходимо отправить сообщение\n\n"
                              f"Чтобы связаться с несколькими студентами, введите их {hbold('номера через пробел')} "
                              f"(например, 1 3 7)\n\n"
                              f"Чтобы выбрать всех, напишите: {hbold('all')}")

    await state.set_state("choose_students_connect")


@dp.message_handler(state="choose_students_connect")
async def select_students_to_connect(message: types.Message, state: FSMContext):
    text = message.text
    selected_id = set(text.split())
    students = await db.get_users("Students")
    edge = len(students)

    if text == "all":
        async with state.proxy() as data:
            data["to_connect"] = list(range(1, edge + 1))
    else:
        selected_id = list(map(int, selected_id))
        list_is_correct_id = map(lambda x: 1 <= x <= edge, selected_id)

        if all(list_is_correct_id):
            async with state.proxy() as data:
                data["to_connect"] = selected_id
        else:
            raise ValueError

    await state.reset_state(with_data=False)

    await message.answer("Отлично! Теперь введите сообщение, которое Вы хотите отослать выбранным студентам")

    await state.set_state("message")


@dp.message_handler(state="message")
async def select_students_to_connect(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["message"] = message.text
    await state.reset_state(with_data=False)

    await message.answer("Вы точно хотите отправить сообщение? Дальше Вы никак не сможете изменить его",
                         reply_markup=send_message_kb)


@dp.callback_query_handler(curator_cd.filter(feature="message"))
async def send_message_to_student(call: types.CallbackQuery, state: FSMContext):
    curator_chat_id = call.from_user.id
    curator = await db.get_user("Curators", curator_chat_id)

    await state.set_state("message")
    data = await state.get_data()
    text = f"📧 ТЕБЕ ПРИШЛО СООБЩЕНИЕ\n\n" \
           f"Куратор {curator['full_name']} написал:\n" \
           f"{data['message']}"

    await state.set_state("choose_students_connect")
    data = await state.get_data()
    to_connect = data["to_connect"]
    await state.reset_state(with_data=False)

    students = await db.get_users("Students")
    for student_id in to_connect:
        student = students[student_id - 1]
        chat_id = student["chat_id"]

        try:
            await bot.send_message(chat_id, text)
        except BotBlocked as ex:
            print(ex)

    await call.message.edit_text("Сообщение было отправлено",
                                 reply_markup=curator_kb)


@dp.callback_query_handler(curator_cd.filter(feature="check_tasks"))
async def show_homeworks_to_check(call: types.CallbackQuery):
    await call.answer()

    kb = await homeworks_to_check_kb()

    if kb["inline_keyboard"]:
        await call.message.edit_text("На текущий момент имеются ответы на следующие домашние задания. "
                                     "Выберете домашнее задание, ответы на которое Вы хотите проверить",
                                     reply_markup=kb)
    else:
        await call.message.edit_text("Доступных для проверки ответов на домашние задания пока нет...",
                                     reply_markup=curator_kb)


@dp.callback_query_handler(homework_cd.filter())
async def check_homework(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    homework_id = int(callback_data["homework_id"])

    await state.set_state("choose_student_homework_feedback")
    async with state.proxy() as data:
        data["homework_id"] = homework_id

    answers = await db.get_answers(homework_id)

    text = []
    for answer in enumerate(answers, start=1):
        chat_id = answer[1]["student_chat_id"]
        student = await db.get_user("Students", chat_id)
        text.append(f"{answer[0]}. Студент {student['full_name']}")
    text.insert(0, "✍ ОТВЕТЫ, КОТОРЫЕ НУЖНО ПРОВЕРИТЬ\n")

    await call.message.edit_text("\n".join(text))
    await call.message.answer("Введите номер студента,ответ которого Вы хотите проверить")


@dp.message_handler(state="choose_student_homework_feedback")
async def select_student_to_homework_feedback(message: types.Message, state: FSMContext):
    data = await state.get_data()
    homework_id = data["homework_id"]

    answer_id = int(message.text)
    answers = await db.get_answers(homework_id)
    edge = len(answers)

    if 1 <= answer_id <= edge:
        async with state.proxy() as data:
            data["to_feedback"] = answer_id
    else:
        raise ValueError

    await state.reset_state(with_data=False)

    answer = answers[answer_id - 1]
    chat_id = answer["student_chat_id"]
    student = await db.get_user("Students", chat_id)

    answer_text = f"ОТВЕТ СТУДЕНТА - {student['full_name']}\n\n"
    if answer["text"]:
        answer_text += answer["text"]

    if answer["video"]:
        await message.answer_video(video=answer["video"],
                                   caption=answer_text)
    elif answer["photo"]:
        await message.answer_photo(photo=answer["photo"],
                                   caption=answer_text)
    elif answer["document"]:
        await message.answer_document(document=answer["document"],
                                      caption=answer_text)
    else:
        await message.answer(answer_text)

    await message.answer("Напишите сообщение по этому ответу")
    await state.set_state("feedback")


@dp.message_handler(state="feedback")
async def select_students_to_connect(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["message"] = message.text
    await state.reset_state(with_data=False)

    await message.answer("Вы точно хотите отправить сообщение? Дальше Вы никак не сможете изменить его",
                         reply_markup=send_feedback_kb)


@dp.callback_query_handler(curator_cd.filter(feature="feedback"))
async def send_message_to_student(call: types.CallbackQuery, state: FSMContext):
    curator_chat_id = call.from_user.id
    curator = await db.get_user("Curators", curator_chat_id)

    await state.set_state("choose_student_homework_feedback")
    data = await state.get_data()
    homework_id = data["homework_id"]
    to_feedback = int(data["to_feedback"])

    await state.set_state("feedback")
    data = await state.get_data()
    text = f"📧 РЕЦЕНЗИЯ НА ДОМАШНЕЕ ЗАДАНИЕ №{homework_id}\n\n" \
           f"Куратор {curator['full_name']} написал:\n" \
           f"{data['message']}"
    await state.reset_state(with_data=False)

    students = await db.get_users("Students")
    student = students[to_feedback - 1]
    chat_id = student["chat_id"]

    answer = await db.get_answer(chat_id)

    try:
        if not answer["checked"]:
            await db.check_answer(chat_id, homework_id)
            await bot.send_message(chat_id, text)

            await call.message.edit_text("Сообщение было отправлено",
                                         reply_markup=curator_kb)
        else:
            await call.message.edit_text("Ответ этого студента уже был проверен другим куратором",
                                         reply_markup=curator_kb)
    except BotBlocked:
        await call.message.edit_text("Сообщение не было отправлено, так как этот студент заблокировал бота. "
                                     "Однако задание было отмечено как проверенное",
                                     reply_markup=curator_kb)


@dp.callback_query_handler(curator_cd.filter(feature="menu"))
async def back_to_curator_menu(call: types.CallbackQuery):
    await call.message.edit_text("Выберите раздел, который Вас интересует",
                                 reply_markup=curator_kb)
