"""
    ╔════════════════════════════════════════════════════════════╗
    ║                Модуль handlers/handler_manager.py          ║
    ╚════════════════════════════════════════════════════════════╝

    Описание:
        Модуль содержит обработчики для панели управления менеджера, предоставляя
        функционал управления пользователями и товарами через интерактивное меню.
        Включает возможности просмотра, редактирования и обновления данных.

    Функциональность:
        Управление пользователями:
            - Просмотр списка всех пользователей
            - Получение информации о конкретном пользователе
            - Изменение типа пользователя
            - Управление скидками для разных категорий
            - Редактирование данных пользователей

        Управление товарами:
            - Просмотр информации о товарах
            - Обновление прайс-листа через Excel
            - Скачивание текущего прайс-листа
            - Редактирование данных товаров
"""

from aiogram                    import types
from src.utils                  import logger
from aiogram.types              import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.exceptions         import TelegramBadRequest
from aiogram.fsm.context        import FSMContext
from aiogram.utils.markdown     import hbold, hcode
from src.managers.manager_user  import User

from src.states import ManagerPanelStates


async def cmd_manager_handler(message: types.Message):
    logger.info(f"Received MANAGER command FROM {message.from_user.id}")
    try:
        manager_main_menu_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👥 Управление пользователями", callback_data="manager_menu_users")],
            [InlineKeyboardButton(text="📦 Управление товарами",       callback_data="manager_menu_products")],
            [InlineKeyboardButton(text="❌ Закрыть меню",              callback_data="manager_close_menu")],
        ])
        await message.answer(
            f"🛠 Менеджер-панель\nДобро пожаловать, {message.from_user.first_name}!",
            reply_markup=manager_main_menu_kb
        )
        await message.delete()
    except Exception as e:
        logger.exception(f"ERROR in cmd_manager_handler FOR user_id={message.from_user.id}")
        await message.answer(f"Ошибка: {e}", show_alert=True)





"""
    manager_users_menu_callback_handler

    Этот обработчик обрабатывает callback menu_logs для вывода меню для работы с логами системы
"""
async def manager_users_menu_callback_handler(callback: types.CallbackQuery):
    if callback.data == "manager_menu_users":
        logger.info(f"Get manager users menu command from {callback.from_user.id}")
    try:
        manager_users_menu_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👥 Получить список пользователей",                   callback_data="manager_get_users")],
            [InlineKeyboardButton(text="📋 Получить данные определенного пользователя",      callback_data="manager_get_user")],
            [InlineKeyboardButton(text="🖋️ Изменить данные определенного пользователя",      callback_data="manager_change_user")],
            [InlineKeyboardButton(text="🏷️ Изменить значение скидки для категории клиента",  callback_data="manager_change_discount")],
            [InlineKeyboardButton(text="⬅️ Назад",                                           callback_data="manager_back")],
        ])
        await callback.message.edit_text("🛠 Меню работы с пользователями в системе:")
        await callback.message.edit_reply_markup(reply_markup=manager_users_menu_kb)
        await callback.answer()
    except Exception as e:
        logger.exception(f"ERROR in get_log_menu_callback_handler FOR user_id={callback.from_user.id}")
        await callback.answer(f"Ошибка: {e}", show_alert=True)




"""
    manager_get_users_callback_handler

    Этот обработчик обрабатывает callback menu_logs для вывода меню для работы с логами системы
"""
async def manager_get_users_callback_handler(callback: types.CallbackQuery):
    if callback.data == "manager_get_users":
        logger.info(f"Get from manager list users command from by {callback.from_user.id}")
        try:
            session = callback.bot.um.Session()
            users = session.query(User).all()

            user_lines = []
            for u in users:
                user_lines.append(
                    f"{hbold('ИНН')}: {hcode(u.inn)}\n"
                    f"{hbold('Тип')}: {callback.bot.um.get_user_type_name(u.user_type)}\n"
                    f"{hbold('Telegram ID')}: {u.telegram_id or '❌'}\n"
                    f"{hbold('Авторизован')}: {'✅' if u.is_authenticated else '❌'}\n"
                    f"-------------------------"
                )
            await callback.message.edit_text(
                text="👥 Список пользователей:\n\n" + "\n".join(user_lines),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="manager_menu_users")]
                ])
            )
            await callback.answer()
        except Exception as e:
            logger.exception(f"ERROR in manager_get_users_callback_handler FOR user_id={callback.from_user.id}")
            await callback.answer(f"Ошибка: {str(e)}", show_alert=True)




