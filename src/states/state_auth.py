"""
    ╔════════════════════════════════════════════╗
    ║           state_auth.py                    ║
    ╚════════════════════════════════════════════╝
    
    Модуль состояний авторизации
    
    Описание:
        Модуль определяет состояния для процесса авторизации пользователей:
    
    Состояния:
        • waiting_for_inn_login    - Ожидание ввода ИНН для авторизации
        • waiting_for_inn_register - Ожидание ввода ИНН для регистрации
"""

from aiogram.fsm.state import State, StatesGroup

class AuthStates(StatesGroup):
    waiting_for_inn_login    = State()
    waiting_for_inn_register = State()
