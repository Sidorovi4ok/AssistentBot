"""
Модуль для настройки и использования логирования в приложении.

Описание:
1. Функция setup_logger настраивает логгер с заданным именем, уровнем логирования и форматом.
2. Пример создания логгера для основного файла и команд.
"""

# Стандартная библиотека для логирования
import logging


def setup_logger(name, log_file, level=logging.INFO):
    """
    Настроить логгер с заданными параметрами.

    Аргументы:
    - name (str): Имя логгера.
    - log_file (str): Путь к файлу, в который будет записываться лог.
    - level (int): Уровень логирования (по умолчанию INFO).

    Возвращает:
    - logging.Logger: Настроенный логгер.
    """
    # Создание форматтера для логов
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Создание обработчика для записи логов в файл
    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)

    # Получаем экземпляр логгера
    cur_log = logging.getLogger(name)
    cur_log.setLevel(level)  # Устанавливаем уровень логирования
    cur_log.addHandler(handler)  # Добавляем обработчик в логгер

    return cur_log


# Пример создания логгера
logger = setup_logger('logger', 'logs/main.log')
