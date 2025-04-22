"""
    ╔════════════════════════════════════════════╗
    ║                config.py                   ║
    ╚════════════════════════════════════════════╝
    
    Описание:
    ---------
    Центральный модуль конфигурации, содержащий:
    • Основные настройки Telegram-бота
    • Параметры доступа и авторизации
    • Конфигурацию внешних сервисов
    • Пути к данным и ресурсам
    
    Конфигурации:
    -------------
    • Бот:
      - BOT_TOKEN  - токен для API Telegram
      - BOT_NAME   - имя бота Telegram
      - BOT_TAG    - тэг бота Telegram
    
    • Пользователи:
      - ALLOWED_MANAGERS - список ID менеджеров
      - ALLOWED_ADMINS   - список ID администраторов
    
    • Сервисы:
      - RASA_API_URL - endpoint для NLP-модели
      - API_AI       - endpoint для AI-сервиса
    
    • Данные:
      - DATA_FILE    - путь к файлу с данными
"""



import os
from pathlib     import Path
from dotenv      import load_dotenv
from typing      import List
from dataclasses import dataclass


# Загрузка переменных окружения
load_dotenv()


@dataclass
class BotConfig:
    """
        Конфигурация бота
    """
    token: str
    name:  str
    tag:   str

    @classmethod
    def from_env(cls) -> 'BotConfig':
        return cls(
            token = os.getenv("BOT_TOKEN"),
            name  = os.getenv("BOT_NAME"),
            tag   = os.getenv("BOT_TAG")
        )


@dataclass
class UserConfig:
    """
        Конфигурация пользователей
    """
    managers: List[int]
    admins:   List[int]

    @classmethod
    def from_env(cls) -> 'UserConfig':
        return cls(
            managers = [804676300, 1900362240],
            admins   = [6715041286, 804676300, 1900362240]
        )


@dataclass
class ServiceConfig:
    """
        Конфигурация сервисов
    """
    rasa_url: str
    ai_api:   str
    ai_model: str
    ai_key:   str

    @classmethod
    def from_env(cls) -> 'ServiceConfig':
        return cls(
            rasa_url = os.getenv("RASA_API_URL"),
            ai_api   = os.getenv("AI_API"),
            ai_model = os.getenv("AI_MODEL"),
            ai_key   = os.getenv("AI_KEY"),
        )


@dataclass
class DataConfig:
    """
        Конфигурация данных
    """
    data_file: Path

    @classmethod
    def from_env(cls) -> 'DataConfig':
        return cls(
            data_file = Path("data/excel/" + os.getenv("DATA_FILE"))
        )


class Config:
    """
        Основной класс конфигурации
    """
    def __init__(self):
        self.bot      = BotConfig.from_env()
        self.users    = UserConfig.from_env()
        self.services = ServiceConfig.from_env()
        self.data     = DataConfig.from_env()
        
    def validate(self) -> bool:
        """
            Проверка валидности конфигурации
        """
        if not self.bot.token:
            raise ValueError("BOT_TOKEN not installed")
        if not self.services.rasa_url:
            raise ValueError("RASA_API_URL not installed")
        if not self.data.data_file.exists():
            raise FileNotFoundError(f"The data file was not found: {self.data.data_file}")
        return True


# Создание глобального экземпляра конфигурации
config = Config()
config.validate()
