
# Импортируем необходимые классы и функции из библиотеки aiogram для обработки сообщений.
from aiogram import types
from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Импортируем логгер для логирования информации о процессе работы с пользователем.
from src.utils.logger import logger


async def admin_handler(message: types.Message):
    """
    Обработчик команды /start.

    Этот обработчик приветствует пользователя, отправляет информацию о боте и выводит меню с доступными функциями.

    Параметры:
    - message (types.Message): Сообщение от пользователя, включающее данные о нем и запрос.
    """

    # Логируем информацию о полученной команде /start от пользователя
    logger.info(f"Received start command from {message.from_user.id}")

    admin_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📄 Последние логи", callback_data="get_logs")],
        [InlineKeyboardButton(text="👥 Управление пользователями", callback_data="get_users")],
    ])

    await message.answer(
        f"🛠 Админ-панель\nДобро пожаловать, {message.from_user.first_name}!",
        reply_markup=admin_kb
    )


async def get_log_callback_handler(callback_query: types.CallbackQuery):

    if callback_query.data == "get_logs":
        logger.info(f"Get logs by {callback_query.from_user.id}")

        try:
            with open("logs/main.log", "r") as f:
                logs = f.readlines()[-20:]
            await callback_query.message.edit_text(
                f"<b>Последние логи:</b>\n<code>{''.join(logs)}</code>",
                parse_mode="HTML"
            )
        except Exception as e:
            await callback_query.answer(f"Ошибка: {str(e)}", show_alert=True)



async def control_users_callback_handler(callback_query: types.CallbackQuery):

    if callback_query.data == "get_users":
        logger.info(f"Gets users by {callback_query.from_user.id}")

        user_management_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Список пользователей", callback_data="list_users")],
            [InlineKeyboardButton(text="Изменить пользователя", callback_data="edit_user")],
            [InlineKeyboardButton(text="Удалить пользователя", callback_data="delete_user")],
            [InlineKeyboardButton(text="◀ Назад", callback_data="back_to_admin")]
        ])

        await callback_query.message.edit_text(
            "👥 Управление пользователями:",
            reply_markup=user_management_kb
        )
