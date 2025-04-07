
from aiogram import types
from aiogram.utils.markdown import hbold


async def cmd_change_type(message: types.Message):
    parts = message.text.split()
    if len(parts) != 3:
        await message.answer("❌ Использование: /change_type <ИНН> <тип (2-4)>")
        return

    inn = parts[1]
    try:
        new_type = int(parts[2])
        if new_type not in (2, 3, 4):
            raise ValueError
    except ValueError:
        await message.answer("❌ Тип должен быть числом 2, 3 или 4.")
        return

    success = message.bot.user_manager.change_user_type(inn, new_type)
    if success:
        await message.answer(f"✅ Тип пользователя с ИНН {hbold(inn)} успешно изменён на {new_type}.")
    else:
        await message.answer("❌ Пользователь с таким ИНН не найден.")
