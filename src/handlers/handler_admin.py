
"""
    handler_admin.py

    Этот обработчик обрабатывает команды связанные с администрированием системы
"""



from aiogram       import types
from src.utils     import logger
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.utils.markdown import hbold, hcode
from src.managers.manager_user import User



"""
    cmd_admin_handler

    Этот обработчик обрабатывает команду /admin для вывода меню администратора системы
"""
async def cmd_admin_handler(message: types.Message):
    logger.info(f"Received ADMIN command FROM {message.from_user.id}")
    try:
        admin_main_menu_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📄 Управление логами",         callback_data="menu_logs")],
            [InlineKeyboardButton(text="👥 Управление базой данных",   callback_data="menu_db")],
            [InlineKeyboardButton(text="🤖 Перезагрузка бота",         callback_data="restart_bot")],
            [InlineKeyboardButton(text="❌ Закрыть меню",              callback_data="admin_close")],
        ])
        await message.answer(
            f"🛠 Админ-панель\nДобро пожаловать, {message.from_user.first_name}!",
            reply_markup=admin_main_menu_kb
        )
        await message.delete()
    except Exception as e:
        logger.exception(f"ERROR in cmd_admin_handler FOR user_id={message.from_user.id}")
        await message.answer(f"Ошибка: {e}", show_alert=True)



"""
    admin_logs_menu_callback_handler
    
    Этот обработчик обрабатывает callback menu_logs для вывода меню для работы с логами системы
"""
async def admin_logs_menu_callback_handler(callback: types.CallbackQuery):
    if callback.data == "menu_logs":
        logger.info(f"View admin logs menu command from {callback.from_user.id}")
    try:
        admin_logs_menu_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📄 Вывести последние логи",     callback_data="get_logs")],
            [InlineKeyboardButton(text="📂 Скачать весь файл с логами", callback_data="download_logs")],
            [InlineKeyboardButton(text="⬅️ Назад",                      callback_data="admin_back")],
        ])
        await callback.message.edit_text("🛠 Меню работы с логами всей системы:")
        await callback.message.edit_reply_markup(reply_markup=admin_logs_menu_kb)
        await callback.answer()
    except Exception as e:
        logger.exception(f"ERROR in get_log_menu_callback_handler FOR user_id={callback.from_user.id}")
        await callback.answer(f"Ошибка: {e}", show_alert=True)



"""
    admin_view_logs_callback_handler

    Этот обработчик обрабатывает callback get_logs для вывода в сообщении последних логов из файла logs/main.log
"""
async def admin_view_logs_callback_handler(callback: types.CallbackQuery):
    if callback.data == "get_logs":
        logger.info(f"Get logs by {callback.from_user.id}")
        try:
            with open("logs/main.log", "r") as f:
                await (callback.message.edit_text(
               f"<b>Последние логи в системе:</b>\n<code>{''.join(f.readlines()[-25:])}</code>",
                    parse_mode="HTML"
                ))
                admin_logs_menu_kb = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="menu_logs")],
                ])
                await callback.message.edit_reply_markup(reply_markup=admin_logs_menu_kb)
                await callback.answer()
        except Exception as e:
            logger.exception(f"ERROR in view_log_callback_handler FOR user_id={callback.from_user.id}")
            await callback.answer(f"Ошибка: {e}", show_alert=True)



"""
    admin_download_logs_callback_handler

    Этот обработчик обрабатывает callback download_logs для отправки всего файла с логами
"""
async def admin_download_logs_callback_handler(callback: types.CallbackQuery):
    if callback.data == "download_logs":
        logger.info(f"Download logs by {callback.from_user.id}")
        try:
            log_file = FSInputFile("logs/main.log")
            await callback.message.answer_document(
                document=log_file,
                caption="📝 Вот ваш файл с логами всей системы на данный момент"
            )
            await callback.answer()
        except Exception as e:
            logger.exception(f"ERROR in admin_download_logs_callback_handler FOR user_id={callback.from_user.id}")
            await callback.answer(f"Ошибка: {str(e)}", show_alert=True)



