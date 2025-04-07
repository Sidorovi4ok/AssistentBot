from aiogram.fsm.state import State, StatesGroup

class AuthStates(StatesGroup):
    waiting_for_inn_login = State()
    waiting_for_inn_register = State()
