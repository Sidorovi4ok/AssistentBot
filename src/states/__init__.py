
"""
    Импортируем все состояни из пакета states
"""

from .state_auth     import AuthStates
from .state_request  import RequestStates
from .state_manager_panel import ManagerPanelStates

"""
    Определяем список объектов, которые будут доступны при импорте пакета.
    AuthStates      - Состояния для процесса авторизации
    RequestStates   - Состояния для процесса запросов
    
"""
__all__ = ["AuthStates", "RequestStates", "ManagerPanelStates"]
