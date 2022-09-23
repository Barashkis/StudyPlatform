import asyncio

import gspread
from config import SHEET_URL

from loader import db


gc = gspread.service_account()


async def update_db():
    while True:
        sh = gc.open_by_url(SHEET_URL)

        lessons = await db.get_lessons()
        homeworks = await db.get_homeworks()

        lesson_id = 1
        homework_id = 1
        for row in sh.sheet1.get_all_values()[1:]:
            title = row[1]
            lesson_text = row[2]
            homework_text = row[3]

            if not homework_text:
                homework_id_for_lesson = None
            else:
                homework_id_for_lesson = homework_id

            if not all([title, lesson_text]):
                break

            if lesson_id <= len(lessons):
                await db.update_lesson(lesson_id, title, lesson_text, homework_id_for_lesson)
            else:
                await db.add_lesson(title, lesson_text, homework_id_for_lesson)

            if homework_text:
                if homework_id <= len(homeworks):
                    await db.update_homework(homework_text, homework_id)
                else:
                    await db.add_homework(homework_text)

                homework_id += 1

            lesson_id += 1

        await asyncio.sleep(120)
