
# Импортируем необходимые модули для работы с Aiogram
from aiogram                import Dispatcher, types
from aiogram.filters        import Command
from aiogram                import F

# Импортируем обработчики команд
from src.handlers.start     import start_handler
from src.handlers.help      import help_handler
from src.handlers.info      import info_handler
from src.handlers.settings  import settings_handler
from src.handlers.about     import about_handler

# Импортируем обработчики команд, связанных с запросами
from src.handlers.request   import (
    RequestStates,
    request_handler,
    receive_request,
    cancel_callback_handler,
    tables_callback_handler,
    search_priority_callback_handler
)


def register_handlers(dp: Dispatcher):
    """
    Регистрирует все обработчики команд и callback-запросов для бота.

    Вызывается из main.py.
    """

    # Регистрация текстовых команд
    dp.message.register(start_handler, Command(commands=["start"]))
    dp.message.register(request_handler, Command(commands=["request"]))
    dp.message.register(help_handler, Command(commands=["help"]))
    dp.message.register(info_handler, Command(commands=["info"]))
    dp.message.register(settings_handler, Command(commands=["settings"]))
    dp.message.register(about_handler, Command(commands=["about"]))

    # Регистрация обработчика для получения запросов в состоянии ожидания ввода
    dp.message.register(receive_request, RequestStates.waiting_for_request)

    # Регистрация обработчиков callback-запросов
    dp.callback_query.register(
        tables_callback_handler,
        RequestStates.choosing_list,
        F.data.startswith("sheet_")
    )
    dp.callback_query.register(
        cancel_callback_handler,
        RequestStates.choosing_list,
        F.data.startswith("cancel_")
    )
    dp.callback_query.register(
        search_priority_callback_handler,
        RequestStates.choosing_list,
        F.data.startswith("priority_")
    )
