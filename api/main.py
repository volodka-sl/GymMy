import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# добавляем родительский каталог в sys.path, чтобы найти storage, handlers и т.д.
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

# настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s"
)
logger = logging.getLogger("api")

from api.routers.robokassa import router as robokassa_router

app = FastAPI(
    title="GymMy Payment Webhook",
    description="Принимает колл-бэки от Robokassa и уведомляет бота",
    version="1.0",
)

# CORS, если понадобится
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(robokassa_router, prefix="/robokassa", tags=["robokassa"])

logger.info("FastAPI payment webhook initialized")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=int(os.getenv("API_PORT", 8000)),
        reload=True
    )
