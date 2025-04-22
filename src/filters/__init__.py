"""
    ╔════════════════════════════════════════════╗
    ║              filters/__init__.py           ║
    ╚════════════════════════════════════════════╝

    Описание:
        Пакет фильтров для Telegram бота.
        Содержит фильтры для проверки прав доступа и авторизации пользователей.

    Компоненты:
        • filter_not_authorized - фильтр для неавторизованных пользователей
        • filter_only_auth - фильтр для авторизованных пользователей
        • filter_only_manager - фильтр для пользователей с правами менеджера
        • filter_only_admin - фильтр для пользователей с правами администратора

"""

from .filter_not_auth     import filter_not_authorized
from .filter_only_auth    import filter_only_auth
from .filter_only_manager import filter_only_manager
from .filter_only_admin   import filter_only_admin

__all__ = [
    "filter_article",
    "filter_product_name",
    "filter_not_authorized",
    "filter_only_auth",
    "filter_only_manager",
    "filter_only_admin"
]
