"""
    Пакет handlers
    Этот пакет загружает все использщуемые ботом обработчики команд
"""

from .all_commands import register_handlers

"""
    Определяем список объектов, которые будут доступны при импорте пакета
"""
__all__ = ["register_handlers"]
