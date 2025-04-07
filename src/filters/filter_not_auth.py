
from aiogram import types


async def filter_not_authorized(message: types.Message) -> bool:
    """
    Фильтр для проверки, что пользователь не авторизован.

    Возвращает:
    - True: если пользователь не найден в базе или не прошёл авторизацию.
    - False: если пользователь авторизован.
    """

    user = message.bot.user_manager.get_user_by_telegram(message.from_user.id)

    if user and user.is_authenticated:
        await message.answer("Вы уже авторизованы!")

    return not (user and user.is_authenticated)