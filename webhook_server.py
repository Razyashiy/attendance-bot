from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from datetime import datetime

from telegram_bot import telegram_bot
from config import config
from logging_config import logger
from database_manager import database_manager

app = FastAPI(title="Attendance System API")

@app.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    secret_token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    if secret_token != config.telegram.secret_token:
        raise HTTPException(403, "Forbidden")
    
    try:
        data = await request.json()
        message = data.get('message', {})
        user = message.get('from', {})
        text = message.get('text', '')
        user_id = user.get('id')
        
        result = await telegram_bot.process_message(user_id, text, user)
        
        # Отправляем ответ в Telegram
        if result.get('response'):
            await send_telegram_message(user_id, result['response'])
        
        return JSONResponse(result)
    except Exception as e:
        logger.error(f"❌ Webhook error: {e}")
        raise HTTPException(500, str(e))

async def send_telegram_message(chat_id: int, text: str):
    import httpx
    url = f"https://api.telegram.org/bot{config.telegram.secret_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    async with httpx.AsyncClient() as client:
        await client.post(url, json=payload, timeout=10)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/stats")
async def get_system_stats():
    stats = database_manager.get_attendance_stats()
    return {"data": stats}

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    with open("web_panel.html", "r", encoding="utf-8") as f:
        return f.read()

# Для статики (если добавишь CSS/JS отдельно)
app.mount("/static", StaticFiles(directory="static"), name="static")

async def start():
    logger.info(f"🚀 Server starting on {config.server.host}:{config.server.port}")
    uvicorn.run(app, host=config.server.host, port=config.server.port, reload=config.server.debug)

webhook_server = app