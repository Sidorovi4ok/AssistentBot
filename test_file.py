import os
import pandas as pd
from fuzzywuzzy import fuzz
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Border, Side
from src.managers.manager_price import DataManager

# --- НАСТРОЙКИ ---
INPUT_EXCEL = 'test_1.xlsx'
OUTPUT_EXCEL = 'sales_report.xlsx'
SIMILARITY_THRESHOLD = 80  # порог схожести (0-100)
FUZZY_METHOD = fuzz.WRatio  # алгоритм fuzzywuzzy

# Возможные названия колонок
PRODUCT_COLUMNS = ['Наименование товара', 'Товар', 'Название', 'Наименование', 'Product', 'Item']
QUANTITY_COLUMNS = ['Количество', 'Кол-во', 'Quantity', 'Кол', 'Qty']

# Инициализация DataManager
dm = DataManager.initialize('price-list.xlsx', update_db=False)


def preprocess_string(s: str) -> str:
    return str(s).strip().lower()


def find_product_in_db(product_name: str):
    exact_matches = []
    partial_matches = []
    clean_name = preprocess_string(product_name)

    for table in dm.get_all_table_names():
        df = dm.get_table_data(table)
        if 'Наименование' not in df.columns:
            continue

        for _, row in df.iterrows():
            db_name = preprocess_string(row['Наименование'])
            score = FUZZY_METHOD(clean_name, db_name)
            if score == 100:
                exact_matches.append(row)
            elif score >= SIMILARITY_THRESHOLD:
                partial_matches.append({'row': row, 'score': score})

    partial_matches.sort(key=lambda x: x['score'], reverse=True)
    return exact_matches, [pm['row'] for pm in partial_matches]


def process_input_sheets(input_file):
    """Обработка всех листов входного файла"""
    xls = pd.ExcelFile(input_file)
    all_data = []

    for sheet_name in xls.sheet_names:
        df = xls.parse(sheet_name)

        # Поиск колонки с наименованием товара
        product_col = next((col for col in PRODUCT_COLUMNS if col in df.columns), None)
        if not product_col:
            raise ValueError(f"Лист '{sheet_name}' не содержит подходящей колонки с товарами")

        # Переименовываем в стандартное название
        df.rename(columns={product_col: 'Наименование товара'}, inplace=True)

        # Поиск колонки с количеством
        quantity_col = next((col for col in QUANTITY_COLUMNS if col in df.columns), None)
        if not quantity_col:
            df['Кол-во'] = 1
        else:
            # Переименовываем в стандартное название
            df.rename(columns={quantity_col: 'Кол-во'}, inplace=True)

        # Обработка количества
        df['Кол-во'] = df['Кол-во'].apply(lambda x:
                                          int(float(x)) if pd.notnull(x) and float(x) > 0 else 1
                                          )

        # Сохраняем исходное имя листа
        df['Источник'] = sheet_name
        all_data.append(df)

    return pd.concat(all_data, ignore_index=True)


# --- ОБРАБОТКА ВХОДНЫХ ДАННЫХ ---
combined_df = process_input_sheets(INPUT_EXCEL)
report_data = []

for _, row in combined_df.iterrows():
    prod = row['Наименование товара']
    quantity = row['Кол-во']
    exact, partial = find_product_in_db(prod)

    base = {
        'Источник': row.get('Источник', ''),
        'Ваши предложения': prod,
        'Наши товары': '',
        'Кол-во': quantity,
        'Описание': '',
        'Цена за единицу': 0,
        'Коэф.': 0.0,
        'Статус': 'red'
    }

    if exact:
        match = exact[0]
        base.update({
            'Наши товары': match['Наименование'],
            'Описание': match.get('Описание', ''),
            'Цена за единицу': match.get('Цена с НДС', 0),
            'Коэф.': 1.0,
            'Статус': 'green'
        })
    elif partial:
        match = partial[0]
        base.update({
            'Наши товары': match['Наименование'],
            'Описание': match.get('Описание', ''),
            'Цена за единицу': match.get('Цена с НДС', 0),
            'Статус': 'yellow'
        })

    report_data.append(base)

# --- ФОРМИРОВАНИЕ ОТЧЁТА ---
report_df = pd.DataFrame(report_data)
report_df.insert(0, '№', range(1, len(report_df) + 1))
report_df['Итоговая цена'] = (
        report_df['Цена за единицу'] *
        report_df['Кол-во'] *
        report_df['Коэф.']
)

report_df.rename(columns={'Цена за единицу': 'Цена за единицу, ₽'}, inplace=True)
export_columns = ['№', 'Источник', 'Ваши предложения', 'Наши товары',
                  'Кол-во', 'Описание', 'Цена за единицу, ₽',
                  'Коэф.', 'Итоговая цена']

# --- ЗАПИСЬ В EXCEL ---
wb = Workbook()
ws = wb.active
ws.append(export_columns)

# Стили оформления
fills = {
    'green': PatternFill(start_color='C6EFCE', fill_type='solid'),
    'yellow': PatternFill(start_color='FFEB9C', fill_type='solid'),
    'red': PatternFill(start_color='FFC7CE', fill_type='solid'),
}
bold_font = Font(bold=True)
border = Border(top=Side(style='medium'), bottom=Side(style='medium'))

for idx, row in report_df.iterrows():
    ws.append([row[col] for col in export_columns])
    for cell in ws[ws.max_row]:
        cell.fill = fills[row['Статус']]

# Итоговая строка
total = report_df.loc[report_df['Статус'] == 'green', 'Итоговая цена'].sum()
ws.append(['Итого'] + [''] * (len(export_columns) - 2) + [total])

# Форматирование итоговой строки
for cell in ws[ws.max_row]:
    cell.font = bold_font
    cell.border = border

# Настройка ширины столбцов
col_widths = {
    'A': 8, 'B': 20, 'C': 40, 'D': 40,
    'E': 10, 'F': 80, 'G': 18, 'H': 10, 'I': 15
}
for col, w in col_widths.items():
    ws.column_dimensions[col].width = w

wb.save(OUTPUT_EXCEL)
print(f'Отчет успешно сгенерирован: {OUTPUT_EXCEL}')