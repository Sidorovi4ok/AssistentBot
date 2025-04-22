"""
    ╔════════════════════════════════════════════════════════════╗
    ║                    Модуль manager_price.py                  ║
    ╚════════════════════════════════════════════════════════════╝

    Описание:
        Модуль реализует систему управления данными о ценах и товарах,
        обеспечивая синхронизацию между Excel-файлами и SQLite базой данных.
        Использует паттерн Singleton для обеспечения единой точки доступа к данным.

    Основные компоненты:
        - DataManager: Синглтон-класс для управления данными
        - База данных SQLite: Хранение структурированных данных
        - Excel файлы: Источник данных для импорта

    Функциональность:
        - Импорт данных из Excel в базу данных
        - Получение данных из таблиц БД
        - Управление структурой данных
        - Синхронизация данных между источниками
"""

# Стандартные библиотеки
import os

# Библиотеки для работы с данными и базой данных
import pandas as pd
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.declarative import declarative_base

# Создание базового класса для моделей SQLAlchemy
Base = declarative_base()

class DataManager:
    """
    Класс для работы с данными из базы данных SQLite и файла Excel.

    Он реализует паттерн Singleton, обеспечивая, что экземпляр класса существует только один раз.

    Атрибуты:
    - _instance (DataManager): Экземпляр класса (для паттерна Singleton).
    - _initialized (bool): Флаг инициализации экземпляра.
    """
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        """
        Паттерн Singleton: возвращает единственный экземпляр класса.
        """
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, filename, update_db=False):
        """
        Инициализирует экземпляр DataManager.

        Аргументы:
        filename (str): Имя файла Excel для загрузки данных.
        update_db (bool): Если True, выполняет обновление базы данных из Excel.
        """
        if not self._initialized:
            # Путь к файлу Excel
            self.filepath = os.path.join(filename)

            # Создание соединения с базой данных SQLite
            self.engine = create_engine(f'sqlite:///{os.path.join("data", "db", "database.db")}')
            self.Session = sessionmaker(bind=self.engine)

            if not os.path.exists(self.filepath):
                raise FileNotFoundError(f"Excel file not found: {self.filepath}")

            if update_db:
                self.update_database()

            self._initialized = True

    def get_sheet_names(self):
        """
        Возвращает список названий листов Excel.

        Возвращает:
        list: Список имен листов Excel.
        """
        return pd.ExcelFile(self.filepath).sheet_names

    def get_table_data(self, table_name):
        """
        Возвращает данные из указанной таблицы в виде DataFrame.

        Аргументы:
        table_name (str): Название таблицы для извлечения данных.

        Возвращает:
        pd.DataFrame: Данные из указанной таблицы.
        """
        with self.engine.connect() as conn:
            return pd.read_sql_table(table_name, conn)

    def update_database(self):
        """
        Обновляет базу данных из Excel файла.

        Читает данные с каждого листа Excel и добавляет их в базу данных.
        """
        excel_file = pd.ExcelFile(self.filepath)

        with self.engine.begin() as connection:
            for sheet_name in excel_file.sheet_names:
                df = excel_file.parse(sheet_name=sheet_name)

                target_column = 'Артикул'  # Столбец, по которому будет осуществляться фильтрация

                if target_column in df.columns:
                    df = df.dropna(subset=[target_column])  # Удаляем строки с пропусками в целевом столбце
                else:
                    print(f"Внимание: в листе '{sheet_name}' отсутствует столбец '{target_column}'")

                # Загружаем данные в таблицу базы данных
                df.to_sql(name=sheet_name, con=connection, if_exists='replace', index=False)

            # Выполняем операции COMMIT и VACUUM для оптимизации базы данных
            connection.execute(text("COMMIT"))
            connection.execute(text("VACUUM"))

    def get_all_table_names(self):
        """
        Возвращает список всех таблиц в базе данных.

        Возвращает:
        list: Список имен всех таблиц в базе данных.
        """
        inspector = inspect(self.engine)
        return inspector.get_table_names()

    @classmethod
    def initialize(cls, filename, update_db=False):
        """
        Инициализация экземпляра DataManager.

        Этот метод будет вызываться для создания экземпляра DataManager с подтверждением необходимости обновления БД.

        Аргументы:
        filename (str): Имя файла Excel для инициализации.
        update_db (bool): Если True, выполняется обновление БД.

        Возвращает:
        DataManager: Экземпляр DataManager.
        """
        if not cls._instance:
            confirm = input("Update database from Excel? (y/n) default=n: ").lower().strip()
            # Если ничего не введено, устанавливаем значение по умолчанию 'n'
            if confirm == '':
                confirm = 'n'
            update = confirm == 'y'
            cls._instance = cls(filename, update)
        return cls._instance
