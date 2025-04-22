"""
    ╔════════════════════════════════════════════════════════════╗
    ║                Модуль handlers/handler_role.py             ║
    ╚════════════════════════════════════════════════════════════╝

    Описание:
        Модуль содержит обработчик команды /role, который определяет и отображает
        роль пользователя в системе. Предоставляет информацию о типе пользователя
        и связанных с ним привилегиях (например, скидках).
"""

from aiogram import types

async def role_handler(message: types.Message):
    """
        Обработчик команды /role.
    """
    user = message.bot.um.get_user_by_telegram(message.from_user.id)

    if user.user_type == 1:
        await message.answer("Ваша роль: Менеджер")
    else:
        await message.answer(f"Ваша роль: {message.bot.um.get_user_type_name(user.user_type)}\n"
                             f"Ваша скидка: {message.bot.um.get_discount(user.user_type) * 100}%")