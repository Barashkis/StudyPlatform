from loader import dp, db

from aiogram import types


@dp.my_chat_member_handler()
async def user_leave_or_join(update: types.ChatMemberUpdated):
    if update.new_chat_member.is_chat_member():
        leave = False
    else:
        leave = True

    await db.update_student(update.chat.id, leave)
