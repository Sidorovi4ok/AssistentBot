"""
    ╔════════════════════════════════════════════╗
    ║              logger.py                     ║
    ╚════════════════════════════════════════════╝
    
    Описание:
        Модуль предоставляет функционал для настройки и использования
        системы логирования в приложении. Включает:
        • Настройку логгеров с различными обработчиками
        • Ротацию лог-файлов
        • Форматирование сообщений
        • Управление уровнями логирования
        • Цветной вывод в консоль
        • JSON форматирование
        • Асинхронное логирование
    
    Примеры использования:
        1. Базовое использование:
        from src.utils.logger import logger
        
        logger.info("Запуск приложения")
        logger.error("Произошла ошибка: %s", error_message)
        logger.debug("Отладочная информация: %s", debug_data)
        
        2. Создание кастомного логгера:
        from src.utils.logger import LoggerSetup
        
        custom_logger = LoggerSetup(
            name="custom",
            log_file="custom.log",
            level=DEBUG,
            console_output=False
        ).get_logger()
        
        custom_logger.warning("Предупреждение в кастомном логгере")
        
        3. Логирование с контекстом:
        logger.info("Пользователь %s выполнил действие %s", user_id, action)
        logger.error("Ошибка в модуле %s: %s", module_name, error)
        
        4. Использование контекстного менеджера:
        with logger.context(level=DEBUG):
            logger.debug("Временное включение отладки")
            # ... код с отладочными сообщениями ...
        
        5. JSON логирование:
        logger.json({"event": "user_action", "user_id": 123, "action": "login"})
"""



import sys
import json

from pathlib          import Path
from typing           import Union, Dict, Any, Optional
from contextlib       import contextmanager
from logging.handlers import RotatingFileHandler

from logging import (
    Logger, 
    getLogger,
    StreamHandler,
    Formatter,
    INFO, 
    DEBUG, 
    WARNING, 
    ERROR, 
    CRITICAL
)



class ColoredFormatter(Formatter):
    """
        Форматтер с цветным выводом для консоли
    """
    
    # Словарь соответствия уровней логирования и цветов
    level_colors = {
        DEBUG:    '\033[36m', # Голубой
        INFO:     '\033[32m', # Зеленый
        WARNING:  '\033[33m', # Желтый
        ERROR:    '\033[31m', # Красный
        CRITICAL: '\033[35m'  # Пурпурный
    }
    
    def format(self, record):
        if record.levelno in self.level_colors:
            color = self.level_colors[record.levelno]
            record.levelname = f"{color}{record.levelname}{'\033[0m'}"
        return super().format(record)


class JsonFormatter(Formatter):
    """
        Форматтер для JSON логирования
    """
    
    def format(self, record):
        log_data = {
            'timestamp': self.formatTime(record),
            'level':     record.levelname,
            'message':   record.getMessage(),
            'module':    record.module,
            'function':  record.funcName,
            'line':      record.lineno
        }
        if hasattr(record, 'json_data'):
            log_data.update(record.json_data)
        return json.dumps(log_data)



class LoggerSetup:
    """
        Класс для настройки и управления логгерами
    """
    
    def __init__(
        self,
        name:           str       = 'app',
        log_dir: Union[str, Path] = 'logs',
        log_file:       str       = 'main.log',
        level:          int       = INFO,
        format_str:     str       = '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        date_format:    str       = '%Y-%m-%d %H:%M:%S',
        max_bytes:      int       = 10 * 1024 * 1024,
        backup_count:   int       = 5,
        console_output: bool      = True,
        json_format:    bool      = False
    ):
        """
            Инициализация настроек логгера
        """

        self.name           = name                      # Имя логгера
        self.log_dir        = Path(log_dir)             # Директория для хранения логов
        self.log_file       = self.log_dir / log_file   # Имя файла логов
        self.level          = level                     # Формат сообщений логов
        self.format_str     = format_str                # Формат даты в логах
        self.date_format    = date_format               # Максимальный размер файла логов
        self.max_bytes      = max_bytes                 # Максимальный размер файла логов
        self.backup_count   = backup_count              # Количество файлов ротации
        self.console_output = console_output            # Включить вывод в консоль
        self.json_format    = json_format               # Использовать JSON формат для файлового логгера
        
        # Создаем директорию для логов если её нет
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Инициализируем логгер
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> Logger:
        """
            Настройка и возврат логгера
        """
        logger = getLogger(self.name)
        logger.setLevel(self.level)
        
        # Очищаем существующие обработчики
        logger.handlers.clear()
        
        # Создаем форматтеры
        console_formatter = ColoredFormatter(
            fmt     = self.format_str,
            datefmt = self.date_format
        )
        
        file_formatter = JsonFormatter() if self.json_format else Formatter(
            fmt     = self.format_str,
            datefmt = self.date_format
        )
        
        # Добавляем обработчик файла с ротацией
        file_handler = RotatingFileHandler(
            filename    = self.log_file,
            maxBytes    = self.max_bytes,
            backupCount = self.backup_count,
            encoding    = 'utf-8'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        # Добавляем вывод в консоль если нужно
        if self.console_output:
            console_handler = StreamHandler(sys.stdout)
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
        
        # Добавляем метод для JSON логирования
        def json_log(self, data: Dict[str, Any], level: int = INFO):
            """
                Логирование в JSON формате
            """
            record = self.makeRecord(
                self.name, level, "(unknown file)", 0,
                msg="", args=(), exc_info=None
            )
            record.json_data = data
            self.handle(record)
        
        logger.json = json_log.__get__(logger)
        
        # Добавляем контекстный менеджер
        @contextmanager
        def context(self, level: Optional[int] = None):
            """
                Временное изменение уровня логирования
            """
            old_level = logger.level
            if level is not None:
                logger.setLevel(level)
            try:
                yield logger
            finally:
                logger.setLevel(old_level)
        logger.context = context.__get__(logger)
        return logger
    
    def get_logger(self) -> Logger:
        """
            Получить настроенный логгер
        """
        return self.logger



# Создаем глобальный логгер по умолчанию
logger = LoggerSetup().get_logger()