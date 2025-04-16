
"""
    state_discount.py
    Состояние для процесса изменения скидки для пользователей
"""

from aiogram.fsm.state import State, StatesGroup


"""
    waiting_for_file      - ожидание ввода типа пользователя
    waiting_for_new_discount  - ожидание ввода значения для новой скидки
"""
class ManagerPanelStates(StatesGroup):
    waiting_for_file         = State()
    waiting_for_inn          = State()
    waiting_for_type         = State()

    waiting_for_type_discount = State()
    waiting_for_new_discount = State()