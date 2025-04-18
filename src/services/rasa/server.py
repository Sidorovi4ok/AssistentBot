from fastapi import FastAPI, Request
from pydantic import BaseModel
import uvicorn
import logging
from rasa.core.agent import Agent
from contextlib import asynccontextmanager
import os

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QueryRequest(BaseModel):
    text: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global agent
    model_path = "nlu/models"  # Проверьте, что путь правильный!
    if not os.path.exists(model_path):
        os.makedirs(model_path)

    try:
        agent = Agent.load(model_path)
        logger.info("✅ NLU модель успешно загружена")
    except Exception as e:
        logger.error(f"❌ Ошибка при загрузке модели: {e}")
        raise
    yield
    # Shutdown
    pass


app = FastAPI(lifespan=lifespan)


@app.post("/parse/")
async def parse_query(request: QueryRequest):
    try:
        result = await agent.parse_message(request.text)
        intent = result.get("intent", {}).get("name", "unknown")
        entities = {e.get("entity"): e.get("value") for e in result.get("entities", [])}
        return {
            "query": request.text,
            "intent": intent,
            "entities": entities
        }
    except Exception as e:
        logger.error(f"Ошибка при разборе запроса: {e}")
        return {"error": str(e)}


# Запуск сервера
if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)