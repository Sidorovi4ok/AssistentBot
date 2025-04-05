"""
Модуль для регистрации обработчиков, логирования и обработки данных.

Описание:
1. Импортируется `logger` для логирования сообщений.
2. Импортируется `DataManager` для работы с данными (например, базы данных и Excel).
3. Импортируется `VectorSearchManager` для поиска по векторным представлениям (например, для поиска по эмбеддингам).
4. Импортируются функции фильтрации: `filter_article_extract` и `filter_product_name` для обработки и извлечения данных из запросов пользователя.

Объекты, доступные при импорте:
- logger
- DataManager
- VectorSearchManager
- filter_article_extract
- filter_product_name
"""

# Импортируем необходимые модули для логирования, работы с данными и поиска
from .logger import logger  # Логирование с настройкой через logger
from .manager import DataManager  # Менеджер данных для работы с Excel и базой данных
from .search import VectorSearchManager  # Поиск по векторным представлениям (FAISS)
from .filters import filter_article_extract, filter_product_name, filter_only_manager  # Фильтры для обработки запросов

# Определяем список объектов, которые будут доступны при импорте пакета.
__all__ = ["logger", "DataManager", "VectorSearchManager", "filter_article_extract", "filter_product_name", "filter_only_manager"]
