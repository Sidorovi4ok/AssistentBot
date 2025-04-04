
# Импортируем необходимые модули.
from aiogram import types

# `logger` используется для логирования действий пользователей.
from src.utils.logger import logger


async def help_handler(message: types.Message):
    """
    Обработчик команды /help.

    Выдает справочную информацию о возможностях бота.

    Логирует запрос от пользователя и отправляет список доступных команд.
    """

    # Логируем получение команды /help от пользователя
    logger.info(f"Received help command from {message.from_user.id}")

    # Составляем текст справочного меню с командами и их описанием
    help_text = (
        "🤖 <b>Меню поддержки @YourAssistent</b>\n\n"
        
        "🚀 <i>Запуск бота</i>\n"
        "/start - Запустить/перезапустить бота\n\n"
        
        "🎁 <i>Запросы</i>\n"
        "/request - Отправить новый запрос\n"
        "/history - История запросов (В процессе)\n\n"
        
        "ℹ️ <i>Информация</i>\n"
        "/role - Ваша роль в системе\n"
        "/help - Меню поддержки\n"
        "/info - Подробная информация обо мне\n\n"
        
        "⚙️ <i>Настройки</i>\n"
        "/settings - Открыть настройки (В процессе)\n\n"
        
        "💻 <i>Еще наши приложения</i>\n"
        "Наш веб-сайт - ?ссылка?\n"
        "Наше приложение - ?ссылка?\n"
        "/about - Информация о нашей компании\n\n"
        
        "💡 Нужно больше деталей? Просто выбери команду!"
    )

    # Отправляем пользователю справочное сообщение
    await message.answer(help_text)
