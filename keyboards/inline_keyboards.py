from aiogram.utils.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from loader import db

start_cd = CallbackData("user", "type")
curator_cd = CallbackData("curator", "feature")
student_cd = CallbackData("student", "feature")
homework_cd = CallbackData("homework", "homework_id")

start_kb = InlineKeyboardMarkup(
    inline_keyboard=[
            [
                InlineKeyboardButton(text="👨‍🎓Студент", callback_data=start_cd.new("student")),
            ],
            [
                InlineKeyboardButton(text="👨‍💻Куратор", callback_data=start_cd.new("curator"))
            ]
    ]
)

curator_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Посмотреть список группы", callback_data=curator_cd.new("students_list"))
        ],
        [
            InlineKeyboardButton(text="Связаться со студентом", callback_data=curator_cd.new("connect_student"))
        ],
        [
            InlineKeyboardButton(text="Проверка заданий", callback_data=curator_cd.new("check_tasks"))
        ],
        [
            InlineKeyboardButton(text="FAQ", callback_data=curator_cd.new("faq"))
        ]
    ]
)

student_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Прохождение программы обучения", callback_data=student_cd.new("education_program"))
        ],
        [
            InlineKeyboardButton(text="Проверка успеваемости", callback_data=student_cd.new("check_marks"))
        ],
        [
            InlineKeyboardButton(text="Связь с куратором", callback_data=student_cd.new("connect_curator"))
        ],
        [
            InlineKeyboardButton(text="Архив", callback_data=student_cd.new("archive"))
        ],
        [
            InlineKeyboardButton(text="FAQ", callback_data=student_cd.new("faq"))
        ]
    ]
)

homework_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Назад", callback_data=student_cd.new("education_program")),
            InlineKeyboardButton(text="Сдать домашнее задание", callback_data=student_cd.new("input_homework"))
        ]
    ]
)

send_homework_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Назад", callback_data=student_cd.new("homework")),
            InlineKeyboardButton(text="Отправить", callback_data=student_cd.new("send_homework"))
        ]
    ]
)

send_message_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Назад", callback_data=curator_cd.new("menu")),
            InlineKeyboardButton(text="Отправить", callback_data=curator_cd.new("message"))
        ]
    ]
)

send_feedback_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Назад", callback_data=curator_cd.new("menu")),
            InlineKeyboardButton(text="Отправить", callback_data=curator_cd.new("feedback"))
        ]
    ]
)


async def homeworks_to_check_kb():
    homeworks = await db.get_homeworks()
    homework_ids = [homework["id"] for homework in homeworks]
    kb = InlineKeyboardMarkup()

    for homework_id in homework_ids:
        answers = await db.get_answers(homework_id)

        if answers:
            kb.add(InlineKeyboardButton(text=f"Домашнее задание №{homework_id}",
                                        callback_data=homework_cd.new(homework_id)))

    return kb


def education_program_kb(has_homework=True):
    kb = InlineKeyboardMarkup()
    button_1 = InlineKeyboardButton(text="Домашнее задание", callback_data=student_cd.new("homework"))
    button_2 = InlineKeyboardButton(text="Следующий урок", callback_data=student_cd.new("next_lesson"))
    button_3 = InlineKeyboardButton(text="Назад", callback_data=student_cd.new("menu"))

    if has_homework:
        kb.add(button_1, button_2)
        kb.add(button_3)
    else:
        kb.add(button_3, button_2)

    return kb


def archive_lessons_kb(lesson_id, edge):
    kb = InlineKeyboardMarkup()
    button_1 = InlineKeyboardButton(text="Предыдущий", callback_data=student_cd.new("previous_archive"))
    button_2 = InlineKeyboardButton(text="Следующий", callback_data=student_cd.new("next_archive"))
    button_3 = InlineKeyboardButton(text="Назад", callback_data=student_cd.new("menu"))

    if edge == 1:
        pass
    elif lesson_id == 1:
        kb.add(button_2)
    elif lesson_id == edge:
        kb.add(button_1)
    else:
        kb.add(button_1, button_2)

    kb.add(button_3)

    return kb
