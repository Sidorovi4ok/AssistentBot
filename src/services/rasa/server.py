"""
    ╔════════════════════════════════════════════╗
    ║           rasa/server.py                   ║
    ╚════════════════════════════════════════════╝
    
    FastAPI сервер для обработки запросов к Rasa NLU
    
    Описание:
        Сервер предоставляет REST API для обработки текстовых запросов
        с использованием Rasa NLU. Поддерживает асинхронную обработку
        и автоматическую загрузку модели при старте.
"""

import uvicorn
import logging

from pydantic        import BaseModel, Field
from typing          import Dict, Optional
from contextlib      import asynccontextmanager
from fastapi         import FastAPI, HTTPException
from pathlib         import Path
from rasa.core.agent import Agent



MODEL_PATH = Path("nlu/models")

logging.basicConfig(
    level  = getattr(logging, "INFO"),
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
agent: Optional[Agent] = None


# Модели данных
class QueryRequest(BaseModel):
    """
        Модель запроса для обработки текста
    """
    text: str = Field(
        ...,
        min_length  = 1,
        max_length  = 1000,
        description = "Текст для обработки"
    )

class QueryResponse(BaseModel):
    """
        Модель ответа с результатами обработки
    """
    query:  str = Field(..., description="Исходный текст запроса")
    intent: str = Field(..., description="Определенное намерение")
    entities: Dict[str, str] = Field(
        default_factory=dict,
        description="Извлеченные сущности"
    )
    confidence: float = Field(..., description="Уверенность в определении намерения")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
        Управление жизненным циклом приложения
    """
    global agent
    logger.info("🚀 Запуск сервера Rasa NLU")
    
    if not MODEL_PATH.exists():
        logger.warning(f"⚠️ Директория модели не существует: {MODEL_PATH}")
        MODEL_PATH.mkdir(parents=True, exist_ok=True)
        logger.info(f"✅ Создана директория: {MODEL_PATH}")

    try:
        agent = Agent.load(str(MODEL_PATH))
        logger.info("✅ NLU модель успешно загружена")
    except Exception as e:
        logger.error(f"❌ Ошибка при загрузке модели: {e}")
        raise RuntimeError(f"Не удалось загрузить модель: {e}")
    yield
    logger.info("🛑 Выключение сервера Rasa NLU")


app = FastAPI(
    title       = "Rasa NLU Server",
    description = "API сервер для обработки текстовых запросов с использованием Rasa NLU",
    version     = "1.0.0",
    lifespan    = lifespan
)


@app.get("/health")
async def health_check():
    """
        Проверка работоспособности сервера
    """
    return {
        "status": "healthy",
        "model_loaded": agent is not None
    }


@app.post("/parse/", response_model=QueryResponse)
async def parse_query(request: QueryRequest):
    """
        Обработка текстового запроса
    """
    try:
        result = await agent.parse_message(request.text)
        
        intent_data = result.get("intent", {})
        intent      = intent_data.get("name", "unknown")
        confidence  = intent_data.get("confidence", 0.0)
        
        entities = {
            e.get("entity"): e.get("value") 
            for e in result.get("entities", [])
        }
            
        response = QueryResponse(
            query      = request.text,
            intent     = intent,
            entities   = entities,
            confidence = confidence
        )
        
        return response
        
    except Exception as e:
        logger.error(f"❌ Ошибка при разборе запроса: {e}")
        raise HTTPException(
            status_code = 500,
            detail = f"Ошибка при обработке запроса: {str(e)}"
        )


if __name__ == "__main__":
    logger.info(f"🌐 Запуск сервера на 0.0.0.0:8000")
    uvicorn.run(
        "server:app",
        host = "0.0.0.0",
        port = 8000,
        reload = False,
        log_level = "info"
    )