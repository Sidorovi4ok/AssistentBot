"""
    ╔════════════════════════════════════════════════════════════╗
    ║                    Модуль filter_only_auth.py               ║
    ╚════════════════════════════════════════════════════════════╝

    Описание:
        Модуль содержит фильтр для проверки статуса авторизации пользователя
        в Telegram боте. Используется для контроля доступа к функционалу,
        требующему авторизации.
"""

from aiogram import types

async def filter_only_auth(message: types.Message) -> bool:
    """
        Фильтр: разрешает доступ только авторизованным пользователям 
    """

    user = message.bot.um.get_user_by_telegram(message.from_user.id)

    if not(user and user.is_authenticated):
        await message.answer("Для работы с ботом необходимо авторизоваться!")

    return (user and user.is_authenticated)