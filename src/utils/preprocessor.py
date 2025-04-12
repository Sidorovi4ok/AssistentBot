from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from string import punctuation


class TextPreprocessor:
    """Класс для предобработки текстов"""

    def __init__(self, language='russian'):
        self.language = language
        self.stop_words = set(stopwords.words(language))
        self.punctuation = set(punctuation)

    def clean_text(self, text, is_article=False):
        if is_article:
            return text.strip().lower()
        return ''.join([ch if ch.isalnum() or ch.isspace() else ' ' for ch in text.lower()])

    def tokenize(self, text):
        return word_tokenize(text.lower())

    def remove_stopwords(self, tokens):
        return [word for word in tokens if word not in self.stop_words]

    def filter_punctuation(self, tokens):
        return [token for token in tokens if token not in self.punctuation]

    def preprocess(self, text, is_article=False):
        if not isinstance(text, str):
            text = str(text)
        if is_article:
            return text.strip().lower()
        cleaned = self.clean_text(text)
        tokens = self.tokenize(cleaned)
        tokens = self.remove_stopwords(tokens)
        tokens = self.filter_punctuation(tokens)
        return " ".join(tokens) 