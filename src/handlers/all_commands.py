
# Импортируем необходимые модули для работы с Aiogram
from aiogram                import Dispatcher, types
from aiogram.filters        import Command
from aiogram                import F

# Импортируем обработчики команд
from src.handlers.handler_start     import start_handler
from src.handlers.handler_help      import help_handler
from src.handlers.handler_info      import info_handler
from src.handlers.handler_settings  import settings_handler
from src.handlers.handler_about     import about_handler
from src.handlers.handler_role      import role_handler
from src.handlers.handler_type      import cmd_change_type
from src.handlers.handler_client    import cmd_get_user

# Импортируем обработчики команд, связанных с запросами
from src.handlers.handler_request   import (
    RequestStates,
    request_handler,
    receive_request,
    cancel_callback_handler,
    tables_callback_handler,
    search_priority_callback_handler
)

# Импорт обработчиков авторизации/регистрации
from src.handlers.handler_auth import (
    AuthStates,
    cmd_login,
    process_login_inn,
    cmd_register,
    process_register_inn
)

from src.filters import filter_not_authorized, filter_only_auth, filter_only_manager


def register_handlers(dp: Dispatcher):
    """
    Регистрирует все обработчики команд и callback-запросов для бота.
    Вызывается из main.py.
    """
    # Регистрация текстовых команд
    dp.message.register(start_handler,    Command(commands=["start"]))


    # Регистрируем обработчики авторизации/регистрации
    dp.message.register(cmd_login,        Command(commands=["login"]),    filter_not_authorized)
    dp.message.register(cmd_register,     Command(commands=["register"]), filter_not_authorized)
    dp.message.register(process_login_inn,    AuthStates.waiting_for_inn_login)
    dp.message.register(process_register_inn, AuthStates.waiting_for_inn_register)


    # Регистрируем обработчики запросов
    dp.message.register(request_handler,  Command(commands=["request"]), filter_only_auth)
    dp.message.register(receive_request, RequestStates.waiting_for_request)


    # Регистрируем обработчики для менеджеров
    dp.message.register(cmd_change_type, Command(commands=["change_type"]), filter_only_manager)
    dp.message.register(cmd_get_user,    Command(commands=["get_user"]),    filter_only_manager)


    # Регистрируем обработчики информации
    dp.message.register(role_handler,     Command(commands=["role"]))
    dp.message.register(help_handler,     Command(commands=["help"]))
    dp.message.register(info_handler,     Command(commands=["info"]))
    dp.message.register(about_handler,    Command(commands=["about"]))
    dp.message.register(settings_handler, Command(commands=["settings"]))


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
