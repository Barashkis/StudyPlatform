from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import CommandStart

from keyboards.inline_keyboards import start_kb, curator_kb, student_kb, start_cd
from loader import dp, db, bot

from config import CURATOR_PASS


@dp.message_handler(CommandStart())
async def start(message: types.Message):
    chat_id = message.from_user.id
    user_student = await db.get_user("Students", chat_id)
    user_curator = await db.get_user("Curators", chat_id)

    if user_curator or user_student:
        if user_curator:
            await message.answer("Выбери раздел, который тебя интересует", reply_markup=curator_kb)
        else:
            await message.answer("Выбери раздел, который тебя интересует", reply_markup=student_kb)
    else:
        await message.answer("Сперва необходимо зарегистрироваться. Выбери пользователя", reply_markup=start_kb)


@dp.callback_query_handler(start_cd.filter())
async def start_auth(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    await state.set_state("is_curator")
    async with state.proxy() as data:
        if callback_data["type"] == "curator":
            data["is_curator"] = True
        else:
            data["is_curator"] = False

    await call.message.edit_text("Введи свой ФИО")

    await state.set_state("full_name")


@dp.message_handler(state="full_name")
async def get_full_name(message: types.Message, state: FSMContext):
    full_name = message.text

    await state.set_state("is_curator")
    data = await state.get_data()
    is_curator = data["is_curator"]

    if is_curator:
        async with state.proxy() as data:
            data["full_name"] = full_name
        await state.reset_state(with_data=False)

        await message.answer("Для того, чтобы получить доступ к функционалу куратора, нужно ввести пароль. "
                             "Так мы убедимся, что ты не студент, который хочет быть куратором :)")
        await state.set_state("password")
    else:
        chat_id = message.from_user.id
        username = message.from_user.username
        full_name_tg = message.from_user.full_name

        await db.add_student(chat_id, username, full_name_tg, full_name)
        await bot.send_sticker(chat_id, "CAACAgIAAxkBAAEEslFieqWUgKY_zwUVBhlPWnrpsp1mjwACQhAAAjPFKUmQDtQRpypKgiQE")
        await message.answer("Добро пожаловать на программу «Я – оратор. Как научиться выступать публично»! "
                             "Сегодня навык публичных выступлений один из самых "
                             "востребованных и включает в себя большое количество аспектов, "
                             "которые невозможно охватить, пройдя один тренинг или вебинар. Именно поэтому"
                             " мы создали для вас уникальную "
                             "возможность изучить все необходимые инструменты и познакомиться "
                             "с основными принципами подготовки и проведения "
                             "публичных выступлений в одном месте в рамках одного обучения\n\n"
                             "В ходе прохождения программы вы узнаете\n"
                             "- что такое личный бренд\n"
                             "- как управлять впечатлением аудитории\n"
                             "- как формулировать цель своего выступления и формировать структуру презентации\n"
                             "- как готовить презентационный материал\n"
                             "- что такое природа волнения и техники по работе с ним\n"
                             "- как сделать свою подачу яркой и запоминающейся\n"
                             "- кто такие сложные участники и как взаимодействовать с ними, "
                             "а также техники по работе с вопросами от аудитории\n\n"
                             "Программа состоит из теоретических блоков в формате видеороликов и домашних "
                             "заданий на отработку. Это позволит"
                             "вам потренировать полученные знания и в дальнейшем облегчит использование их в "
                             "реальных рабочих ситуациях")
        await message.answer("Выбери раздел, который тебя интересует", reply_markup=student_kb)
        await state.reset_state(with_data=False)


@dp.message_handler(state="password")
async def get_email_and_register(message: types.Message, state: FSMContext):
    await state.set_state("full_name")
    data = await state.get_data()
    full_name = data["full_name"]

    chat_id = message.from_user.id
    username = message.from_user.username
    full_name_tg = message.from_user.full_name
    password = message.text
    if password == CURATOR_PASS:
        await db.add_curator(chat_id, username, full_name_tg, full_name)
        await message.answer("Добро пожаловать на программу «Я – оратор. Как научиться выступать публично»!\n\n"
                             "Вы стали куратором группы. В этом чат-боте Вы сможете проверять домашние "
                             "задания Ваших студентов и отправлять им пуш-сообщения с важными новостями")
        await message.answer("Выберите раздел, который Вас интересует", reply_markup=curator_kb)
    else:
        await message.answer("Пароль оказался неверным. Выбери пользователя", reply_markup=start_kb)

    await state.reset_state(with_data=False)
