import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from webhook_server import app as webhook_app
from telegram_bot import telegram_bot

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await telegram_bot.setup_webhook(webhook_url=f"{config.public_url}/webhook/telegram")
    yield
    # Shutdown
    pass

app = FastAPI(lifespan=lifespan)

app.mount("/", webhook_app)

if __name__ == "__main__":
    import uvicorn
    import os
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8080)), reload=False)
