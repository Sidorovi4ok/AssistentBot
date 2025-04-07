from aiogram import types

async def filter_only_manager(message: types.Message) -> bool:
    """
    Фильтр: разрешает доступ только пользователям с ролью менеджера (user_type = 1).

    Возвращает:
    - True, если пользователь менеджер.
    - False, если не авторизован или не менеджер.
    """

    user = message.bot.user_manager.get_user_by_telegram(message.from_user.id)

    if not (user and user.user_type == 1):
        await message.answer("Данная функция доступна только менеджерам!")

    return bool(user and user.user_type == 1)