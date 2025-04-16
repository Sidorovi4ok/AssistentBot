
"""
    Импортирует все фильтры для дальнейшего использования из filters
"""

from .filter_article      import filter_article
from .filter_product_name import filter_product_name
from .filter_not_auth     import filter_not_authorized
from .filter_only_auth    import filter_only_auth
from .filter_only_manager import filter_only_manager
from .filter_only_admin   import filter_only_admin


"""
    Определяем список объектов, которые будут доступны при импорте пакета
    Это позволяет скрыть внутренние детали реализации и 
    предоставляет только нужные элементы для использования
"""
__all__ = [
    "filter_article",
    "filter_product_name",
    "filter_not_authorized",
    "filter_only_auth",
    "filter_only_manager",
    "filter_only_admin"
]
