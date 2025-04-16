
"""
    config.py

    Этот модуль загружает конфигурационные переменные из файла .env
    и предоставляет их для использования в других частях бота и служит для быстрой настройки
"""

import os
from dotenv import load_dotenv

load_dotenv()


"""
    Основные настройки бота
    BOT_TOKEN - Токен бота для работы с Telegram API
    BOT_NAME  - Имя бота (для справки)
    BOT_TAG   - @username бота в Telegram
"""
BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_NAME  = os.getenv("BOT_NAME")
BOT_TAG   = os.getenv("BOT_TAG")



"""
    Настройка данных
    DATA_FILE - Файл с данными товаров компании
"""
DATA_FILE = os.getenv("DATA_FILE")



"""
    Настройка пользователей 
    ALLOWED_MANAGERS - ID телеграма менеджеров
    ALLOWED_ADMINS   - ID телеграма админов
"""
ALLOWED_MANAGERS = [804676300, 1900362240]
ALLOWED_ADMINS   = [6715041286, 804676300, 1900362240]



"""
    Настройка сервисов 
    RASA_API_URL - API для работы с моделью rasa
    API_AI       - API для работы с моделью из https://ai.io.net/
"""
RASA_API_URL = os.getenv("RASA_API_URL")
API_AI       = os.getenv("API_AI")