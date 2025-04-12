import os
import re
import hashlib
import numpy as np
import pandas as pd
import faiss
import spacy
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from string import punctuation
from sentence_transformers import SentenceTransformer
from thefuzz import fuzz
from src.managers import DataManager

# Инициализация моделей
nlp = spacy.load("ru_core_news_sm")
dm = DataManager.initialize("price-list.xlsx")


class TextPreprocessor:
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


def filter_article(query: str) -> str:
    matches = re.findall(r'\b([A-Za-zА-Яа-я0-9\-]{5,})\b', query)
    return max(matches, key=len) if matches else ""


def extract_entities(query: str):
    doc = nlp(query)
    return {ent.label_: ent.text for ent in doc.ents}


def classify_intent(query: str):
    query = query.lower()
    keywords = {
        "search_article": ["артикул", "арт.", "код товара", "номер"],
        "search_name": ["наименование", "название", "что за товар"],
        "search_description": ["описание", "характеристики", "подробности", "состав"]
    }
    for intent, words in keywords.items():
        if any(word in query for word in words):
            return intent
    return "search_unknown"


def get_embedding_path(table_name, column_name):
    hash_name = hashlib.md5(f"{table_name}_{column_name}".encode()).hexdigest()
    return os.path.join("data", "embeddings", f"{hash_name}.npy")


def detect_target_column(query: str, table_name: str, dm: DataManager) -> str:
    article = filter_article(query)
    if article:
        return "Артикул"

    if any(word in query.lower() for word in ("описание", "характеристики")):
        return "Описание"

    return "Наименование"


def search_in_single_column(query, table_name, column, model, preprocessor, top_k=5):
    print(f"[🔎] Поиск в колонке '{column}' по запросу: '{query}'")
    df = dm.get_table_data(table_name).copy()

    # Нормализация данных
    df['clean_article'] = df['Артикул'].astype(str).str.strip().str.lower()

    # Точный поиск для артикулов
    if column == "Артикул":
        article = filter_article(query)
        if article:
            print(f"[🔍] Проверка артикулов: {df['Артикул'].head(3).tolist()}")

            # Точное совпадение
            exact_match = df[df['clean_article'] == article.lower()]
            if not exact_match.empty:
                print(f"[✓] Найдено точное совпадение артикула")
                exact_match['similarity'] = 1.0
                return exact_match.head(top_k)

            # Частичное совпадение
            partial_match = df[df['clean_article'].str.contains(article.lower())]
            if not partial_match.empty:
                print(f"[⚠] Найдены частичные совпадения артикулов")
                partial_match['similarity'] = 0.9
                return partial_match.head(top_k)

    # Семантический поиск
    cleaned = preprocessor.preprocess(query, is_article=(column == "Артикул"))
    q_emb = model.encode([cleaned])[0]
    q_emb /= np.linalg.norm(q_emb)

    try:
        emb_path = get_embedding_path(table_name, column)
        col_emb = np.load(emb_path)
        col_emb /= np.linalg.norm(col_emb, axis=1, keepdims=True)

        index = faiss.IndexFlatIP(col_emb.shape[1])
        index.add(col_emb)
        distances, indices = index.search(np.array([q_emb]), top_k)

        res = df.iloc[indices[0]].copy()
        res["similarity"] = distances[0]
        res["search_column"] = column
        return res

    except Exception as e:
        print(f"[❌] Ошибка при загрузке эмбеддингов: {str(e)}")
        return pd.DataFrame()


