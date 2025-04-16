
"""
    state_auth.py
    Состояние для процесса авторизации
"""

from aiogram.fsm.state import State, StatesGroup


"""
    waiting_for_inn_login     - ожидание ввода инн для авторизации
    waiting_for_inn_register  - ожидание ввода инн для регистрации
"""
class AuthStates(StatesGroup):
    waiting_for_inn_login    = State()
    waiting_for_inn_register = State()
