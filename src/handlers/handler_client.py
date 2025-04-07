
from aiogram import types
from aiogram.utils.markdown import hbold, hcode


async def cmd_get_user(message: types.Message):
    parts = message.text.strip().split()
    if len(parts) != 2:
        await message.answer("❌ Использование: /get_user <ИНН>")
        return

    inn = parts[1]
    user = message.bot.user_manager.get_user_by_inn(inn)

    if not user:
        await message.answer("❌ Пользователь с таким ИНН не найден.")
        return

    info = (
        f"{hbold('ИНН:')} {hcode(user.inn)}\n"
        f"{hbold('Telegram ID:')} {user.telegram_id or '—'}\n"
        f"{hbold('Тип пользователя:')} {user.user_type} ({message.bot.user_manager.get_user_type_name(user.user_type)})\n"
        f"{hbold('Авторизован:')} {'✅' if user.is_authenticated else '❌'}"
    )
    await message.answer(info)
