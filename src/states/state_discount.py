from aiogram.fsm.state import State, StatesGroup

class DiscountStates(StatesGroup):
    waiting_for_user_type = State()
    waiting_for_new_discount = State()
