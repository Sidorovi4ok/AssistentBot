"""
    ╔════════════════════════════════════════════╗
    ║                ИМПОРТЫ                     ║
    ╚════════════════════════════════════════════╝
"""

import asyncio

from aiogram                    import Bot, Dispatcher
from aiogram.enums              import ParseMode
from aiogram.client.default     import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from src.handlers               import register_handlers
from src.managers               import DataManager, UserManager, EmbeddingManager
from src.services.rasa.client   import RasaClient
from src.utils                  import logger

from config import BOT_TOKEN, DATA_FILE

"""
    ╔════════════════════════════════════════════╗
    ║           Функция запуска бота             ║
    ╚════════════════════════════════════════════╝
"""

async def main():
    # Инициализация менеджера для работы с данными
    data_manager = DataManager.initialize(DATA_FILE)

    # Инициализация менеджера для работы с эмбеддингами
    embedding_manager = EmbeddingManager(data_manager)

    # Инициализация менеджера для работы с пользователями
    user_manager = UserManager()

    # Инициализация клиена для работы с нашей моделью rasa
    raca_manager = RasaClient()
    if not raca_manager.is_available:
        print("[❌] Rasa недоступен. Убедитесь, что API работает:", rc.api_url)
        return

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML,
        )
    )

    bot.data_manager      = data_manager
    bot.embedding_manager = embedding_manager
    bot.user_manager      = user_manager
    bot.rasa_manager      = raca_manager


    dp = Dispatcher(storage=MemoryStorage())
    register_handlers(dp)

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
