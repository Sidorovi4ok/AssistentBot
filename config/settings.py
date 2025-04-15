"""
config.py

Этот модуль загружает конфигурационные переменные из файла .env
и предоставляет их для использования в других частях бота.

Файл .env должен содержать:
- BOT_TOKEN  — API токен Telegram бота
- BOT_NAME   — Имя бота (для справки)
- BOT_TAG    — @username бота в Telegram
- DATA_FILE  — Имя файла с данными (например, список товаров)
"""

# Импортируем необходимые модули.
import os
from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env
load_dotenv()

# Основные настройки бота
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Токен бота для работы с Telegram API
BOT_NAME  = os.getenv("BOT_NAME")   # Имя бота (для справки)
BOT_TAG   = os.getenv("BOT_TAG")    # @username бота в Telegram

# Файл с данными (например, список товаров)
DATA_FILE = os.getenv("DATA_FILE")

# ID менеджеров в телеграме
ALLOWED_MANAGERS = [804676300, 1900362240]
ALLOWED_ADMINS = [6715041286]