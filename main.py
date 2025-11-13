import asyncio
from fastapi import FastAPI
from webhook_server import app as webhook_app
from telegram_bot import start_polling

app = FastAPI()

# Веб-панель и QR-сканер
app.mount("/", webhook_app)

# Запуск бота
@app.on_event("startup")
async def startup():
    asyncio.create_task(start_polling())

if __name__ == "__main__":
    import uvicorn
    import os
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8080)), reload=False)
