

# Стандартные библиотеки
import asyncio

# Сторонние библиотеки
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

# Локальные модули
from src.handlers import register_handlers
from src.managers import DataManager, UserManager, EmbeddingManager
from src.utils import logger
from src.services.rasa.client import RasaClient



# Конфигурационные данные
from config import BOT_TOKEN, DATA_FILE

"""
Этот модуль содержит основную логику для запуска Telegram-бота с использованием библиотеки aiogram.
Бот выполняет асинхронные запросы и обрабатывает сообщения и команды, взаимодействуя с пользователем.

Основные шаги работы бота:
1. Инициализация и создание объекта бота с указанным токеном.
2. Настройка диспетчера (Dispatcher), который управляет состоянием и обработкой сообщений.
3. Регистрация обработчиков для команд и запросов от пользователя.
4. Запуск процесса поллинга (опроса новых сообщений) для получения обновлений от Telegram.
5. Закрытие сессии и завершение работы бота при остановке.

Основные компоненты:
- Bot: объект, представляющий Telegram-бота.
- Dispatcher: объект, управляющий обработкой сообщений и состоянием.
- DataManager: класс, используемый для управления данными, связанными с ботом.
- Logger: компонент для логирования событий в процессе работы.

Файл настроен для асинхронного запуска, что позволяет эффективно обрабатывать запросы и не блокировать другие операции.
"""


async def main():
    """
    Главная асинхронная функция, запускающая бота.

    1. Инициализирует DataManager для работы с данными (например, база данных, файлы).
    2. Создает объект бота с помощью токена из конфигурации и устанавливает режим парсинга сообщений (HTML).
    3. Создает диспетчер с использованием памяти для хранения состояний FSM (Finite State Machine).
    4. Регистрирует обработчики команд и запросов, обеспечивая реакцию на различные команды пользователя.
    5. Запускает процесс поллинга для получения новых сообщений от пользователей.
    6. После завершения работы бота, закрывает сессию и завершает работу.

    Исключения и завершение работы обрабатываются в блоке finally для корректного закрытия сессии.
    """
    dm = DataManager.initialize(DATA_FILE)  # Инициализация менеджера данных
    em = EmbeddingManager(dm)               # Инициализация менеджера
    um = UserManager()                      # Инициализация менеджера пользователей
    rc = RasaClient()                       # Инициализация клиена для работы с моделью rasa

    if not rc.is_available:
        print("[❌] Rasa недоступен. Убедитесь, что API работает:", rc.api_url)
        return

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML,  # Используем HTML-разметку в сообщениях
        )
    )

    bot.data_manager      = dm  # Добавляем менеджер данных в объект бота
    bot.user_manager      = um  # Добавляем менеджер данных в объект бота
    bot.rasa_manager      = rc  # Добавляем клиена для работы с моделью rasa
    bot.embedding_manager = em  # Добавляем клиена для работы с моделью rasa

    dp = Dispatcher(storage=MemoryStorage())  # Создаем диспетчер с хранилищем FSM в памяти
    register_handlers(dp)  # Регистрируем обработчики команд и сообщений


    try:
        logger.info("Starting polling")  # Логируем запуск поллинга
        await dp.start_polling(bot)  # Запускаем поллинг
    except KeyboardInterrupt:
        # Если было нажатие Ctrl+C, просто игнорируем и завершаем
        logger.info("Bot stopped by user (Ctrl+C)")
    except asyncio.CancelledError:
        # В случае отмены задачи asyncio
        logger.info("Polling was cancelled")
    finally:
        # Закрываем сессию и освобождаем ресурсы
        await bot.close()
        logger.info("Bot session closed")


if __name__ == '__main__':
    logger.info("Bot is starting")  # Логируем запуск бота
    asyncio.run(main())  # Запускаем основную асинхронную функцию
    logger.info("Bot stopped")  # Логируем остановку бота