def search_smart(query, table_name, model, preprocessor, top_k=5):
    # Поиск по артикулу
    article = filter_article(query)
    if article:
        print(f"[🔎] Поиск по артикулу: {article}")
        df = dm.get_table_data(table_name).copy()
        df['clean_article'] = df['Артикул'].astype(str).str.strip().str.lower()

        # Точное совпадение
        exact_match = df[df['clean_article'] == article.lower()].copy()
        if not exact_match.empty:
            print(f"[✓] Точное совпадение артикула: {article}")
            exact_match['similarity'] = 1.0
            exact_match['search_column'] = 'Артикул'
            return exact_match.head(top_k)

        # Нечеткий поиск
        print(f"[⚠] Точного совпадения нет, поиск похожих артикулов")
        fuzzy_df = df.copy()
        fuzzy_df['fuzzy_score'] = fuzzy_df['clean_article'].apply(
            lambda x: fuzz.ratio(x, article.lower())
        )
        fuzzy_results = fuzzy_df[fuzzy_df['fuzzy_score'] > 70].sort_values(
            'fuzzy_score', ascending=False
        ).head(top_k)

        if not fuzzy_results.empty:
            fuzzy_results = fuzzy_results.copy()
            fuzzy_results['similarity'] = fuzzy_results['fuzzy_score'] / 100
            return fuzzy_results

    # Поиск по намерению
    intent = classify_intent(query)
    print(f"[ℹ] Определено намерение: {intent}")

    if intent == "search_article":
        return search_in_single_column(query, table_name, "Артикул", model, preprocessor, top_k)
    elif intent == "search_description":
        return search_in_single_column(query, table_name, "Описание", model, preprocessor, top_k)

    # Расширенный поиск
    results = []
    for column in ["Наименование", "Описание", "Артикул"]:
        try:
            res = search_in_single_column(query, table_name, column, model, preprocessor, top_k)
            results.append(res)
        except Exception as e:
            print(f"[⚠] Ошибка поиска в колонке {column}: {str(e)}")

    final_results = pd.concat(results).sort_values(
        "similarity",
        ascending=False
    ).drop_duplicates(subset='Артикул').head(top_k)

    return final_results

    # Поиск по намерению
    intent = classify_intent(query)
    print(f"[ℹ] Определено намерение: {intent}")

    if intent == "search_article":
        return search_in_single_column(query, table_name, "Артикул", model, preprocessor, top_k)
    elif intent == "search_description":
        return search_in_single_column(query, table_name, "Описание", model, preprocessor, top_k)

    # Расширенный поиск
    results = []
    for column in ["Наименование", "Описание", "Артикул"]:
        try:
            res = search_in_single_column(query, table_name, column, model, preprocessor, top_k)
            results.append(res)
        except Exception as e:
            print(f"[⚠] Ошибка поиска в колонке {column}: {str(e)}")

    final_results = pd.concat(results).sort_values(
        "similarity",
        ascending=False
    ).drop_duplicates(subset='Артикул').head(top_k)

    return final_results


def main():
    preprocessor = TextPreprocessor(language="russian")
    model = SentenceTransformer("sberbank-ai/sbert_large_nlu_ru")

    # Генерация эмбеддингов
    for table in dm.get_all_table_names():
        df = dm.get_table_data(table)
        for column in ["Наименование", "Артикул", "Описание"]:
            emb_path = get_embedding_path(table, column)
            if os.path.exists(emb_path):
                continue

            print(f"[⏳] Генерация эмбеддингов для {table}.{column}...")
            texts = df[column].astype(str)

            if column == "Артикул":
                pre_texts = [preprocessor.preprocess(t, is_article=True) for t in texts]
            else:
                pre_texts = [preprocessor.preprocess(t) for t in texts]

            embeddings = model.encode(pre_texts, show_progress_bar=True)
            os.makedirs(os.path.dirname(emb_path), exist_ok=True)
            np.save(emb_path, embeddings)
            print(f"[✓] Эмбеддинги сохранены: {table}.{column}")

    # Интерфейс поиска
    print("\n=== Выбор таблицы ===")
    tables = dm.get_all_table_names()
    for i, name in enumerate(tables, 1):
        print(f"{i}. {name}")

    table_idx = int(input("\nВыберите номер таблицы: ")) - 1
    selected_table = tables[table_idx]
    query = input("Введите поисковый запрос: ")

    results = search_smart(query, selected_table, model, preprocessor)

    print("\n🔍 Результаты поиска:")
    if not results.empty:
        # Список обязательных колонок
        required_columns = ['Артикул', 'Наименование', 'Описание', 'similarity', 'search_column']

        # Добавляем недостающие колонки
        for col in required_columns:
            if col not in results.columns:
                results[col] = None

        # Выводим только нужные колонки
        print(results[required_columns])
    else:
        print("По вашему запросу ничего не найдено")


if __name__ == "__main__":
    main()