"""
    admin_db_menu_callback_handler

    Этот обработчик обрабатывает callback menu_db для вывода меню для работы с базой данных
"""
async def admin_db_menu_callback_handler(callback: types.CallbackQuery):
    if callback.data == "menu_db":
        logger.info(f"View admin database menu command from by {callback.from_user.id}")
        try:
            admin_users_menu_kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📋 Список пользователей",  callback_data="admin_get_users")],
                [InlineKeyboardButton(text="🖋️ Изменить пользователя", callback_data="admin_edit_user")],
                [InlineKeyboardButton(text="🗑️ Удалить пользователя",  callback_data="admin_delete_user")],
                [InlineKeyboardButton(text="⬅️ Назад",                 callback_data="admin_back")],
            ])
            await callback.message.edit_text("🛠 Меню работы с базой данных всей системы:")
            await callback.message.edit_reply_markup(reply_markup=admin_users_menu_kb)
            await callback.answer()
        except Exception as e:
            logger.exception(f"ERROR in admin_db_menu_callback_handler FOR user_id={callback.from_user.id}")
            await callback.answer(f"Ошибка: {str(e)}", show_alert=True)



"""
    admin_get_users_callback_handler

    Этот обработчик обрабатывает callback admin_get_users для вывода списка в сообщении всех пользователей в базе данных
"""
async def admin_get_users_callback_handler(callback: types.CallbackQuery):
    if callback.data == "admin_get_users":
        logger.info(f"Get admin list users command from by {callback.from_user.id}")
        try:
            session = callback.bot.user_manager.Session()
            users = session.query(User).all()

            user_lines = []
            for u in users:
                user_lines.append(
                    f"{hbold('ИНН')}: {hcode(u.inn)}\n"
                    f"{hbold('Тип')}: {callback.bot.user_manager.get_user_type_name(u.user_type)}\n"
                    f"{hbold('Telegram ID')}: {u.telegram_id or '❌'}\n"
                    f"{hbold('Авторизован')}: {'✅' if u.is_authenticated else '❌'}\n"
                    f"-------------------------"
                )
            await callback.message.edit_text(
                text="👥 Список пользователей:\n\n" + "\n".join(user_lines),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="menu_db")]
                ])
            )
            await callback.answer()
        except Exception as e:
            logger.exception(f"ERROR in admin_get_users_callback_handler FOR user_id={callback.from_user.id}")
            await callback.answer(f"Ошибка: {str(e)}", show_alert=True)



"""
    admin_back_menu_callback_handler

    Этот обработчик обрабатывает callback admin_back для возвращения в главное меню администратора
"""
async def admin_back_menu_callback_handler(callback: types.CallbackQuery):
    if callback.data == "admin_back":
        logger.info(f"Back admin menu by {callback.from_user.id}")
        try:
            admin_main_menu_kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📄 Управление логами",       callback_data="menu_logs")],
                [InlineKeyboardButton(text="👥 Управление базой данных", callback_data="menu_db")],
                [InlineKeyboardButton(text="🤖 Перезагрузка бота",       callback_data="restart_bot")],
                [InlineKeyboardButton(text="❌ Закрыть меню",            callback_data="admin_close")],
            ])
            await callback.message.edit_text(f"🛠 Админ-панель\nДобро пожаловать, {callback.from_user.first_name}!")
            await callback.message.edit_reply_markup(reply_markup=admin_main_menu_kb)
            await callback.answer()
        except Exception as e:
            logger.exception(f"ERROR in admin_back_menu_callback_handler FOR user_id={callback.from_user.id}")
            await callback.answer(f"Ошибка: {str(e)}", show_alert=True)



"""
    admin_close_menu_callback_handler

    Этот обработчик обрабатывает callback admin_close для закрытия меню администратора
"""
async def admin_close_menu_callback_handler(callback: types.CallbackQuery):
    if callback.data == "admin_close":
        logger.info(f"Close admin menu by {callback.from_user.id}")
        try:
            await callback.message.delete()
            await callback.answer()
        except Exception as e:
            logger.exception(f"ERROR in admin_close_menu_callback_handler FOR user_id={callback.from_user.id}")
            await callback.answer(f"Ошибка: {str(e)}", show_alert=True)