"""
    ╔════════════════════════════════════════════╗
    ║           rasa/client.py                   ║
    ╚════════════════════════════════════════════╝
    
    Клиент для взаимодействия с Rasa NLU сервером
    
    Описание:
        Асинхронный клиент для работы с Rasa NLU API:
        • Отправка запросов на обработку текста
        • Извлечение сущностей
        • Определение намерений
        • Определение целевой колонки для поиска
    
    Зависимости:
        • aiohttp - для асинхронных HTTP запросов
        • config - для получения api сервера
        • logger - для логирования
"""


import sys
import aiohttp

from pathlib import Path
from typing  import Dict, Optional, Any, Tuple

sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from config     import config
from src.utils  import logger




class RasaClient:
    """
        Класс для работы с Rasa моделью
    """
    
    def __init__(self, api_url: Optional[str] = config.services.rasa_url):
        """
            Инициализация клиента
        """
        self.api_url = api_url
        self._session: Optional[aiohttp.ClientSession] = None
        
        
    async def __aenter__(self):
        """
            Создание сессии при входе в контекстный менеджер
        """
        self._session = aiohttp.ClientSession()
        return self
        
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
            Закрытие сессии при выходе из контекстного менеджера
        """
        if self._session:
            await self._session.close()
            
            
    @classmethod
    async def check_availability(cls, api_url: Optional[str] = config.services.rasa_url) -> bool:
        """
            Проверка доступности Rasa API
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(api_url, json={"text": "test"}) as response:
                    if response.status == 200:
                        logger.info("✓ Rasa NLU API доступен и работает")
                        return True
                    logger.warning(f"⚠ Ошибка при запросе к Rasa NLU API: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"❌ Rasa NLU API недоступен: {str(e)}")
            return False
            
            
    async def query(self, text: str) -> Optional[Dict[str, Any]]:
        """
            Отправка запроса в Rasa NLU
        """
        if not self._session:
            self._session = aiohttp.ClientSession()
            
        try:
            async with self._session.post(self.api_url, json={"text": text}) as response:
                if response.status == 200:
                    return await response.json()
                logger.warning(f"⚠ Ошибка при запросе к Rasa NLU API: {response.status}")
                return None
        except Exception as e:
            logger.error(f"❌ Исключение при обращении к Rasa NLU API: {str(e)}")
            return None
            
            
    async def process_query(self, query_text: str) -> Tuple[Dict[str, str], str, str]:
        """
            Обработка запроса и получение всех данных сразу
        """
        response = await self.query(query_text)
        if not response:
            return {}, "unknown", "Наименование"
            
        # Извлечение сущностей
        entities = response.get("entities", {})
        
        # Определение намерения
        intent = response.get("intent", "unknown")
        
        # Определение целевой колонки
        target_column = "Наименование"  # значение по умолчанию
        
        # Проверка сущностей для определения колонки
        if "artikul" in entities:
            target_column = "Артикул"
        elif "naimenovanie" in entities:
            target_column = "Наименование"
            
        # Проверка намерения для определения колонки
        if intent == "search_by_artikul":
            target_column = "Артикул"
        elif intent == "search_by_naimenovanie":
            target_column = "Наименование"
            
            
        # ДОБАВИТЬ ОПИСАНИЕ СЮДА
            
        return entities, intent, target_column
        
    async def close(self):
        """
            Закрытие сессии клиента
        """
        if self._session:
            await self._session.close()
            self._session = None
