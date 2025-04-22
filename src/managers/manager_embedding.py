"""
    ╔════════════════════════════════════════════════════════════╗
    ║                    Модуль manager_embedding.py             ║
    ╚════════════════════════════════════════════════════════════╝

    Описание:
        Модуль реализует систему управления векторными представлениями (эмбеддингами)
        текстовых данных с использованием модели SBERT и библиотеки FAISS.
        Обеспечивает генерацию, сохранение, загрузку и поиск эмбеддингов.

    Основные компоненты:
        - EmbeddingManager: Синглтон-класс для управления эмбеддингами
        - SentenceTransformer: Модель для генерации эмбеддингов
        - FAISS: Библиотека для эффективного поиска ближайших соседей
        - TextPreprocessor: Класс для предобработки текста

    Функциональность:
        - Генерация эмбеддингов для текстовых данных
        - Сохранение и загрузка эмбеддингов
        - Поиск похожих текстов
        - Предобработка текста перед генерацией
        - Нормализация векторов
"""

import hashlib
import numpy as np
import faiss
from pathlib import Path
from sentence_transformers import SentenceTransformer


import os
import sys
from pathlib import Path

# Добавляем корневую директорию проекта в PYTHONPATH
root_dir = str(Path(__file__).parent.parent.parent)
if root_dir not in sys.path:
    sys.path.append(root_dir)
    
from src.utils import preprocessor



class EmbeddingManager:
    """
        Синглтон-класс для работы с эмбеддингами: генерация, сохранение, загрузка и поиск
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(EmbeddingManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, data_manager, base_path="data/embeddings"):
        if hasattr(self, "_initialized") and self._initialized:
            return  # предотвращаем повторную инициализацию при повторном вызове

        self.base_path = base_path
        self.model = SentenceTransformer("sberbank-ai/sbert_large_nlu_ru")
        self.preproc = preprocessor

        # Генерация эмбеддингов для всех таблиц и колонок
        for table in data_manager.get_all_table_names():
            df = data_manager.get_table_data(table)
            for col in ["Наименование", "Артикул", "Описание"]:
                self.generate_and_save(table, col, df[col].astype(str))

        self._initialized = True  # флаг, чтобы инициализация прошла только один раз

    def get_embedding_path(self, table, column):
        h = hashlib.md5(f"{table}_{column}".encode()).hexdigest()
        return os.path.join(self.base_path, f"{h}.npy")

    def generate_and_save(self, table, column, texts):
        path = self.get_embedding_path(table, column)
        if os.path.exists(path):
            return
        print(f"[⏳] Генерация эмбеддингов для {table}.{column}")
        prep_texts = [self.preproc.preprocess(t, column == "Артикул") for t in texts]
        emb = self.model.encode(prep_texts, show_progress_bar=True)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        np.save(path, emb)
        print(f"[✓] Эмбеддинги сохранены: {path}")

    def load_embeddings(self, table, column):
        path = self.get_embedding_path(table, column)
        emb = np.load(path)
        emb /= np.linalg.norm(emb, axis=1, keepdims=True)
        return emb

    def search(self, table, column, query, top_k=5):
        try:
            emb = self.load_embeddings(table, column)
            index = faiss.IndexFlatIP(emb.shape[1])
            index.add(emb)
            query_embedding = self.model.encode([query])[0]
            distances, indices = index.search(np.array([query_embedding]), top_k)
            return distances[0], indices[0]
        except Exception as e:
            print(f"[❌] Ошибка при работе с эмбеддингами: {e}")
            return None, None