"""
    manager_get_user_callback_handler

    Этот обработчик обрабатывает callback menu_logs для вывода меню для работы с логами системы
"""
async def manager_get_user_callback_handler(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == "manager_get_user":
        logger.info(f"Manager get info user by {callback.from_user.id}")
        try:
            await callback.message.answer("👤 Пожалуйста, отправьте ИНН пользователя")
            await state.set_state(ManagerPanelStates.waiting_for_inn)
        except Exception as e:
            logger.exception(f"ERROR in manager_get_user FOR user_id={callback.from_user.id}")
            await callback.answer(f"Ошибка: {str(e)}", show_alert=True)

async def handle_inn_user(message: types.Message, state: FSMContext):
    try:
        user = message.bot.um.get_user_by_inn(message.text)
        if not user:
            await message.answer("❌ Пользователь с таким ИНН не найден.")
            return
        info = (
            f"{hbold('ИНН:')} {hcode(user.inn)}\n"
            f"{hbold('Telegram ID:')} {user.telegram_id or '—'}\n"
            f"{hbold('Тип пользователя:')} {user.user_type} ({message.bot.um.get_user_type_name(user.user_type)})\n"
            f"{hbold('Авторизован:')} {'✅' if user.is_authenticated else '❌'}"
        )
        await message.answer(info)
        await state.clear()
    except Exception as e:
        logger.exception(f"ERROR in handle_inn_user FOR user_id={message.from_user.id}")
        await message.answer(f"Ошибка: {str(e)}", show_alert=True)











"""
    manager_change_user_callback_handler
    Этот обработчик обрабатывает callback menu_logs для вывода меню для работы с логами системы
"""
async def manager_change_user_callback_handler(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == "manager_change_user":
        logger.info(f"Manager change user by {callback.from_user.id}")
        try:
            manager_users_menu_kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🛠️ Изменить ТИП клиента", callback_data="manager_change_type_user")],
                [InlineKeyboardButton(text="📝 Изменить ИНН клиента", callback_data="manager_change_inn_user")],
                [InlineKeyboardButton(text="❌ Удалить клиента из базы", callback_data="manager_delete_user")],
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="manager_menu_users")],
            ])
            await callback.message.edit_text("🛠 Меню изменения пользователя:")
            await callback.message.edit_reply_markup(reply_markup=manager_users_menu_kb)
            await callback.answer()
        except Exception as e:
            logger.exception(f"ERROR in manager_change_user_callback_handler FOR user_id={callback.from_user.id}")
            await callback.answer(f"Ошибка: {str(e)}", show_alert=True)



