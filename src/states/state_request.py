
"""
    state_request.py
    Состояние для процесса поиска по текстовому запросу
"""

from aiogram.fsm.state import State, StatesGroup


"""
    choosing_list        - ожидание выбора нужной таблицы
    waiting_for_request  - ожидание ввода поиского запроса
"""
class RequestStates(StatesGroup):
    choosing_list       = State()
    waiting_for_request = State()