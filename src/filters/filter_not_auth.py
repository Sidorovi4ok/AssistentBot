"""
    ╔════════════════════════════════════════════════════════════╗
    ║                    Модуль filter_not_auth.py                ║
    ╚════════════════════════════════════════════════════════════╝

    Описание:
        Модуль содержит фильтр для проверки статуса авторизации пользователя
        в Telegram боте. Используется для контроля доступа к функционалу,
        требующему авторизацию.
"""

from aiogram import types

async def filter_not_authorized(message: types.Message) -> bool:
    """
        Фильтр: разрешает доступ только не авторизованным пользователям 
    """
    
    user = message.bot.um.get_user_by_telegram(message.from_user.id)

    if user and user.is_authenticated:
        await message.answer("Вы уже авторизованы!")

    return not (user and user.is_authenticated)