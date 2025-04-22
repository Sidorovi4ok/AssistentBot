"""
    ╔════════════════════════════════════════════╗
    ║       state_manager_panel.py               ║
    ╚════════════════════════════════════════════╝
    
    Модуль состояний панели управления менеджера
    
    Описание:
        Модуль определяет состояния для процесса управления скидками 
        и другими параметрами пользователей:
    
    Состояния:
        • waiting_for_file          - Ожидание загрузки файла
        • waiting_for_inn           - Ожидание ввода ИНН пользователя
        • waiting_for_type          - Ожидание выбора типа операции
        • waiting_for_type_discount - Ожидание выбора типа скидки
        • waiting_for_new_discount  - Ожидание ввода нового значения скидки
"""

from aiogram.fsm.state import State, StatesGroup

class ManagerPanelStates(StatesGroup):
    waiting_for_file          = State()
    waiting_for_inn           = State()
    waiting_for_type          = State()
    waiting_for_type_discount = State()
    waiting_for_new_discount  = State()