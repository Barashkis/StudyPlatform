from loader import dp

from aiogram import types


@dp.message_handler(content_types=types.ContentTypes.ANY)
async def answer_to_other_messages(message: types.Message):
    await message.answer("К сожалению, у меня нет ответа на это сообщение. "
                         "Для взаимодействия со мной необходимо использовать клавиатуру")
