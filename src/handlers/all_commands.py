
"""
     ╔════════════════════════════════════════════════════════════╗
     ║                     ИМПОРТЫ МОДУЛЕЙ                        ║
     ╚════════════════════════════════════════════════════════════╝
"""

# Базовые импорты Aiogram
from aiogram         import Dispatcher
from aiogram.filters import Command
from aiogram         import F

# Обработчики команд
from src.handlers.handler_start     import start_handler
from src.handlers.handler_help      import help_handler
from src.handlers.handler_info      import info_handler
from src.handlers.handler_about     import about_handler
from src.handlers.handler_role      import role_handler
from src.handlers.handler_unknown import unknown_message_handler

# Обработчики запросов
from src.handlers.handler_request import (
    RequestStates, request_handler, receive_request,
    cancel_callback_handler, tables_callback_handler,
    request_text_menu, request_file_menu, request_get_example,
    request_back_main_menu, request_close_menu, request_from_file,
    handle_request_excel_file
    
)

# Авторизация / Регистрация
from src.handlers.handler_auth import (
    AuthStates, cmd_login, process_login_inn, cmd_register, process_register_inn
)

# ──🛠 Админ-панель
from src.handlers.handler_admin import (
    cmd_admin_handler, admin_logs_menu_callback_handler, admin_view_logs_callback_handler,
    admin_download_logs_callback_handler, admin_back_menu_callback_handler,
    admin_db_menu_callback_handler, admin_close_menu_callback_handler,
    admin_get_users_callback_handler, admin_update_db_callback_handler,
    admin_useful_button_callback_handler
)

# ──🛠 Менеджер-панель
from src.handlers.handler_manager import (
    ManagerPanelStates,
    cmd_manager_handler, manager_products_menu_callback_handler, manager_back_menu_callback_handler,
    manager_close_menu_callback_handler, manager_users_menu_callback_handler,
    manager_get_users_callback_handler, manager_download_excel_callback_handler,
    manager_update_excel_callback_handler, manager_get_user_callback_handler,
    manager_change_user_callback_handler, manager_change_type_user_callback_handler,
    manager_change_type_handler, manager_change_discount_callback_handler,
    manager_wait_user_type_callback_handler, manager_wait_new_discount_callback_handler,
    handle_excel_file, handle_inn_user,
)


# ──⚙️ Кастомные фильтры
from src.filters import (
    filter_only_auth,
    filter_only_manager,
    filter_only_admin

)



"""
    ╔════════════════════════════════════════════════════════════╗
    ║                РЕГИСТРАЦИИ ХЕНДЛЕРОВ                       ║
    ║                           И                                ║
    ║                 CALLBACK-ОБРАБОТЧИКОВ                      ║
    ╚════════════════════════════════════════════════════════════╝
"""


