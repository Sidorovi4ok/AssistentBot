from aiogram import types
from src.utils import filter_only_manager


async def role_handler(message: types.Message):
    """
        Обработчик команды /role.

        Использует manager_only_handler для проверки прав доступа.

        Если пользователь менеджер, возвращает "менеджер", иначе – "клиент".
    """

    if await filter_only_manager(message):
        await message.answer("Ваша роль: Менеджер")
    else:
        # Если пользователь не менеджер, можно отправить дополнительное сообщение
        # или оставить только сообщение из manager_only_handler.
        await message.answer("Ваша роль: Клиент")