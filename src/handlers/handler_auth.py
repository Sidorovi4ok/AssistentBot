from aiogram import types
from aiogram.fsm.context import FSMContext
from src.states import AuthStates
from src.utils import logger

# Для регистрации: запрашиваем ИНН и пароль
async def cmd_register(message: types.Message, state: FSMContext):
    await message.answer("📝 Введите ваш ИНН для регистрации (12 цифр):")
    await state.set_state(AuthStates.waiting_for_inn_register)
    # Сохраним информацию о том, что это регистрация
    await message.answer("Также введите пароль через пробел после ИНН. Пример: 123456789012 mypass")

async def process_register_inn(message: types.Message, state: FSMContext):
    # Ожидаем сообщение в формате: <ИНН> <пароль>
    parts = message.text.strip().split(maxsplit=1)
    if len(parts) != 2:
        await message.answer("❌ Неверный формат. Введите ИНН и пароль через пробел.")
        return
    inn, password = parts
    if not inn.isdigit() or len(inn) != 12:
        await message.answer("❌ Некорректный ИНН. Он должен состоять из 12 цифр.")
        return

    success = message.bot.user_manager.register_user(inn, password, message.from_user.id)

    if success:
        await message.answer("🎉 Регистрация прошла успешна!")
        logger.info(f"Зарегистрирован новый пользователь с ИНН {inn}")
    else:
        await message.answer("❌ Регистрация не удалась. Возможно, этот ИНН уже зарегистрирован.")
    await state.clear()

# Для авторизации: запрашиваем ИНН и пароль
async def cmd_login(message: types.Message, state: FSMContext):
    await message.answer("🔑 Введите ваш ИНН и пароль через пробел (пример: 123456789012 mypass):")
    await state.set_state(AuthStates.waiting_for_inn_login)

async def process_login_inn(message: types.Message, state: FSMContext):
    parts = message.text.strip().split(maxsplit=1)
    if len(parts) != 2:
        await message.answer("❌ Неверный формат. Введите ИНН и пароль через пробел.")
        return
    inn, password = parts
    if not inn.isdigit() or len(inn) != 12:
        await message.answer("❌ Некорректный ИНН. Он должен состоять из 12 цифр.")
        return
    success = message.bot.user_manager.login_user(inn, password, message.from_user.id)
    if success:
        user = message.bot.user_manager.get_user_by_telegram(message.from_user.id)
        discount = message.bot.user_manager.get_discount(user.user_type) * 100
        await message.answer(
            f"✅ Авторизация успешна!\nВаш тип: {user.user_type}\nВаша скидка: {discount}%"
        )
        logger.info(f"Пользователь {message.from_user.id} авторизовался по ИНН {inn}")
    else:
        await message.answer("❌ Неверный ИНН или пароль. Попробуйте снова или зарегистрируйтесь через /register.")
    await state.clear()
