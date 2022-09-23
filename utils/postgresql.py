import asyncio
import asyncpg

import config


class Database:
    def __init__(self, loop: asyncio.AbstractEventLoop):
        self.pool: asyncpg.Pool = loop.run_until_complete(
            asyncpg.create_pool(
                user=config.PG_USER,
                password=config.PG_PASS,
                host=config.PG_HOST
            )
        )

    async def create_all_tables(self):
        sql = """
        CREATE TABLE IF NOT EXISTS Students (
        id SERIAL NOT NULL,
        chat_id BIGINT,
        username VARCHAR(100),
        full_name_tg VARCHAR(100),
        full_name VARCHAR(100),
        passed_lessons INT DEFAULT 0 NOT NULL,
        current_lesson_id INT DEFAULT 1 NOT NULL,
        leave BOOLEAN DEFAULT FALSE,
        PRIMARY KEY (chat_id)
        );
        
        CREATE TABLE IF NOT EXISTS Curators (
        id SERIAL NOT NULL,
        chat_id BIGINT,
        username VARCHAR(100),
        full_name_tg VARCHAR(100),
        full_name VARCHAR(100),
        PRIMARY KEY (id)
        );
        
        CREATE TABLE IF NOT EXISTS Lessons (
        id SERIAL NOT NULL,
        title VARCHAR,
        text VARCHAR,
        homework_id INT,
        PRIMARY KEY (id)
        );
        
        CREATE TABLE IF NOT EXISTS Homeworks (
        id SERIAL NOT NULL,
        text VARCHAR,
        PRIMARY KEY (id)
        );
        
        CREATE TABLE IF NOT EXISTS Answers (
        id SERIAL NOT NULL,
        text VARCHAR DEFAULT NULL,
        video VARCHAR DEFAULT NULL,
        photo VARCHAR DEFAULT NULL,
        document VARCHAR DEFAULT NULL,
        student_chat_id INT,
        homework_id INT,
        checked BOOLEAN DEFAULT FALSE,
        PRIMARY KEY (id)
        );
        """
        await self.pool.execute(sql)

    async def add_student(self, chat_id, username, full_name_tg, full_name):
        sql = """
        INSERT INTO Students (chat_id, username, full_name_tg, full_name) VALUES ($1, $2, $3, $4);
        """
        await self.pool.execute(sql, chat_id, username, full_name_tg, full_name)

    async def add_curator(self, chat_id, username, full_name_tg, full_name):
        sql = f"""
        INSERT INTO Curators (chat_id, username, full_name_tg, full_name) VALUES ($1, $2, $3, $4);
        """
        await self.pool.execute(sql, chat_id, username, full_name_tg, full_name)

    async def add_answer(self, chat_id, text, photo, video, document, homework_id):
        sql = """
        INSERT INTO Answers (student_chat_id, text, photo, video, document, homework_id) VALUES ($1, $2, $3, $4, $5, $6);
        """

        await self.pool.execute(sql, chat_id, text, photo, video, document, homework_id)

    async def add_lesson(self, title, text, homework_id):
        sql = f"""
        INSERT INTO Lessons (title, text, homework_id) VALUES ($1, $2, $3);
        """
        await self.pool.execute(sql, title, text, homework_id)

    async def add_homework(self, text):
        sql = f"""
        INSERT INTO Homeworks (text) VALUES ($1);
        """
        await self.pool.execute(sql, text)

    async def get_user(self, table_name, chat_id):
        sql = f"""
        SELECT * FROM {table_name} WHERE chat_id = $1;
        """
        return await self.pool.fetchrow(sql, chat_id)

    async def get_lesson(self, lesson_id):
        sql = """
        SELECT * FROM Lessons WHERE id = $1;
        """
        return await self.pool.fetchrow(sql, lesson_id)

    async def get_answer(self, chat_id):
        sql = f"""
        SELECT * FROM Answers WHERE student_chat_id = $1;
        """
        return await self.pool.fetchrow(chat_id)

    async def get_users(self, table_name):
        sql = f"""
        SELECT * FROM {table_name};
        """
        return await self.pool.fetch(sql)

    async def get_lessons(self):
        sql = """
        SELECT * FROM Lessons;
        """
        return await self.pool.fetch(sql)

    async def get_homeworks(self):
        sql = """
        SELECT * FROM Homeworks;
        """
        return await self.pool.fetch(sql)

    async def get_answers(self, homework_id):
        sql = """
        SELECT * FROM Answers
        WHERE homework_id = $1 AND checked = FALSE;
        """
        return await self.pool.fetch(sql, homework_id)

    async def get_current_lesson(self, chat_id):
        sql = """
        SELECT Lessons.id, Lessons.title, Lessons.text, Lessons.homework_id FROM Lessons
        JOIN Students ON Lessons.id = Students.current_lesson_id
        WHERE Students.chat_id = $1;
        """
        return await self.pool.fetchrow(sql, chat_id)

    async def get_current_homework(self, chat_id):
        sql = """
        SELECT Homeworks.id, Homeworks.text FROM Homeworks 
        JOIN Lessons ON Homeworks.id = Lessons.homework_id
        WHERE Lessons.id = (SELECT current_lesson_id FROM Students WHERE chat_id = $1);
        """
        return await self.pool.fetchrow(sql, chat_id)

    async def update_current_lesson_id(self, chat_id):
        sql = """
        UPDATE Students 
        SET current_lesson_id = current_lesson_id + 1
        WHERE chat_id = $1;
        """
        return await self.pool.execute(sql, chat_id)

    async def update_student(self, chat_id, leave):
        sql = """
        UPDATE Students 
        SET leave = $2
        WHERE chat_id = $1;
        """
        return await self.pool.execute(sql, chat_id, leave)

    async def update_homework(self, text, homework_id):
        sql = """
        UPDATE Homeworks
        SET text = $1
        WHERE id = $2
        """
        return await self.pool.execute(sql, text, homework_id)

    async def update_lesson(self, lesson_id, title, text, homework_id):
        sql = """
        UPDATE Lessons 
        SET title = $1,
        text = $2, 
        homework_id = $3
        WHERE id = $4;
        """
        return await self.pool.execute(sql, title, text, homework_id, lesson_id)

    async def pass_homework(self, chat_id):
        sql = """
        UPDATE Students 
        SET passed_lessons = passed_lessons + 1
        WHERE chat_id = $1;
        """
        await self.pool.execute(sql, chat_id)

    async def check_answer(self, chat_id, homework_id):
        sql = """
        UPDATE Answers 
        SET checked = TRUE
        WHERE student_chat_id = $1 AND homework_id = $2;
        """
        await self.pool.execute(sql, chat_id, homework_id)
