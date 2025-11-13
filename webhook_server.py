from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from config import config
from database_manager import database_manager
from telegram_bot import bot
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "ok"}

# QR-СКАНЕР (Telegram WebApp)
@app.get("/qr_universal")
async def qr_universal():
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width,initial-scale=1">
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <style>
            body {margin:0;background:#000;color:#0f0;text-align:center;padding:40px;font-family:sans-serif;}
            h1 {font-size:2em;}
            button {background:#0f0;color:#000;padding:18px 40px;font-size:1.5em;border:none;border-radius:15px;margin:20px;cursor:pointer;}
        </style>
    </head>
    <body>
        <h1>QR Посещаемость</h1>
        <button onclick="scan()">СКАНИРОВАТЬ QR</button>
        <script>
        function scan() {
            Telegram.WebApp.showScanQrPopup({text: "Наведи на QR в классе"});
        }

        Telegram.WebApp.onEvent('qrTextReceived', function(event) {
            const qr = event.data;
            Telegram.WebApp.closeScanQrPopup();
            fetch('/record?qr=' + encodeURIComponent(qr))
            .then(() => {
                Telegram.WebApp.showAlert('Отметка принята! Success');
                setTimeout(() => Telegram.WebApp.close(), 1500);
            });
        });
        </script>
    </body>
    </html>
    """)

# ПРИЁМ ОТМЕТКИ
@app.get("/record")
async def record(qr: str, request: Request):
    init_data = request.headers.get("X-Telegram-WebApp-Init-Data")
    if not init_data:
        return JSONResponse({"status": "error"})

    try:
        import urllib.parse, json
        params = dict(urllib.parse.parse_qsl(init_data))
        user = json.loads(params.get("user", "{}"))
        user_id = int(user["id"])
        
        database_manager.record_attendance(user_id, "QR")
        
        full_name = user.get("first_name", "Студент")
        await bot.send_message(
            config.telegram.admin_chat_id,
            f"ВХОД\n{full_name}\n{datetime.now().strftime('%H:%M:%S')} | QR"
        )
    except Exception as e:
        logger.error(f"Ошибка: {e}")
    
    return JSONResponse({"status": "ok"})
