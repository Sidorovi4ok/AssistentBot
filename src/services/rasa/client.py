import requests


class RasaClient:
    """Класс для работы с Rasa моделью"""

    def __init__(self, api_url="http://localhost:8000/parse/"):
        self.api_url = api_url
        self.is_available = self._check_availability()

    def _check_availability(self):
        """Проверяет доступность Rasa API"""
        try:
            response = self.query("test query")
            if response:
                print("[✓] Rasa NLU API доступен и работает")
                return True
            return False
        except Exception as e:
            print(f"[❌] Rasa NLU API недоступен: {str(e)}")
            return False

    def query(self, text):
        """Отправляет запрос в Rasa NLU и возвращает результат"""
        try:
            response = requests.post(self.api_url, json={"text": text})
            if response.status_code == 200:
                return response.json()
            else:
                print(f"[⚠] Ошибка при запросе к Rasa NLU API: {response.status_code}")
                return None
        except Exception as e:
            print(f"[❌] Исключение при обращении к Rasa NLU API: {str(e)}")
            return None

    def extract_entities(self, query):
        """Извлекает сущности из запроса"""
        response = self.query(query)

        if response and "entities" in response:
            entities = response["entities"]
            print(f"[ℹ] Rasa извлекла сущности: {entities}")
            return entities

        print("[⚠] Rasa не смогла извлечь сущности")
        return {}

    def classify_intent(self, query):
        """Определяет намерение из запроса"""
        response = self.query(query)

        if response and "intent" in response:
            intent = response["intent"]
            print(f"[ℹ] Rasa определила намерение: {intent}")
            return intent

        print("[⚠] Rasa не смогла определить намерение")
        return "unknown"

    def detect_target_column(self, query):
        """Определяет целевую колонку для поиска на основе Rasa анализа"""
        response = self.query(query)

        if response and "entities" in response:
            entities = response["entities"]
            if "artikul" in entities:
                return "Артикул"
            if "naimenovanie" in entities:
                return "Наименование"

        if response and "intent" in response:
            intent = response["intent"]
            if intent == "search_by_artikul":
                return "Артикул"
            if intent == "search_by_naimenovanie":
                return "Наименование"

        # По умолчанию ищем по наименованию
        return "Наименование"