from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
import aiohttp
from config import config
from telegram_bot import telegram_bot
from database_manager import database_manager
from logging_config import logger

app = FastAPI()

@app.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    if secret != config.telegram.webhook_secret:
        raise HTTPException(403, "Forbidden")
    
    data = await request.json()
    message = data.get("message", {})
    user = message.get("from", {})
    text = message.get("text", "") or ""
    user_id = user.get("id")
    username = user.get("username", "")
    first_name = user.get("first_name", "")
    last_name = user.get("last_name", "")

    result = await telegram_bot.process_message(
        user_id, text,
        {"first_name": first_name, "last_name": last_name, "username": username}
    )

    if result.get("response"):
        keyboard = result.get("keyboard")
        reply_markup = {"keyboard": keyboard, "resize_keyboard": True} if keyboard else {"remove_keyboard": True}
        await send_tg(user_id, result["response"], reply_markup)

    return JSONResponse({"ok": True})

async def send_tg(chat_id: int, text: str, reply_markup: dict = None):
    url = f"https://api.telegram.org/bot{config.telegram.bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    async with aiohttp.ClientSession() as session:
        try:
            await session.post(url, json=payload)
        except:
            pass

@app.get("/health")
async def health():
    return {"status": "ok", "bot": "working"}

@app.get("/qr_universal")
async def qr_universal():
    return HTMLResponse("""
    <!DOCTYPE html><html><body style="margin:0;background:#000;">
    <video id="v" autoplay playsinline style="width:100%;height:100vh;"></video>
    <div id="s" style="position:absolute;bottom:20px;color:lime;font-size:2em;left:20px;">Наведи на QR...</div>
    <script src="https://cdn.jsdelivr.net/npm/jsqr@1.4.0/dist/jsQR.min.js"></script>
    <script>
    navigator.mediaDevices.getUserMedia({video:{facingMode:"environment"}})
    .then(s=>{document.getElementById('v').srcObject=s;
    setInterval(()=>{let v=document.getElementById('v'),c=document.createElement('canvas');
    c.width=v.videoWidth;c.height=v.height;
    c.getContext('2d').drawImage(v,0,0);
    let code=jsQR(c.getContext('2d').getImageData(0,0,c.width,c.height).data,c.width,c.height);
    if(code){fetch('/record?qr='+encodeURIComponent(code.data));}},400);});
    </script></body></html>
    """)
