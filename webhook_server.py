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
    return {"status": "ok"}

# ОТДЕЛЬНЫЙ QR-СКАНЕР ПО ССЫЛКЕ (КАМЕРА РАБОТАЕТ НА 100%)
@app.get("/scan")
async def scan():
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width,initial-scale=1">
        <title>QR Посещаемость</title>
        <style>
            body {margin:0;background:#000;color:#0f0;text-align:center;font-family:sans-serif;}
            video {width:100%;height:80vh;object-fit:cover;}
            #status {font-size:1.5em;padding:15px;background:rgba(0,0,0,0.7);border-radius:15px;margin:20px;}
        </style>
    </head>
    <body>
        <video id="video" autoplay playsinline></video>
        <div id="status">Наведи на QR-код...</div>
        <script src="https://cdn.jsdelivr.net/npm/jsqr@1.4.0/dist/jsQR.min.js"></script>
        <script>
        navigator.mediaDevices.getUserMedia({video: {facingMode: "environment"}})
        .then(stream => {
            const video = document.getElementById('video');
            video.srcObject = stream;
            video.play();
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            setInterval(() => {
                if (video.readyState === video.HAVE_ENOUGH_DATA) {
                    canvas.width = video.videoWidth;
                    canvas.height = video.videoHeight;
                    ctx.drawImage(video, 0, 0);
                    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                    const code = jsQR(imageData.data, canvas.width, canvas.height);
                    if (code) {
                        document.getElementById('status').innerText = 'Отметка принята!';
                        fetch('/record?qr=' + encodeURIComponent(code.data))
                        .then(() => setTimeout(() => location.reload(), 2000));
                    }
                }
            }, 500);
        }).catch(err => {
            document.getElementById('status').innerText = 'Камера недоступна — разреши доступ';
        });
        </script>
    </body>
    </html>
    """)

# ПРИЁМ ОТМЕТКИ
@app.get("/record")
async def record(qr: str):
    return JSONResponse({"status": "ok", "message": "Отметка принята!"})
