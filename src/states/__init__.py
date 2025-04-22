"""
    ╔════════════════════════════════════════════╗
    ║               __init__.py                  ║
    ╚════════════════════════════════════════════╝
    
    Модуль состояний
    
    Описание:
        Модуль предоставляет доступ к классам состояний для различных 
        процессов в приложении:
    
    • AuthStates         - Состояния процесса авторизации
    • RequestStates      - Состояния процесса обработки запросов
    • ManagerPanelStates - Состояния панели управления
"""

from .state_auth          import AuthStates
from .state_request       import RequestStates
from .state_manager_panel import ManagerPanelStates

__all__ = ["AuthStates", "RequestStates", "ManagerPanelStates"]
