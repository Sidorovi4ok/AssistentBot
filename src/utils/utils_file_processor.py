import os
import sys
from pathlib import Path
from openpyxl import load_workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import asyncio
import aiofiles
from typing import Optional, List, Tuple, Callable, Awaitable, Dict
from thefuzz import fuzz
import re
from functools import lru_cache
from src.utils.utils_preprocessor import TextPreprocessor

# Добавляем корневую директорию проекта в PYTHONPATH
root_dir = str(Path(__file__).parent.parent.parent)
if root_dir not in sys.path:
    sys.path.append(root_dir)

import pandas as pd
from typing import Optional, List, Tuple
import logging
from src.managers import EmbeddingManager
from src.managers import DataManager

class AsyncCache:
    """Простой кэш для асинхронных функций."""
    def __init__(self, maxsize: int = 1000):
        self.cache: Dict[str, any] = {}
        self.maxsize = maxsize

    def get_key(self, *args, **kwargs) -> str:
        """Создает ключ из аргументов."""
        return f"{args}:{kwargs}"

    async def get_or_create(self, key: str, create_func: Callable) -> any:
        """Получает значение из кэша или создает новое."""
        if key not in self.cache:
            if len(self.cache) >= self.maxsize:
                # Удаляем первый элемент если кэш переполнен
                self.cache.pop(next(iter(self.cache)))
            self.cache[key] = await create_func()
        return self.cache[key]

