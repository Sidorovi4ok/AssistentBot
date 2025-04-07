from aiogram import types
from src.filters import filter_only_manager


async def role_handler(message: types.Message):
    """
        Обработчик команды /role.

        Использует manager_only_handler для проверки прав доступа.

        Если пользователь менеджер, возвращает "менеджер", иначе – "клиент".
    """

    if await filter_only_manager(message):
        await message.answer("Ваша роль: Менеджер")
    else:
        await message.answer("Ваша роль: Клиент")