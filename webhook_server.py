from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from config import config
from database_manager import database_manager
from telegram_bot import bot
from logging_config import logger
from datetime import datetime

app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "ok", "bot": "running", "time": "November 13, 2025"}

# QR-КАМЕРА (Mini App)
@app.get("/qr_universal")
async def qr_universal():
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width,initial-scale=1">
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
    </head>
    <body style="margin:0;background:#000;">
        <video id="v" autoplay playsinline style="width:100%;height:100vh;object-fit:cover;"></video>
        <div id="s" style="position:absolute;bottom:30px;left:50%;transform:translateX(-50%);color:#0f0;font-size:1.5em;background:rgba(0,0,0,0.6);padding:15px 30px;border-radius:15px;">
            Наведи на QR в классе...
        </div>
        <script src="https://cdn.jsdelivr.net/npm/jsqr@1.4.0/dist/jsQR.min.js"></script>
        <script>
        navigator.mediaDevices.getUserMedia({video:{facingMode:"environment"}})
        .then(stream => {
            document.getElementById('v').srcObject = stream;
            setInterval(() => {
                let v = document.getElementById('v');
                let c = document.createElement('canvas');
                c.width = v.videoWidth; c.height = v.videoHeight;
                c.getContext('2d').drawImage(v, 0, 0);
                let code = jsQR(c.getContext('2d').getImageData(0,0,c.width,c.height).data, c.width, c.height);
                if (code && code.data.includes('t.me')) {
                    document.getElementById('s').innerText = 'Отметка принята!';
                    fetch('/record?qr=' + encodeURIComponent(code.data))
                    .then(() => Telegram.WebApp.close());
                }
            }, 500);
        });
        </script>
    </body>
    </html>
    """)

# ПРИЁМ ОТМЕТКИ ОТ КАМЕРЫ
@app.get("/record")
async def record(qr: str):
    # Здесь можно добавить проверку класса по QR, если нужно
    return JSONResponse({"status": "ok", "message": "Отметка принята!"})
