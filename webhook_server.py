from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from telegram_bot import bot
from database_manager import database_manager
from config import config
from datetime import datetime

app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/scan")
async def scan_page():
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width,initial-scale=1">
        <title>QR — Школа Россия 2025</title>
        <style>
            body,html{margin:0;padding:0;height:100%;background:#000;overflow:hidden;font-family:sans-serif;}
            #container{position:relative;width:100%;height:100%;}
            video{width:100%;height:100%;object-fit:cover;}
            #overlay{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);
                     width:280px;height:280px;border:4px solid #0f0;box-shadow:0 0 0 9999px rgba(0,0,0,0.65);
                     border-radius:18px;box-sizing:border-box;}
            #overlay::after{content:"";position:absolute;top:0;left:0;right:0;bottom:0;
                     border:3px solid #0f0;border-radius:18px;animation:scan 2s infinite;}
            @keyframes scan{0%,100%{clip-path:polygon(0 0,100% 0,100% 8%,0 8%);}
                           50%{clip-path:polygon(0 0,100% 0,100% 100%,0 100%);}}
            #msg{position:absolute;bottom:80px;left:50%;transform:translateX(-50%);
                 background:rgba(0,255,0,0.25);color:#0f0;padding:16px 36px;border-radius:50px;
                 font-size:1.3em;backdrop-filter:blur(10px);border:1px solid #0f0;}
        </style>
    </head>
    <body>
        <div id="container">
            <video id="video" autoplay playsinline muted></video>
            <div id="overlay"></div>
            <div id="msg">Наведи квадрат на QR-код</div>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/jsqr@1.4.0/dist/jsQR.min.js"></script>
        <script>
        const video = document.getElementById('video');
        const msg = document.getElementById('msg');
        let scanning = true;
        navigator.mediaDevices.getUserMedia({video:{facingMode:"environment"}})
        .then(stream => {
            video.srcObject = stream;
            video.play();
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            const tick = () => {
                if (video.readyState === video.HAVE_ENOUGH_DATA && scanning) {
                    canvas.width = video.videoWidth;
                    canvas.height = video.videoHeight;
                    ctx.drawImage(video, 0, 0);
                    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                    const code = jsQR(imageData.data, imageData.width, imageData.height);
                    if (code) {
                        scanning = false;
                        msg.innerHTML = "Отметка принята!";
                        msg.style.background = "rgba(0,255,0,0.8)";
                        fetch("/mark?qr=" + encodeURIComponent(code.data))
                        .finally(() => setTimeout(() => location.href = "tg://resolve?domain=Attendance_sbot", 1500));
                    }
                }
                requestAnimationFrame(tick);
            };
            requestAnimationFrame(tick);
        })
        .catch(() => {
            msg.innerText = "Разреши камеру в настройках";
            msg.style.background = "rgba(255,0,0,0.7)";
        });
        </script>
    </body>
    </html>
    """)

@app.get("/mark")
async def mark(qr: str):
    class_name = qr.strip().upper()
    database_manager.record_attendance(
        telegram_id=0,
        method="QR",
        class_name=class_name
    )
    await bot.send_message(
        config.telegram.admin_chat_id,
        f"ВХОД\n"
        f"{datetime.now().strftime('%H:%M:%S')} | QR\n"
        f"Класс: {class_name}"
    )
    return JSONResponse({"ok": True})
    return JSONResponse({"ok": True})


