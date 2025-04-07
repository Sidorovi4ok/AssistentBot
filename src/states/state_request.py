from aiogram.fsm.state import State, StatesGroup

class RequestStates(StatesGroup):
    """Класс состояний FSM для управления процессом запроса."""
    choosing_list       = State()  # Выбор таблицы
    waiting_for_request = State()  # Ожидание ввода поискового запроса