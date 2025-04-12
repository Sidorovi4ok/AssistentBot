from aiogram import types
from src.filters import filter_only_manager


async def role_handler(message: types.Message):
    """
        Обработчик команды /role.

        Использует manager_only_handler для проверки прав доступа.

        Если пользователь менеджер, возвращает "менеджер", иначе – "клиент".
    """
    user = message.bot.user_manager.get_user_by_telegram(message.from_user.id)

    if user.user_type == 1:
        await message.answer("Ваша роль: Менеджер")
    else:
        await message.answer(f"Ваша роль: {message.bot.user_manager.get_user_type_name(user.user_type)}\n"
                             f"Ваша скидка: {message.bot.user_manager.get_discount(user.user_type) * 100}%")