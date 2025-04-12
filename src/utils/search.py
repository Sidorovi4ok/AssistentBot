import numpy as np
import pandas as pd
pd.options.mode.chained_assignment = None

from sentence_transformers import SentenceTransformer
from thefuzz import fuzz

from src.utils.preprocessor import TextPreprocessor

class SearchService:
    """Сервис для семантического и 'умного' поиска по таблицам."""
    def __init__(self, data_manager, rasa_client):
        self.dm = data_manager
        self.rasa_client = rasa_client
        self.model = SentenceTransformer("sberbank-ai/sbert_large_nlu_ru")
        self.preproc = TextPreprocessor()

        def __init__(self, base_path="data/embeddings"):
            self.base_path = base_path

    def search_in_single_column(self, query, table, column, emb_manager, top_k=5):
        print(f"[🔎] Поиск в '{column}' по: '{query}'")
        df = self.dm.get_table_data(table).copy()
        df['clean_article'] = df['Артикул'].astype(str).str.lower().str.strip()

        # Если ищем по артикулам – пытаемся извлечь сущности от Rasa
        if column == "Артикул":
            entities = self.rasa_client.extract_entities(query)
            article = entities.get("artikul")
            if article:
                match = df[df['clean_article'] == article.lower()]
                if not match.empty:
                    match['similarity'] = 1.0
                    match['search_column'] = 'Артикул'
                    return match.head(top_k)
                partial = df[df['clean_article'].str.contains(article.lower())]
                if not partial.empty:
                    partial['similarity'] = 0.9
                    partial['search_column'] = 'Артикул'
                    return partial.head(top_k)

        # Семантический поиск: предобработка, получение эмбеддингов и поиск через Faiss
        cleaned = self.preproc.preprocess(query, column == "Артикул")
        q_emb = self.model.encode([cleaned])[0]
        q_emb /= np.linalg.norm(q_emb)
        distances, indices = emb_manager.search(table, column, q_emb, top_k)
        if distances is None:
            return pd.DataFrame()
        res = df.iloc[indices].copy()
        res["similarity"], res["search_column"] = distances, column
        return res

    def search_smart(self, query, table, emb_manager, top_k=5):
        res = self.rasa_client.query(query) or {}
        entities, intent = res.get("entities", {}), res.get("intent", "unknown")
        df = self.dm.get_table_data(table).copy()
        df['clean_article'] = df['Артикул'].astype(str).str.lower().str.strip()

        # Если есть сущность artikul, пытаемся точное и нечеткое совпадения
        if "artikul" in entities:
            article = entities["artikul"]
            match = df[df['clean_article'] == article.lower()]
            if not match.empty:
                match['similarity'] = 1.0
                match['search_column'] = 'Артикул'
                return match.head(top_k)
            df['fuzzy_score'] = df['clean_article'].apply(lambda x: fuzz.ratio(x, article.lower()))
            fuzzy = df[df['fuzzy_score'] > 70].sort_values('fuzzy_score', ascending=False).head(top_k)
            if not fuzzy.empty:
                fuzzy['similarity'] = fuzzy['fuzzy_score'] / 100
                fuzzy['search_column'] = 'Артикул'
                return fuzzy

        # Если сущность naimenovanie есть, запускаем поиск по колонке "Наименование"
        if "naimenovanie" in entities:
            return self.search_in_single_column(entities["naimenovanie"], table, "Наименование", emb_manager, top_k)

        # Если определено намерение – выбираем колонку в зависимости от типа поиска
        if intent in ["search_by_artikul", "search_by_naimenovanie"]:
            column = "Артикул" if intent == "search_by_artikul" else "Наименование"
            return self.search_in_single_column(query, table, column, emb_manager, top_k)

        print("[⚠] Fallback: семантический поиск по всем колонкам")
        results = []
        for col in ["Наименование", "Описание", "Артикул"]:
            try:
                results.append(self.search_in_single_column(query, table, col, emb_manager, top_k))
            except Exception as e:
                print(f"[⚠] Ошибка в колонке {col}: {e}")
        if results:
            return pd.concat(results).sort_values("similarity", ascending=False).drop_duplicates("Артикул").head(top_k)
        return pd.DataFrame()
