from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from config import config
from database_manager import database_manager
from telegram_bot import bot
from logging_config import logger
from datetime import datetime

app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "ok", "time": "November 13, 2025"}

# НАТИВНЫЙ QR-СКАНЕР (РАБОТАЕТ В MINI APP!)
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
            button {background:#0f0;color:#000;padding:15px 30px;font-size:1.5em;border:none;border-radius:12px;margin:20px;cursor:pointer;}
        </style>
    </head>
    <body>
        <h1>Отметка посещаемости</h1>
        <p>Нажми кнопку и наведи камеру на QR-код</p>
        <button onclick="scan()">СКАНИРОВАТЬ QR</button>
        <script>
        function scan() {
            Telegram.WebApp.showScanQrPopup({text: "Наведи на QR в классе"});
        }

        Telegram.WebApp.onEvent('qrTextReceived', function(data) {
            Telegram.WebApp.closeScanQrPopup();
            fetch('/record?qr=' + encodeURIComponent(data.data))
            .then(() => {
                Telegram.WebApp.showAlert('Отметка принята! ✅');
                setTimeout(() => Telegram.WebApp.close(), 1000);
            });
        });
        </script>
    </body>
    </html>
    """)

# ПРИЁМ ОТМЕТКИ
@app.get("/record")
async def record(qr: str, request: Request):
    user_data = request.headers.get("X-Telegram-WebApp-Init-Data")
    if not user_data:
        return JSONResponse({"status": "error"})

    try:
        # Парсим user_id из initData
        import urllib.parse
        params = dict(urllib.parse.parse_qsl(user_data))
        user = eval(params.get("user", "{}"))
        user_id = int(user.get("id"))
        
        database_manager.record_attendance(user_id, "QR")
        await bot.send_message(
            config.telegram.admin_chat_id,
            f"ВХОД\nСтудент\n{datetime.now().strftime('%H:%M:%S')} | QR"
        )
    except:
        pass
    
    return JSONResponse({"status": "ok"})
