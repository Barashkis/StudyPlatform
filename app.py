from aiogram import executor

from handlers import dp
from loader import db

from utils import set_default_commands


async def on_shutdown(_):
    await db.pool.close()


async def on_startup(_):
    await set_default_commands(dp)
    await db.create_all_tables()


if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup, on_shutdown=on_shutdown)
