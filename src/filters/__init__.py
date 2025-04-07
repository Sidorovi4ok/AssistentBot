
# Импортируем функцию регистрации обработчиков из модуля commands.
# Эта функция используется для регистрации всех обработчиков команд и сообщений в диспетчере.

from .filter_article import filter_article
from .filter_product_name import filter_product_name

from .filter_not_auth import filter_not_authorized
from .filter_only_auth import filter_only_auth

from .filter_only_manager import filter_only_manager

# Модуль содержит все необходимые функции для регистрации обработчиков команд и сообщений для бота.
# Эти обработчики управляют тем, как бот реагирует на команды, такие как /start, /help и т.д.

# Определяем список объектов, которые будут доступны при импорте пакета.
# Это позволяет скрыть внутренние детали реализации и предоставляет только нужные элементы для использования.
__all__ = ["filter_article", "filter_product_name", "filter_not_authorized", "filter_only_auth", "filter_only_manager"]
