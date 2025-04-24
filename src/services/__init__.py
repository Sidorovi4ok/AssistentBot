"""
    ╔════════════════════════════════════════════════════════════╗
    ║                Модуль services/__init__.py                 ║
    ╚════════════════════════════════════════════════════════════╝

    Описание:
        Пакет содержит сервисы для обработки и генерации текста, а также
        взаимодействия с внешними API. Включает интеграцию с Rasa для
        обработки естественного языка и генерацию текста с помощью LLM.

    Основные компоненты:
        - RasaClient:    Клиент для взаимодействия с Rasa API
        - TextGenerator: Сервис генерации текста
        - Speller:       Сервис проверки орфографии

"""

from .rasa.client            import RasaClient
from .llama.generation       import TextGenerator
from .speller.yandex_speller import speller

__all__ = ["RasaClient", "TextGenerator", "speller"]
