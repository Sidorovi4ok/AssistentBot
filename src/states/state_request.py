"""
    ╔════════════════════════════════════════════╗
    ║           state_request.py                 ║
    ╚════════════════════════════════════════════╝
    
    Модуль состояний поисковых запросов
    
    Описание:
        Модуль определяет состояния для процесса поиска по текстовому запросу:
    
    Состояния:
        • choosing_list       - Ожидание выбора нужной таблицы для поиска
        • waiting_for_request - Ожидание ввода поискового запроса
        • waiting_for_file    - Ожидание загрузки файла
"""

from aiogram.fsm.state import State, StatesGroup

class RequestStates(StatesGroup):
    choosing_list       = State()
    waiting_for_request = State()
    waiting_for_file    = State()
    