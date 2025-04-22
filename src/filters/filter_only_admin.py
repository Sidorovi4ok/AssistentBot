"""
    ╔════════════════════════════════════════════════════════════╗
    ║                    Модуль filter_only_admin.py              ║
    ╚════════════════════════════════════════════════════════════╝

    Описание:
        Модуль содержит фильтр для проверки прав администратора в Telegram боте.
        Используется для ограничения доступа к административным функциям
        только для пользователей из списка разрешенных администраторов.
"""

from aiogram import types
from config import config

async def filter_only_admin(message: types.Message) -> bool:
    """
        Фильтр: разрешает доступ только администраторам 
    """

    if not(message.from_user.id in config.users.admins):
        await message.answer("Данная команда доступна только администратору")

    return message.from_user.id in config.users.admins
