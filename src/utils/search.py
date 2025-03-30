import os
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
import hashlib

class VectorSearchManager:
    def __init__(self, data_manager, table_name, text_column, base_dir="data/indexes"):
        """
        Инициализация менеджера поиска по векторным эмбеддингам.

        Аргументы:
        - data_manager (DataManager): Экземпляр класса DataManager для работы с данными.
        - table_name (str): Имя таблицы для загрузки данных.
        - text_column (str): Столбец с текстовыми данными, по которому будет осуществляться поиск.
        - base_dir (str, optional): Базовая директория для сохранения файлов индексов и эмбеддингов.
        """
        self.data_manager = data_manager
        self.table_name = table_name
        self.text_column = text_column
        self.base_dir = base_dir

        # Создание уникальных путей для файлов
        self.index_path, self.embeddings_path = self._generate_paths()

        # Загружаем данные из базы
        self.df = self.data_manager.get_table_data(table_name)

        # Инициализация модели эмбеддингов
        self.model = SentenceTransformer("distiluse-base-multilingual-cased-v2")

        # Флаги загрузки
        index_loaded = False
        embeddings_loaded = False

        # Загрузка сохранённых эмбеддингов (если файл существует)
        if os.path.exists(self.embeddings_path):
            try:
                self.embeddings = np.load(self.embeddings_path)
                embeddings_loaded = True
                print(f"Загружены эмбеддинги из {self.embeddings_path}")
            except Exception as e:
                print(f"Ошибка при загрузке эмбеддингов: {e}")

        # Вычисление эмбеддингов, если файл отсутствует
        if not embeddings_loaded:
            texts = self.df[self.text_column].tolist()
            print("Вычисление эмбеддингов...")
            self.embeddings = self.model.encode(texts, show_progress_bar=True)
            self.embeddings = np.array(self.embeddings, dtype=np.float32)
            np.save(self.embeddings_path, self.embeddings)
            print(f"Эмбеддинги сохранены в {self.embeddings_path}")

        # Загрузка индекса (если файл существует)
        if os.path.exists(self.index_path):
            try:
                self.index = faiss.read_index(self.index_path)
                index_loaded = True
                print(f"Загружен индекс из {self.index_path}")
            except Exception as e:
                print(f"Ошибка при загрузке индекса: {e}")

        # Создание индекса, если файл отсутствует или загрузка не удалась
        if not index_loaded:
            self.dimension = self.embeddings.shape[1]
            self.index = faiss.IndexFlatL2(self.dimension)
            self.index.add(self.embeddings)
            faiss.write_index(self.index, self.index_path)
            print(f"Индекс создан и сохранён в {self.index_path}")

    def _normalize_filename(self, name):
        """
        Генерирует хэш md5 для переданной строки.
        """
        encoded_name = name.encode("utf-8")
        return hashlib.md5(encoded_name).hexdigest()

    def _generate_paths(self):
        """
        Генерирует пути для файлов эмбеддингов и индекса, используя только хэш от (table_name + text_column).
        """
        os.makedirs(self.base_dir, exist_ok=True)
        filename_hash = self._normalize_filename(f"{self.table_name}_{self.text_column}")
        index_path = os.path.join(self.base_dir, f"{filename_hash}_index.faiss")
        embeddings_path = os.path.join(self.base_dir, f"{filename_hash}_embeddings.npy")
        return index_path, embeddings_path

    def search(self, query, top_k=5):
        """
        Выполняет поиск по запросу и возвращает top_k наиболее релевантных записей.

        Аргументы:
        - query (str): Текстовый запрос для поиска.
        - top_k (int): Количество наиболее релевантных записей для возврата.

        Возвращает:
        - results (DataFrame): Найденные записи из таблицы.
        - distances (ndarray): Расстояния для найденных записей.
        """
        query_embedding = self.model.encode([query])
        query_embedding = np.array(query_embedding, dtype=np.float32)

        distances, indices = self.index.search(query_embedding, top_k)
        results = self.df.iloc[indices[0]]
        return results, distances[0]
