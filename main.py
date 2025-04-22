"""
    ╔════════════════════════════════════════════╗
    ║                main.py                     ║
    ╚════════════════════════════════════════════╝
    
    Описание:
        Основной модуль приложения, отвечающий за:
        • Инициализацию всех необходимых компонентов системы
        • Настройку и конфигурацию телеграм-бота
        • Управление жизненным циклом бота

    Компоненты:
        • DataManager      - управление данными и их хранением
        • UserManager      - управление пользователями и их данными
        • EmbeddingManager - работа с векторными представлениями
        • RasaClient       - взаимодействие с rasa-моделью
        
    Зависимости:
        • aiogram    - библиотека для создания телеграм-ботов
        • asyncio    - библиотека для асинхронной работы
"""



import asyncio

from aiogram                    import Bot, Dispatcher
from aiogram.enums              import ParseMode
from aiogram.client.default     import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from src.handlers               import register_handlers
from src.managers               import DataManager, UserManager, EmbeddingManager
from src.services               import RasaClient
from src.utils                  import logger

from config                     import config



async def main():
    """
        Основная функция инициализации и запуска бота
    """
    
    dm = DataManager.initialize(config.data.data_file)
    em = EmbeddingManager(dm)
    um = UserManager()
    
    
    if not await RasaClient.check_availability():
        return

    # Создание и настройка экземпляра бота
    bot = Bot(
        token=config.bot.token,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML,
        )
    )

    # Привязка менеджеров к экземпляру бота для удобного доступа
    bot.dm = dm
    bot.um = um
    bot.em = em

    # Создание диспетчера и регистрация обработчиков
    dp = Dispatcher(storage=MemoryStorage())
    register_handlers(dp)

    # Запуск бота и обработка исключений
    try:
        logger.info("Starting polling")
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user (Ctrl+C)")
    except asyncio.CancelledError:
        logger.info("Polling was cancelled")
    finally:
        await bot.close()
        logger.info("Bot session closed")


if __name__ == '__main__':
    logger.info("Bot is starting")
    asyncio.run(main())
    logger.info("Bot stopped")