"""
    Регистрирует все обработчики команд и callback-запросов для бота
"""
def register_handlers(dp: Dispatcher):


    # Команды общего доступа
    dp.message.register(start_handler,    Command(commands=["start"]))
    dp.message.register(help_handler,     Command(commands=["help"]))
    dp.message.register(info_handler,     Command(commands=["info"]))
    dp.message.register(about_handler,    Command(commands=["about"]))
    dp.message.register(role_handler,     Command(commands=["role"]))


    # Авторизация / Регистрация
    dp.message.register(cmd_login,        Command(commands=["login"]))
    dp.message.register(cmd_register,     Command(commands=["register"]))
    dp.message.register(process_login_inn,    AuthStates.waiting_for_inn_login)
    dp.message.register(process_register_inn, AuthStates.waiting_for_inn_register)


    # Запросы
    dp.message.register(request_handler,  Command(commands=["request"]))
    dp.message.register(receive_request,                RequestStates.waiting_for_request,                                       filter_only_auth)
    dp.message.register(handle_request_excel_file,      RequestStates.waiting_for_file,                                          filter_only_auth)
        
    dp.callback_query.register(request_text_menu,                                    F.data.startswith("request_text_menu"),      filter_only_auth)
    dp.callback_query.register(tables_callback_handler, RequestStates.choosing_list, F.data.startswith("sheet_"),                 filter_only_auth)
    dp.callback_query.register(request_file_menu,                                    F.data.startswith("request_file_menu"),      filter_only_auth)
    dp.callback_query.register(request_from_file,                                    F.data.startswith("request_from_file"),      filter_only_auth)
    dp.callback_query.register(request_get_example,                                  F.data.startswith("request_get_example"),    filter_only_auth)
    dp.callback_query.register(request_back_main_menu,                               F.data.startswith("request_back_main_menu"), filter_only_auth)
    dp.callback_query.register(request_close_menu,                                   F.data.startswith("request_close_menu"),     filter_only_auth)
    dp.callback_query.register(cancel_callback_handler,                              F.data.startswith("cancel_"),                filter_only_auth) 


    # Менеджерские команды
    dp.message.register(cmd_manager_handler, Command(commands=["manager_panel"]), filter_only_manager)
    
    dp.callback_query.register(manager_users_menu_callback_handler,       F.data.startswith("manager_menu_users"),       filter_only_manager)
    dp.callback_query.register(manager_products_menu_callback_handler,    F.data.startswith("manager_menu_products"),    filter_only_manager)
    dp.callback_query.register(manager_get_users_callback_handler,        F.data.startswith("manager_get_users"),        filter_only_manager)
    dp.callback_query.register(manager_get_user_callback_handler,         F.data.startswith("manager_get_user"),         filter_only_manager)
    dp.callback_query.register(manager_change_user_callback_handler,      F.data.startswith("manager_change_user"),      filter_only_manager)
    dp.callback_query.register(manager_change_type_user_callback_handler, F.data.startswith("manager_change_type_user"), filter_only_manager)
    dp.callback_query.register(manager_change_discount_callback_handler,  F.data.startswith("manager_change_discount"),  filter_only_manager)
    dp.callback_query.register(manager_download_excel_callback_handler,   F.data.startswith("manager_download_excel"),   filter_only_manager)
    dp.callback_query.register(manager_update_excel_callback_handler,     F.data.startswith("manager_update_excel"),     filter_only_manager)
    dp.callback_query.register(manager_back_menu_callback_handler,        F.data.startswith("manager_back"),             filter_only_manager)
    dp.callback_query.register(manager_close_menu_callback_handler,       F.data.startswith("manager_close_menu"),       filter_only_manager)
    
    # Ожидание ввода данных пользователем
    dp.message.register(handle_excel_file,                              ManagerPanelStates.waiting_for_file,             filter_only_manager)
    dp.message.register(handle_inn_user,                                ManagerPanelStates.waiting_for_inn,              filter_only_manager)
    dp.message.register(manager_change_type_handler,                    ManagerPanelStates.waiting_for_type,             filter_only_manager)
    
    dp.callback_query.register(manager_wait_user_type_callback_handler, ManagerPanelStates.waiting_for_type_discount,    filter_only_manager)
    dp.message.register(manager_wait_new_discount_callback_handler,     ManagerPanelStates.waiting_for_new_discount,     filter_only_manager)


    # Админские команды
    dp.message.register(cmd_admin_handler, Command(commands=["admin_panel"]), filter_only_admin)

    dp.callback_query.register(admin_logs_menu_callback_handler,     F.data.startswith("menu_logs"),        filter_only_admin)
    dp.callback_query.register(admin_db_menu_callback_handler,       F.data.startswith("menu_db"),          filter_only_admin)
    dp.callback_query.register(admin_useful_button_callback_handler, F.data.startswith("useful_button"),    filter_only_admin)
    dp.callback_query.register(admin_view_logs_callback_handler,     F.data.startswith("get_logs"),         filter_only_admin)
    dp.callback_query.register(admin_download_logs_callback_handler, F.data.startswith("download_logs"),    filter_only_admin)
    dp.callback_query.register(admin_get_users_callback_handler,     F.data.startswith("admin_get_users"),  filter_only_admin)
    dp.callback_query.register(admin_update_db_callback_handler,     F.data.startswith("admin_update_db"),  filter_only_admin)
    dp.callback_query.register(admin_back_menu_callback_handler,     F.data.startswith("admin_back"),       filter_only_admin)
    dp.callback_query.register(admin_close_menu_callback_handler,    F.data.startswith("admin_close"),      filter_only_admin)

    # Если ни один обработчик не сработал
    #dp.message.register(unknown_message_handler)


