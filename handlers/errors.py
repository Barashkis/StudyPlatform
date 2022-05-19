from aiogram.types import Update
from aiogram.utils.exceptions import MessageNotModified

from loader import dp


@dp.errors_handler()
async def catch_errors(update: Update, exception):
    if isinstance(exception, ValueError):
        await update.get_current().message.answer("В результате обработки запроса возникла ошибка... "
                                                  "Попробуйте еще раз")
        return
    elif isinstance(exception, MessageNotModified):
        return
