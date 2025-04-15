from aiogram import types
from config import ALLOWED_ADMINS

async def filter_only_admin(message: types.Message) -> bool:

    if not(message.from_user.id in ALLOWED_ADMINS):
        await message.answer("Данная команда доступна только администратору")

    return message.from_user.id in ALLOWED_ADMINS