"""
    manager_change_type_user_callback_handler
    Этот обработчик обрабатывает callback menu_logs для вывода меню для работы с логами системы
"""
async def manager_change_type_user_callback_handler(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == "manager_change_type_user":
        logger.info(f"Manager change type user by {callback.from_user.id}")
        try:
            await callback.message.answer("👤 Пожалуйста, отправьте ИНН пользователя и номер новой категории клиента!")
            await state.set_state(ManagerPanelStates.waiting_for_type)
        except Exception as e:
            logger.exception(f"ERROR in manager_change_type_user_callback_handler FOR user_id={callback.from_user.id}")
            await callback.answer(f"Ошибка: {str(e)}", show_alert=True)


async def manager_change_type_handler(message: types.Message):
    parts = message.text.split()
    if len(parts) != 2:
        await message.answer("❌ Ожидается: <ИНН> <тип (2-4)>")
        return
    inn = parts[0]
    try:
        new_type = int(parts[1])

        if new_type not in (2, 3, 4):
            raise ValueError
    except ValueError:
        await message.answer("❌ Тип должен быть числом 2, 3 или 4.")
        return
    success = message.bot.um.change_user_type(inn, new_type)
    if success:
        await message.answer(f"✅ Тип пользователя с ИНН {hbold(inn)} успешно изменён на {new_type}.")
    else:
        await message.answer("❌ Пользователь с таким ИНН не найден.")









"""
    manager_change_discount_callback_handler
    Этот обработчик обрабатывает callback menu_logs для вывода меню для работы с логами системы
"""
async def manager_change_discount_callback_handler(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == "manager_change_discount":
        logger.info(f"Manager change type user by {callback.from_user.id}")
        try:
            # Создаем кнопки для выбора типа клиента
            manager_discount_kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="2️⃣ Клиент (Базовый)", callback_data="discount_2")],
                [InlineKeyboardButton(text="3️⃣ Клиент (Средний)", callback_data="discount_3")],
                [InlineKeyboardButton(text="4️⃣ Клиент (VIP)",     callback_data="discount_4")],
                [InlineKeyboardButton(text="⬅️ Назад",            callback_data="manager_menu_users")],
            ])
            await callback.message.edit_text("🛠 Выберите тип клиента для изменения скидки:")
            await callback.message.edit_reply_markup(reply_markup=manager_discount_kb)
            await state.set_state(ManagerPanelStates.waiting_for_type_discount)
            await callback.answer()
        except Exception as e:
            logger.exception(f"ERROR in manager_change_discount_callback_handler FOR user_id={callback.from_user.id}")
            await callback.answer(f"Ошибка: {str(e)}", show_alert=True)

async def manager_wait_user_type_callback_handler(callback: types.CallbackQuery, state: FSMContext):
    if callback.data.startswith("discount_"):
        logger.info(f"Manager change type user by {callback.from_user.id}")
        try:
            user_type = int(callback.data.split("_")[1])
            if user_type not in [2, 3, 4]:
                await callback.answer("❌ Некорректный тип пользователя!")
                return
            await state.update_data(
                user_type=user_type,
                discount_message_id=callback.message.message_id
            )
            await callback.message.edit_text("Введите новое значение скидки (например, 0.15 для 15%):")
            await state.set_state(ManagerPanelStates.waiting_for_new_discount)
        except Exception as e:
            logger.exception(f"ERROR in manager_change_discount_callback_handler FOR user_id={callback.from_user.id}")
            await callback.answer(f"Ошибка: {str(e)}", show_alert=True)

async def manager_wait_new_discount_callback_handler(message: types.Message, state: FSMContext):
    try:
        new_discount = float(message.text)
        if not (0 <= new_discount <= 1):
            raise ValueError("Скидка должна быть в пределах от 0 до 1.")
        user_data = await state.get_data()
        user_type = user_data.get('user_type')
        if user_type is None:
            await message.answer("Вы не выбрали тип пользователя!")
            return
        success = message.bot.um.set_discount(user_type, new_discount)
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
                f"Скидка для типа {message.bot.um.get_user_type_name(user_type)} успешно обновлена на {new_discount * 100}%")
            await state.clear()
        else:
            await message.answer("Произошла ошибка при обновлении скидки.")

    except ValueError as e:
        await message.answer(f"Ошибка: некоректное значение. Пожалуйста, введите корректное значение скидки.")
    except Exception as e:
        await message.answer(f"Ошибка: {str(e)}")






"""
    manager_products_menu_callback_handler

    Этот обработчик обрабатывает callback menu_logs для вывода меню для работы с логами системы
"""
async def manager_products_menu_callback_handler(callback: types.CallbackQuery):
    if callback.data == "manager_menu_products":
        logger.info(f"Get manager products menu command from {callback.from_user.id}")
    try:
        manager_products_menu_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Получить данные определенного товара",       callback_data="manager_get_product")],
            [InlineKeyboardButton(text="🖋️ Изменить данные определенного товара",       callback_data="manager_change_product")],
            [InlineKeyboardButton(text="📊 Обновить excel-price с товарами",            callback_data="manager_update_excel")],
            [InlineKeyboardButton(text="🔗 Получить текущий excel-price системы",       callback_data="manager_download_excel")],
            [InlineKeyboardButton(text="⬅️ Назад",                                      callback_data="manager_back")],
        ])
        await callback.message.edit_text("🛠 Меню работы с товарами в системе:")
        await callback.message.edit_reply_markup(reply_markup=manager_products_menu_kb)
        await callback.answer()
    except Exception as e:
        logger.exception(f"ERROR in get_log_menu_callback_handler FOR user_id={callback.from_user.id}")
        await callback.answer(f"Ошибка: {e}", show_alert=True)



