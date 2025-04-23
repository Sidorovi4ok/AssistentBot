import aiohttp
import asyncio
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum
import re
import html

class SpellerError(Exception):
    """Базовый класс для исключений YandexSpeller"""
    pass

class SpellerAPIError(SpellerError):
    """Ошибка при обращении к API YandexSpeller"""
    pass

class SpellerValidationError(SpellerError):
    """Ошибка валидации входных данных"""
    pass

class SpellerOptions(Enum):
    """Опции проверки орфографии"""
    IGNORE_DIGITS = 2
    IGNORE_URLS = 4
    FIND_REPEAT_WORDS = 8
    IGNORE_LATIN = 16
    IGNORE_CAPITALIZATION = 32
    IGNORE_ROMAN_NUMERALS = 64

@dataclass
class SpellError:
    """Информация об ошибке в тексте"""
    pos: int
    len: int
    word: str
    suggestions: List[str]
    code: int
    message: str

class YandexSpeller:
    """
    Асинхронный клиент для сервиса проверки орфографии YandexSpeller.
    
    Примеры использования:
        ```python
        async with YandexSpeller() as speller:
            # Проверка одного текста
            corrected = await speller.correct("привет")
            
            # Пакетная проверка
            texts = ["привет", "как дела"]
            corrected_batch = await speller.correct_batch(texts)
        ```
    
    Ограничения API:
        - Максимальная длина текста: 10000 символов
        - Максимальное количество запросов: 100 в минуту
        - Поддерживаемые языки: ru, en, uk
    """
    
    # Константы
    MAX_TEXT_LENGTH = 10000
    BASE_URL = "https://speller.yandex.net/services/spellservice.json/checkText"
    SUPPORTED_LANGUAGES = {'ru', 'en', 'uk'}
    
    def __init__(
        self,
        lang: str = 'ru',
        options: int = 0,
        format: str = 'plain',
        timeout: int = 30,
        max_retries: int = 3
    ):
        """
        Инициализация клиента YandexSpeller.
        
        Args:
            lang (str): Язык проверки ('ru', 'en', 'uk')
            options (int): Опции проверки (см. SpellerOptions)
            format (str): Формат текста ('plain', 'html')
            timeout (int): Таймаут запроса в секундах
            max_retries (int): Максимальное количество попыток при ошибке
            
        Raises:
            SpellerValidationError: При некорректных параметрах
        """
        if lang not in self.SUPPORTED_LANGUAGES:
            raise SpellerValidationError(f"Unsupported language: {lang}")
        
        self.lang = lang
        self.options = options
        self.format = format
        self.timeout = timeout
        self.max_retries = max_retries
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Создание сессии при входе в контекстный менеджер"""
        if not self._session:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Закрытие сессии при выходе из контекстного менеджера"""
        await self.close()

    async def close(self):
        """Закрытие сессии"""
        if self._session:
            await self._session.close()
            self._session = None

    def _sanitize_text(self, text: str) -> str:
        """
        Очистка и валидация входного текста.
        
        Args:
            text (str): Исходный текст
            
        Returns:
            str: Очищенный текст
            
        Raises:
            SpellerValidationError: При превышении максимальной длины
        """
        if not isinstance(text, str):
            raise SpellerValidationError("Input must be a string")
            
        if len(text) > self.MAX_TEXT_LENGTH:
            raise SpellerValidationError(
                f"Text length exceeds maximum allowed length of {self.MAX_TEXT_LENGTH}"
            )
            
        # Базовая санитизация
        text = html.escape(text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

    async def correct(self, text: str) -> str:
        """
        Исправляет орфографические ошибки в тексте.
        
        Args:
            text (str): Текст для проверки
            
        Returns:
            str: Исправленный текст
            
        Raises:
            SpellerValidationError: При некорректных входных данных
            SpellerAPIError: При ошибке API
        """
        if not self._session:
            raise SpellerAPIError("Session not initialized. Use async with context manager.")
            
        text = self._sanitize_text(text)
        
        params = {
            'text': text,
            'lang': self.lang,
            'options': self.options,
            'format': self.format
        }
        
        for attempt in range(self.max_retries):
            try:
                async with self._session.get(self.BASE_URL, params=params) as response:
                    response.raise_for_status()
                    errors = await response.json()
                    return self._apply_corrections(text, errors)
            except aiohttp.ClientError as e:
                if attempt == self.max_retries - 1:
                    raise SpellerAPIError(f"API request failed after {self.max_retries} attempts: {str(e)}")
                await asyncio.sleep(1)  # Пауза перед повторной попыткой

    def _apply_corrections(self, original: str, errors: List[Dict[str, Any]]) -> str:
        """
        Применяет исправления к исходному тексту.
        
        Args:
            original (str): Исходный текст
            errors (List[Dict]): Список ошибок от API
            
        Returns:
            str: Исправленный текст
        """
        corrected = original
        for error in reversed(errors):
            spell_error = SpellError(
                pos=error['pos'],
                len=error['len'],
                word=error['word'],
                suggestions=error['s'],
                code=error['code'],
                message=error.get('message', '')
            )
            corrected = (
                corrected[:spell_error.pos] +
                spell_error.suggestions[0] +
                corrected[spell_error.pos + spell_error.len:]
            )
        return corrected

    async def correct_batch(self, texts: List[str]) -> List[str]:
        """
        Обрабатывает несколько текстов асинхронно.
        
        Args:
            texts (List[str]): Список текстов для проверки
            
        Returns:
            List[str]: Список исправленных текстов
            
        Raises:
            SpellerValidationError: При некорректных входных данных
            SpellerAPIError: При ошибке API
        """
        tasks = [self.correct(text) for text in texts]
        return await asyncio.gather(*tasks, return_exceptions=True)

async def test_speller():
    """Тестирование функциональности YandexSpeller"""
    test_cases = [
        "каки товары могут быт для класса математтик",
        "Шырокая река",
        "Програмирование",
        "Hello world!",
        "123 45 6",
        "",
        "Превет, как дыла?",
        "Цена 100 долларов",
        "абобус вама"
    ]

    print("┌" + "─" * 50 + "┐")
    print("│ Тестирование Yandex Speller API".ljust(50) + "│")
    print("├" + "─" * 50 + "┤")

    async with YandexSpeller() as speller:
        for i, text in enumerate(test_cases, 1):
            try:
                corrected = await speller.correct(text)
                print(f"│ Тест #{i}".ljust(50) + "│")
                print(f"│ Оригинал:  {text}".ljust(50) + "│")
                print(f"│ Исправлено: {corrected}".ljust(50) + "│")
                print("├" + "─" * 50 + "┤")
            except Exception as e:
                print(f"│ Ошибка в тесте #{i}: {str(e)}".ljust(50) + "│")

        # Тест пакетной обработки
        batch_test = ["правествие", "класнае задание"]
        print("│ Пакетная обработка:".ljust(50) + "│")
        print(f"│ Оригинал:  {batch_test}".ljust(50) + "│")
        print(f"│ Исправлено: {await speller.correct_batch(batch_test)}".ljust(50) + "│")
        print("└" + "─" * 50 + "┘")

if __name__ == "__main__":
    asyncio.run(test_speller())