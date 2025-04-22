"""
    ╔════════════════════════════════════════════════════════════╗
    ║                    Модуль managers/__init__.py             ║
    ╚════════════════════════════════════════════════════════════╝

    Описание:
        Пакет managers содержит классы для управления различными аспектами приложения:
        - DataManager:      Управление данными 
        - UserManager:      Управление пользователями бота
        - EmbeddingManager: Управление векторными представлениями
"""

from .manager_price      import DataManager         
from .manager_user       import UserManager         
from .manager_embedding  import EmbeddingManager    

__all__ = ["DataManager", "UserManager", "EmbeddingManager"]