"""
    manager_update_excel_callback_handler

    Этот обработчик обрабатывает callback download_logs для отправки всего файла с логами
"""
async def manager_update_excel_callback_handler(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == "manager_update_excel":
        logger.info(f"Update excel-price by {callback.from_user.id}")
        
        try:
            await callback.message.answer("📎 Пожалуйста, отправьте новый Excel-файл (.xlsx) для обновления прайса.")
            await state.set_state(ManagerPanelStates.waiting_for_file)
        except Exception as e:
            logger.exception(f"ERROR in manager_update_excel_callback_handler FOR user_id={callback.from_user.id}")
            await callback.answer(f"Ошибка: {str(e)}", show_alert=True)

async def handle_excel_file(message: types.Message, state: FSMContext):
    logger.info(f"Get excel-price by {message.from_user.id}")
    try:
        document = message.document
        if not document.file_name.endswith(".xlsx"):
            await message.reply("⚠️ Пожалуйста, отправьте файл в формате .xlsx")
            return
        file = await message.bot.get_file(document.file_id)
        file_path = file.file_path
        file_bytes = await message.bot.download_file(file_path)
        with open("data/excel/price-list.xlsx", "wb") as f:
            f.write(file_bytes.read())
        await message.reply("✅ Файл успешно сохранён как price-list.xlsx.")
        await state.clear()
    except Exception as e:
        logger.exception(f"ERROR in handle_excel_file FOR user_id={message.from_user.id}")
        await message.answer(f"Ошибка: {str(e)}", show_alert=True)






"""
    manager_download_excel_callback_handler

    Этот обработчик обрабатывает callback download_logs для отправки всего файла с логами
"""
async def manager_download_excel_callback_handler(callback: types.CallbackQuery):
    if callback.data == "manager_download_excel":
        logger.info(f"Download excel-price by {callback.from_user.id}")
        try:
            await callback.message.answer_document(
                document=FSInputFile("data/excel/price-list.xlsx"),
                caption="📊 Вот текущий прайс лист системы:"
            )
            await callback.answer()
        except Exception as e:
            logger.exception(f"ERROR in manager_download_excel_callback_handler FOR user_id={callback.from_user.id}")
            await callback.answer(f"Ошибка: {str(e)}", show_alert=True)




"""
    manager_back_menu_callback_handler

    Этот обработчик обрабатывает callback admin_back для возвращения в главное меню администратора
"""
async def manager_back_menu_callback_handler(callback: types.CallbackQuery):
    if callback.data == "manager_back":
        logger.info(f"Back manager menu by {callback.from_user.id}")
        try:
            manager_main_menu_kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="👥 Управление пользователями",   callback_data="manager_menu_users")],
                [InlineKeyboardButton(text="📦 Управление товарами",         callback_data="manager_menu_products")],
                [InlineKeyboardButton(text="❌ Закрыть меню",                callback_data="manager_close_menu")],
            ])
            await callback.message.edit_text(f"🛠 Менеджер-панель\nДобро пожаловать, {callback.from_user.first_name}!")
            await callback.message.edit_reply_markup(reply_markup=manager_main_menu_kb)
            await callback.answer()
        except Exception as e:
            logger.exception(f"ERROR in admin_back_menu_callback_handler FOR user_id={callback.from_user.id}")
            await callback.answer(f"Ошибка: {str(e)}", show_alert=True)



"""
    manager_close_menu_callback_handler

    Этот обработчик обрабатывает callback admin_close для закрытия меню администратора
"""
async def manager_close_menu_callback_handler(callback: types.CallbackQuery):
    if callback.data == "manager_close_menu":
        logger.info(f"Close manager menu by {callback.from_user.id}")
        try:
            await callback.message.delete()
            await callback.answer()
        except Exception as e:
            logger.exception(f"ERROR in manager_close_menu_callback_handler FOR user_id={callback.from_user.id}")
            await callback.answer(f"Ошибка: {str(e)}", show_alert=True)