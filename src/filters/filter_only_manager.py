"""
    ╔════════════════════════════════════════════════════════════╗
    ║                    Модуль filter_only_manager.py            ║
    ╚════════════════════════════════════════════════════════════╝

    Описание:
        Модуль содержит фильтр для проверки прав менеджера в Telegram боте.
        Используется для ограничения доступа к функциям управления
        только для пользователей с ролью менеджера (user_type = 1).
"""

from aiogram import types

async def filter_only_manager(message: types.Message) -> bool:
    """
        Фильтр: разрешает доступ только пользователям с ролью менеджера
    """

    user = message.bot.um.get_user_by_telegram(message.from_user.id)

    if not (user and user.user_type == 1):
        await message.answer("Данная функция доступна только менеджерам!")

    return bool(user and user.user_type == 1)