class ExcelProcessor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.required_columns = {
            'name': ['наименование', 'название', 'имя', 'name', 'title'],
            'quantity': ['количество', 'кол-во', 'quantity', 'count']
        }
        self.data_manager = DataManager("data/excel/price-list.xlsx")
        self.embedding_manager = EmbeddingManager(self.data_manager)
        self._progress_callback: Optional[Callable[[float], Awaitable[None]]] = None
        
        # Инициализируем препроцессор текста
        self.text_preprocessor = TextPreprocessor(
            language='russian',
            keep_punctuation=False,
            use_lemmatization=True
        )
        
        # Инициализируем кэши
        self.text_cache = AsyncCache(maxsize=1000)
        self.similarity_cache = AsyncCache(maxsize=1000)
        
        # Ключевые слова для определения типа продукта
        self.product_types = {
            'лаборатория': ['цифровая лаборатория', 'лабораторное оборудование'],
            'комплект': ['комплект', 'набор', 'сет'],
            'пособие': ['пособие', 'материалы', 'комплекс', 'плакаты', 'наглядные']
        }

    def set_progress_callback(self, callback: Callable[[float], Awaitable[None]]):
        """Установка callback-функции для отслеживания прогресса"""
        self._progress_callback = callback

    async def _update_progress(self, progress: float):
        """Обновление прогресса через callback"""
        if self._progress_callback:
            await self._progress_callback(progress)

    def _find_column(self, df: pd.DataFrame, possible_names: List[str]) -> Optional[str]:
        """Find column name in DataFrame that matches any of the possible names."""
        for col in df.columns:
            if any(name.lower() in col.lower() for name in possible_names):
                return col
        return None

    async def preprocess_text(self, text: str) -> str:
        """Предварительная обработка текста с использованием TextPreprocessor и кэшированием."""
        async def _process():
            try:
                return await self.text_preprocessor.preprocess(
                    text,
                    remove_stopwords=False,
                    filter_punctuation=True
                )
            except Exception as e:
                self.logger.error(f"Ошибка при предобработке текста: {e}")
                return ' '.join(text.lower().split())

        return await self.text_cache.get_or_create(text, _process)

    def get_product_type(self, text: str) -> str:
        """Определение типа продукта из текста."""
        text = text.lower()
        for type_name, keywords in self.product_types.items():
            if any(keyword in text for keyword in keywords):
                return type_name
        return "other"

    async def calculate_similarity(self, text1: str, text2: str) -> float:
        """Вычисление сходства между двумя текстами с кэшированием."""
        cache_key = self.similarity_cache.get_key(text1, text2)
        
        async def _calculate():
            try:
                # Предварительная обработка обоих текстов
                processed_text1 = await self.preprocess_text(text1)
                processed_text2 = await self.preprocess_text(text2)

                # Базовые метрики на обработанных текстах
                ratio = fuzz.ratio(processed_text1, processed_text2) / 100
                partial_ratio = fuzz.partial_ratio(processed_text1, processed_text2) / 100
                token_sort_ratio = fuzz.token_sort_ratio(processed_text1, processed_text2) / 100
                token_set_ratio = fuzz.token_set_ratio(processed_text1, processed_text2) / 100

                # Определяем тип продукта
                type1 = self.get_product_type(text1)
                type2 = self.get_product_type(text2)

                # Если типы продуктов совпадают, увеличиваем вес
                type_multiplier = 1.2 if type1 == type2 and type1 != "other" else 1.0

                # Взвешенная комбинация метрик
                base_similarity = max(
                    ratio * 0.2 + token_sort_ratio * 0.4 + token_set_ratio * 0.4,
                    partial_ratio * 0.3 + token_sort_ratio * 0.7
                )

                return base_similarity * type_multiplier
            except Exception as e:
                self.logger.error(f"Ошибка при расчете сходства: {e}")
                return fuzz.ratio(text1.lower(), text2.lower()) / 100

        return await self.similarity_cache.get_or_create(cache_key, _calculate)

    async def _search_product_async(self, product_name: str) -> List[Tuple[str, str, float, float, str]]:
        """
        Асинхронный поиск товара во всех таблицах базы данных.
        Returns: List[(найденный_товар, таблица, цена, сходство, описание)]
        """
        results = []
        tables = self.data_manager.get_all_table_names()
        
        # Создаем список задач для асинхронного выполнения
        tasks = []
        for table in tables:
            tasks.append(self._search_in_table_async(table, product_name))
        
        # Запускаем все задачи параллельно
        table_results = await asyncio.gather(*tasks)
        
        # Объединяем результаты
        for table_result in table_results:
            results.extend(table_result)
        
        # Сортировка по сходству (в порядке убывания)
        return sorted(results, key=lambda x: x[3], reverse=True)

    async def _search_in_table_async(self, table: str, product_name: str) -> List[Tuple[str, str, float, float, str]]:
        """Асинхронный поиск товара в конкретной таблице."""
        results = []
        df = await asyncio.to_thread(self.data_manager.get_table_data, table)
        
        # Предварительная обработка искомого продукта
        processed_product_name = await self.preprocess_text(product_name)
        product_type = self.get_product_type(product_name)
        
        # Создаем временный столбец с обработанными названиями
        processed_names = {}
        for idx, row in df.iterrows():
            name = row['Наименование']
            processed_names[idx] = await self.preprocess_text(name)
        
        # Сначала ищем точное совпадение (после предобработки)
        exact_matches = []
        for idx, proc_name in processed_names.items():
            if proc_name == processed_product_name:
                exact_matches.append(idx)
                
        if exact_matches:
            for idx in exact_matches:
                product = df.iloc[idx]
                price = float(product.get('Цена с НДС', 0))
                description = str(product.get('Описание', ''))
                results.append((product['Наименование'], table, price, 1.0, description))
            return results

        # Если точного совпадения нет, используем эмбеддинги и расширенный поиск
        distances, indices = await asyncio.to_thread(
            self.embedding_manager.search, table, "Наименование", product_name
        )

        if distances is not None and indices is not None:
            for dist, idx in zip(distances, indices):
                if idx < len(df):
                    product = df.iloc[idx]
                    found_name = product['Наименование']
                    
                    # Вычисляем сходство с учетом всех метрик
                    fuzzy_similarity = await self.calculate_similarity(product_name, found_name)
                    
                    # Комбинируем эмбеддинг и fuzzy метрики с учетом обработанного текста
                    if dist > 0.9:
                        final_similarity = max(dist, fuzzy_similarity)
                    else:
                        # Для менее похожих результатов используем взвешенную комбинацию
                        # с большим весом для fuzzy_similarity, так как она учитывает лемматизацию
                        final_similarity = (dist * 0.3 + fuzzy_similarity * 0.7)

                    # Логируем результаты для отладки
                    self.logger.debug(f"""
                    Поиск для: {product_name} (тип: {product_type})
                    Обработанный запрос: {processed_product_name}
                    Найдено: {found_name}
                    Обработанная находка: {processed_names.get(idx, '')}
                    Эмбеддинг сходство: {dist:.3f}
                    Fuzzy similarity: {fuzzy_similarity:.3f}
                    Итоговое сходство: {final_similarity:.3f}
                    """)

                    price = float(product.get('Цена с НДС', 0))
                    description = str(product.get('Описание', ''))
                    results.append((found_name, table, price, float(final_similarity), description))

        # Сортируем результаты по убыванию сходства
        results.sort(key=lambda x: x[3], reverse=True)
        
        # Фильтруем результаты с низким сходством
        filtered_results = [r for r in results if r[3] >= 0.5]
        
        # Если есть результаты с высоким сходством, оставляем только их
        high_similarity_results = [r for r in filtered_results if r[3] >= 0.8]
        if high_similarity_results:
            filtered_results = high_similarity_results[:3]  # Оставляем только топ-3 результата
        else:
            filtered_results = filtered_results[:5]  # Оставляем только топ-5 результатов

        self.logger.debug(f"Отфильтрованные результаты: {filtered_results}")
        
        return filtered_results

    async def validate_file_async(self, file_path: str) -> tuple[bool, str, Optional[pd.DataFrame]]:
        """
        Асинхронная валидация Excel файла.
        Returns: (is_valid, error_message, dataframe)
        """
        try:
            # Асинхронное чтение Excel файла
            excel_file = await asyncio.to_thread(pd.ExcelFile, file_path)
            all_sheets = []
            
            for sheet_name in excel_file.sheet_names:
                df = await asyncio.to_thread(pd.read_excel, file_path, sheet_name=sheet_name)
                df['sheet_name'] = sheet_name
                all_sheets.append(df)
            
            # Объединяем все листы в один DataFrame
            df = pd.concat(all_sheets, ignore_index=True)
            
            # Находим колонку с наименованием
            name_col = self._find_column(df, self.required_columns['name'])
            if not name_col:
                return False, "Не найдена колонка с наименованием", None
            
            # Находим колонку с количеством (опционально)
            quantity_col = self._find_column(df, self.required_columns['quantity'])
            
            # Проверяем наличие значений в колонке наименование
            if df[name_col].isna().all():
                return False, "Колонка с наименованием пуста", None
            
            return True, "", df
        except Exception as e:
            return False, f"Ошибка при чтении файла: {str(e)}", None

    async def _process_product_async(self, product_name: str, quantity: float) -> dict:
        """Асинхронная обработка одного продукта."""
        try:
            search_results = await self._search_product_async(product_name)
            
            if search_results:
                best_match = search_results[0]
                found_name, table, price, similarity, description = best_match
                total_price = quantity * price
                
                return {
                    'Исходный товар': product_name,
                    'Найденный товар': found_name,
                    'Описание': description,
                    'Количество': quantity,
                    'Цена за штуку': price,
                    'Итоговая цена': total_price,
                    'Наша таблица': table,
                    'Сходство': similarity
                }
            else:
                return {
                    'Исходный товар': product_name,
                    'Найденный товар': 'Не найдено',
                    'Описание': '',
                    'Количество': quantity,
                    'Цена за штуку': 0,
                    'Итоговая цена': 0,
                    'Наша таблица': '',
                    'Сходство': 0
                }
        except Exception as e:
            self.logger.error(f"Error processing product {product_name}: {e}")
            return {
                'Исходный товар': product_name,
                'Найденный товар': 'Ошибка обработки',
                'Описание': str(e),
                'Количество': quantity,
                'Цена за штуку': 0,
                'Итоговая цена': 0,
                'Наша таблица': '',
                'Сходство': 0
            }

    async def process_file_async(self, input_file: str, output_file: str) -> tuple[bool, str]:
        """
        Асинхронная обработка входного Excel файла и создание выходного файла с результатами поиска.
        Returns: (success, message)
        """
        try:
            # Валидация файла (10% прогресса)
            await self._update_progress(0.1)
            is_valid, error_msg, df = await self.validate_file_async(input_file)
            if not is_valid:
                return False, error_msg

            # Находим необходимые колонки
            name_col = self._find_column(df, self.required_columns['name'])
            quantity_col = self._find_column(df, self.required_columns['quantity'])

            # Обрабатываем продукты последовательно
            result_data = []
            total_rows = len(df)
            processed_rows = 0

            for _, row in df.iterrows():
                product_name = row[name_col]
                
                # Пропускаем строки с пустым наименованием
                if pd.isna(product_name) or str(product_name).strip() == '':
                    processed_rows += 1
                    continue
                
                # Получаем количество, если колонка существует
                quantity = 1.0
                if quantity_col:
                    try:
                        if not pd.isna(row[quantity_col]) and str(row[quantity_col]).strip() != '':
                            quantity = float(row[quantity_col])
                    except (ValueError, TypeError):
                        pass
                
                # Обрабатываем продукт
                result = await self._process_product_async(str(product_name), quantity)
                result_data.append(result)
                processed_rows += 1
                
                # Обновляем прогресс
                progress = 0.1 + (0.7 * processed_rows / total_rows)
                await self._update_progress(progress)
            
            # Создаем и сохраняем результат
            await self._update_progress(0.8)
            result_df = pd.DataFrame(result_data)
            
            # Сохраняем результат
            def save_excel():
                result_df.to_excel(output_file, index=False)
            
            await asyncio.to_thread(save_excel)
            
            # Применяем форматирование
            await self._update_progress(0.9)
            await asyncio.to_thread(self._format_excel, output_file)
            
            await self._update_progress(1.0)
            return True, "Файл успешно обработан"
        except Exception as e:
            self.logger.exception("Error in process_file_async")
            return False, f"Ошибка при обработке файла: {str(e)}"

    # Оставляем синхронные методы для обратной совместимости
    def _search_product(self, product_name: str) -> List[Tuple[str, str, float, float, str]]:
        """Синхронная версия поиска товара."""
        return asyncio.run(self._search_product_async(product_name))

    def validate_file(self, file_path: str) -> tuple[bool, str, Optional[pd.DataFrame]]:
        """Синхронная версия валидации файла."""
        return asyncio.run(self.validate_file_async(file_path))

    def process_file(self, input_file: str, output_file: str) -> tuple[bool, str]:
        """Синхронная версия обработки файла."""
        return asyncio.run(self.process_file_async(input_file, output_file))

    def _format_excel(self, output_file: str):
        """Форматирование Excel файла с цветами и итоговой строкой"""
        wb = load_workbook(output_file)
        ws = wb.active

        # Определяем стиль границ
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )

        # Определяем цвета для разных уровней схожести
        green_fill = PatternFill(start_color='90EE90', end_color='90EE90', fill_type='solid')
        yellow_fill = PatternFill(start_color='FFFFE0', end_color='FFFFE0', fill_type='solid')
        red_fill = PatternFill(start_color='FFB6C1', end_color='FFB6C1', fill_type='solid')

        # Находим индексы нужных колонок
        total_price_col = None
        description_col = None
        for col in range(1, ws.max_column + 1):
            if ws.cell(row=1, column=col).value == 'Итоговая цена':
                total_price_col = col
            elif ws.cell(row=1, column=col).value == 'Описание':
                description_col = col

        if total_price_col is None:
            raise ValueError("Колонка 'Итоговая цена' не найдена")
        if description_col is None:
            raise ValueError("Колонка 'Описание' не найдена")

        # Устанавливаем фиксированную ширину для всех колонок
        column_widths = {
            'Исходный товар': 30,
            'Найденный товар': 30,
            'Описание': 40,
            'Количество': 12,
            'Цена за штуку': 15,
            'Итоговая цена': 15,
            'Наша таблица': 20,
            'Сходство': 10
        }

        # Применяем ширину колонок
        for col in range(1, ws.max_column + 1):
            col_name = ws.cell(row=1, column=col).value
            if col_name in column_widths:
                ws.column_dimensions[get_column_letter(col)].width = column_widths[col_name]

        # Форматируем каждую строку и собираем формулы для суммирования
        sum_formula_parts = []
        for row in range(1, ws.max_row + 1):  # Начинаем с заголовков
            similarity = None
            if row > 1:  # Для строк с данными проверяем схожесть
                similarity = float(ws.cell(row=row, column=ws.max_column).value)
            
            if row == 1:  # Заголовки
                fill = PatternFill(start_color='D3D3D3', end_color='D3D3D3', fill_type='solid')
                font = Font(bold=True)
            elif similarity >= 1.0:
                fill = green_fill
                # Добавляем ячейку в формулу суммирования только если строка зеленая
                cell_ref = f"{get_column_letter(total_price_col)}{row}"
                sum_formula_parts.append(cell_ref)
            elif similarity >= 0.85:
                fill = yellow_fill
            else:
                fill = red_fill

            # Ограничиваем длину описания и добавляем перенос строк
            if row > 1:  # Только для строк с данными
                description_cell = ws.cell(row=row, column=description_col)
                if description_cell.value:
                    description = str(description_cell.value)
                    if len(description) > 300:  # Ограничиваем длину описания
                        description = description[:300] + "..."
                    description_cell.value = description
                    description_cell.alignment = Alignment(wrap_text=True)

            # Применяем форматирование к каждой ячейке
            for col in range(1, ws.max_column + 1):
                cell = ws.cell(row=row, column=col)
                cell.border = thin_border
                cell.fill = fill
                if row == 1:  # Заголовки
                    cell.font = font
                    cell.alignment = Alignment(horizontal='center')
                else:  # Данные
                    cell.alignment = Alignment(wrap_text=True, vertical='top')

        # Добавляем итоговую строку
        total_row = ws.max_row + 1
        ws.cell(row=total_row, column=1, value="Итого:")
        
        # Формируем формулу для суммирования только зеленых строк
        if sum_formula_parts:
            sum_formula = f"=SUM({','.join(sum_formula_parts)})"
            ws.cell(row=total_row, column=total_price_col, value=sum_formula)
        
        # Форматируем итоговую строку
        bold_font = Font(bold=True)
        for col in range(1, ws.max_column + 1):
            cell = ws.cell(row=total_row, column=col)
            cell.font = bold_font
            cell.fill = PatternFill(start_color='D3D3D3', end_color='D3D3D3', fill_type='solid')
            cell.border = thin_border

        wb.save(output_file)