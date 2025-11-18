import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from webhook_server import app as webhook_app          # ← ОК
from telegram_bot import bot, dp                       # ← ИСПРАВЛЕНО: bot и dp
from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Система запущена — Школа Россия 2025")
    yield
    await bot.session.close()

# Основное приложение
app = FastAPI(lifespan=lifespan, title="Школа Россия 2025")

# Подключаем роуты от webhook_server
app.mount("/", webhook_app)

# Запуск бота в фоне (polling)
@app.on_event("startup")
async def startup():
    logger.info("Запуск бота в режиме polling...")
    asyncio.create_task(dp.start_polling(bot))

# Для Railway
if __name__ == "__main__":
    import uvicorn
    import os
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
