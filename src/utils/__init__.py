"""
    ╔════════════════════════════════════════════╗
    ║              __init__.py                   ║
    ╚════════════════════════════════════════════╝
    
    Инициализационный модуль пакета утилит
    
    Описание:
        Данный модуль инициализирует пакет утилит и экспортирует
        основные инструменты для использования в других модулях
        приложения
    
    Экспорты:
        • logger           - модуль логирования с настройкой через logger
        • LoggerSetup      - модуль настройки и создания нового logger
        • preprocessor     - модуль для предобработки текста
"""

from .utils_logger         import logger, LoggerSetup
from .utils_preprocessor   import preprocessor
from .utils_file_processor import ExcelProcessor

__all__ = ["logger", "LoggerSetup", "preprocessor", "ExcelProcessor"]
