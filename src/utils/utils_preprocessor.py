"""
    ╔════════════════════════════════════════════╗
    ║           preprocessor.py                  ║
    ╚════════════════════════════════════════════╝
    
    Описание:
        Модуль предоставляет функционал для предобработки текстовых данных:
        • Очистка текста от специальных символов
        • Токенизация
        • Удаление стоп-слов
        • Фильтрация пунктуации
        • Лематизация (приведение к нормальной форме)
        • Асинхронная обработка текстов
    
    Примеры использования:
        1. Базовая предобработка:
            preprocessor   = TextPreprocessor()
            processed_text = await preprocessor.preprocess("Привет, как дела?")
        
        2. Предобработка с сохранением пунктуации:
            preprocessor   = TextPreprocessor(keep_punctuation=True)
            processed_text = await preprocessor.preprocess("Привет, как дела?")
        
        3. Предобработка с лематизацией:
            preprocessor   = TextPreprocessor(use_lemmatization=True)
            processed_text = await preprocessor.preprocess("Машины едут по дороге")
"""

import re
import pymorphy3
import asyncio

from string         import punctuation
from typing         import List, Union
from nltk.tokenize  import word_tokenize
from nltk.corpus    import stopwords


SUPPORTED_LANGUAGES = {
    'russian': 'russian',
    'english': 'english'
}


WHITESPACE_PATTERN   = re.compile(r'\s+')
UNICODE_WORD_PATTERN = re.compile(r'[\w\u0400-\u04FF]+', re.UNICODE)


class TextPreprocessor:
    """
        Класс для предобработки текстов
    """
    
    def __init__(
        self, 
        language:          str  = 'russian', 
        keep_punctuation:  bool = False,
        use_lemmatization: bool = False
    ):
        """
            Инициализация препроцессора текста
        """
        if language not in SUPPORTED_LANGUAGES:
            raise ValueError(
                f"Неподдерживаемый язык: {language}. "
                f"Поддерживаемые: {', '.join(SUPPORTED_LANGUAGES)}"
            )
            
        self.language          = language
        self.stop_words        = set(stopwords.words(language))
        self.punctuation       = set(punctuation)
        self.keep_punctuation  = keep_punctuation
        self.use_lemmatization = use_lemmatization
        
        if use_lemmatization and language == 'russian':
            try:
                self.morph = pymorphy3.MorphAnalyzer()
            except Exception as e:
                print(f"Ошибка инициализации pymorphy3: {e}")
                self.morph = None
                self.use_lemmatization = False
        else:
            self.morph = None
        
        if keep_punctuation:
            punctuation_chars    = re.escape(''.join(self.punctuation))
            self.cleanup_pattern = re.compile(
                f'[^\\w\\s{punctuation_chars}]', 
                flags=re.UNICODE
            )
        else:
            self.cleanup_pattern = re.compile(
                r'[^\w\s]', 
                flags=re.UNICODE
            )
    
    async def clean_text(self, text: str) -> str:
        """
            Очистка текста от нежелательных символов
        """
        if not isinstance(text, str):
            text = str(text)
            
        text    = text.lower().strip()
        cleaned = self.cleanup_pattern.sub(' ', text)

        return WHITESPACE_PATTERN.sub(' ', cleaned).strip()
    
    async def tokenize(self, text: str) -> List[str]:
        """
            Токенизация текста
        """
        return word_tokenize(text, language=self.language)
    
    async def remove_stopwords(self, tokens: List[str]) -> List[str]:
        """ 
            Удаление стоп-слов из списка токенов
        """
        return [word for word in tokens if word not in self.stop_words]
    
    async def filter_punctuation(self, tokens: List[str]) -> List[str]:
        """
            Фильтрация пунктуационных токенов
        """
        return [token for token in tokens if token not in self.punctuation]
    
    async def lemmatize(self, tokens: List[str]) -> List[str]:
        """
            Лематизация токенов (приведение к нормальной форме)
        """
        if not self.use_lemmatization or not self.morph:
            return tokens
            
        lemmatized = []
        for token in tokens:
            if token in self.punctuation or token in self.stop_words:
                lemmatized.append(token)
                continue
            try:
                parsed = self.morph.parse(token)[0]
                lemmatized.append(parsed.normal_form)
            except Exception as e:
                print(f"Ошибка лематизации для токена '{token}': {e}")
                lemmatized.append(token)
                
        return lemmatized
    
    async def _process_single(self, text: Union[str, List[str]], **kwargs) -> str:
        """
            Обработка одного текста
        """
        if isinstance(text, list):
            tokens = text
        else:
            cleaned = await self.clean_text(text)
            tokens  = await self.tokenize(cleaned)
        
        if kwargs.get('remove_stopwords', True):
            tokens = await self.remove_stopwords(tokens)
        
        if kwargs.get('filter_punctuation', True):
            tokens = await self.filter_punctuation(tokens)
            
        if self.use_lemmatization:
            tokens = await self.lemmatize(tokens)
        
        return ' '.join(tokens)
    
    async def preprocess(
        self, 
        text: Union[str, List[str]], 
        remove_stopwords:   bool = True,
        filter_punctuation: bool = True
    ) -> str:
        """
            Полная предобработка текста
        """
        return await self._process_single(
            text,
            remove_stopwords   = remove_stopwords,
            filter_punctuation = filter_punctuation
        )


# Создаем глобальный препроцессор по умолчанию
preprocessor = TextPreprocessor(use_lemmatization=True)