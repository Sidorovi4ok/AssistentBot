from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from src.states import DiscountStates
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext


async def cmd_change_discount(message: types.Message, state: FSMContext):
    """
    Обрабатывает команду /change_discount.
    Показывает инлайн кнопки для выбора типа клиента.
    """
    # Создаем кнопки для выбора типа клиента
    buttons = [
        InlineKeyboardButton(text="Клиент (Базовый)", callback_data="discount_2"),
        InlineKeyboardButton(text="Клиент (Средний)", callback_data="discount_3"),
        InlineKeyboardButton(text="Клиент (VIP)", callback_data="discount_4"),
        InlineKeyboardButton(text="Отмена", callback_data="cancel_change")  # изменили callback_data
    ]

    # Создаем клавиатуру с кнопками
    keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons], row_width=2)

    # Отправляем сообщение с клавиатурой
    await message.answer("Выберите тип клиента для изменения скидки:", reply_markup=keyboard)

    # Устанавливаем состояние ожидания выбора типа клиента
    await state.set_state(DiscountStates.waiting_for_user_type)


async def process_discount_type(callback_query: types.CallbackQuery, state: FSMContext):
    """
    Обрабатывает выбор типа клиента и переходит к запросу нового значения скидки.
    """
    user_type = int(callback_query.data.split("_")[1])
    await state.update_data(discount_message_id=callback_query.message.message_id)

    if user_type not in [2, 3, 4]:
        await callback_query.answer("Некорректный тип пользователя!")
        return

    # Сохраняем тип пользователя для дальнейшего использования
    await state.update_data(user_type=user_type)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="Отмена", callback_data="cancel_change")  # изменили callback_data
    ]], row_width=1)

    await callback_query.message.edit_text("Введите новое значение скидки (например, 0.15 для 15%) или нажмите отмену:", reply_markup=keyboard)

    # Устанавливаем состояние для ввода скидки
    await state.set_state(DiscountStates.waiting_for_new_discount)


async def process_new_discount(message: types.Message, state: FSMContext):
    """
    Обрабатывает ввод нового значения скидки.
    """
    try:
        new_discount = float(message.text)
        if not (0 <= new_discount <= 1):
            raise ValueError("Скидка должна быть в пределах от 0 до 1.")

        user_data = await state.get_data()
        user_type = user_data.get('user_type')  # Получаем тип клиента, сохраненный на предыдущем шаге

        if user_type is None:
            await message.answer("Вы не выбрали тип пользователя!")
            return

        # Обновляем скидку
        user_manager = message.bot.user_manager
        success = user_manager.set_discount(user_type, new_discount)

        if success:
            user_data = await state.get_data()
            message_id = user_data.get("discount_message_id")
            if message_id:
                try:
                    await message.bot.delete_message(
                        chat_id=message.chat.id,
                        message_id=message_id
                    )
                except TelegramBadRequest:
                    pass

            await message.answer(
                f"Скидка для типа {user_manager.get_user_type_name(user_type)} успешно обновлена на {new_discount * 100}%")
            # Завершаем процесс
            await state.clear()
        else:
            await message.answer("Произошла ошибка при обновлении скидки.")

    except ValueError as e:
        await message.answer(f"Ошибка: некоректное значение. Пожалуйста, введите корректное значение скидки.")
    except Exception as e:
        await message.answer(f"Ошибка: {str(e)}")




async def cancel_change_callback_handler(callback_query: types.CallbackQuery, state: FSMContext):
    """
    Обработчик отмены через inline-кнопку.
    Очищает состояние и отменяет запрос.
    """
    if callback_query.data == "cancel_change":

        user_data = await state.get_data()
        request_message_id = user_data.get("request_message_id")

        try:
            if request_message_id:
                await callback_query.bot.edit_message_reply_markup(
                    chat_id=callback_query.message.chat.id,
                    message_id=request_message_id,
                    reply_markup=None
                )
        except TelegramBadRequest:
            pass

        await state.clear()
        await callback_query.message.edit_text("🚫 Процесс смены скидки отменен. Возврат в главное меню")
        await callback_query.answer()
