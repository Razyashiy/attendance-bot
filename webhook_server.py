from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
import aiohttp
from config import config
from telegram_bot import telegram_bot
from logging_config import logger

app = FastAPI()

@app.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    if secret != config.telegram.webhook_secret:
        raise HTTPException(403, "Forbidden")
    
    try:
        data = await request.json()
        message = data.get("message", {})
        user = message.get("from", {})
        text = message.get("text", "") or ""
        user_id = user.get("id")

        result = await telegram_bot.process_message(user_id, text, user)
        
        if result.get("response"):
            await send_tg(user_id, result["response"])
        
        return JSONResponse({"ok": True})
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(500, "Internal Error")

async def send_tg(chat_id: int, text: str):
    url = f"https://api.telegram.org/bot{config.telegram.bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    async with aiohttp.ClientSession() as session:
        try:
            await session.post(url, json=payload)
        except:
            pass

@app.get("/health")
async def health():
    return {"status": "ok", "time": "November 11, 2025"}

@app.get("/qr_scan")
async def qr_scan(class_name: str = "9A"):
    return HTMLResponse(f"""
    <h1>Класс {class_name}</h1>
    <p>Наведите камеру на QR-код в классе</p>
    <script>
        setTimeout(() => location.href = "https://t.me/your_attendance_bot", 2000);
    </script>
    """)
