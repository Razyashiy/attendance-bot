# webhook_server.py — ФИНАЛЬНЫЙ ПОСРЕДНИК С КВАДРАТОМ

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

# КРАСИВЫЙ СКАНЕР С КВАДРАТОМ
@app.get("/scan")
async def scan_page():
    return HTMLResponse("""
    <!DOCTYPE html>
    <html><head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width,initial-scale=1">
        <title>QR — Школа 2025</title>
        <style>
            body,html{margin:0;padding:0;height:100%;background:#000;overflow:hidden;}
            #c{position:relative;width:100%;height:100%;}
            video{width:100%;height:100%;object-fit:cover;}
            #box{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);
                 width:280px;height:280px;border:4px solid #0f0;
                 box-shadow:0 0 0 9999px rgba(0,0,0,0.7);border-radius:18px;}
            #box::after{content:"";position:absolute;inset:0;
                 border:3px solid #0f0;border-radius:3px solid #0f0;border-radius:18px;
                 animation:s 2s infinite;}
            @keyframes s{0%,100%{clip-path:polygon(0 0,100% 0,100% 8%,0 8%)}
                        50%{clip-path:polygon(0 0,100% 0,100% 100%,0 100%)}}
            #m{position:absolute;bottom:80px;left:50%;transform:translateX(-50%);
               background:rgba(0,255,0,0.3);color:#0f0;padding:16px 36px;
               border-radius:50px;font-size:1.3em;border:1px solid #0f0;}
        </style>
    </head><body>
        <div id="c">
            <video id="v" autoplay playsinline muted></video>
            <div id="box"></div>
            <div id="m">Наведи квадрат на QR-код</div>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/jsqr@1.4.0/dist/jsQR.min.js"></script>
        <script>
        navigator.mediaDevices.getUserMedia({video:{facingMode:"environment"}})
        .then(s=>{document.getElementById('v').srcObject=s;document.getElementById('v').play();
            const c=document.createElement('canvas'); const x=c.getContext('2d');
            const t=()=>{if(document.getElementById('v').readyState===4){
                c.width=v.videoWidth; c.height=v.videoHeight; x.drawImage(v,0,0);
                const code=jsQR(x.getImageData(0,0,c.width,c.height).data,c.width,c.height);
                if(code && window.scanned!==true){
                    window.scanned=true;
                    document.getElementById('m').innerHTML="Отметка принята!";
                    document.getElementById('m').style.background="rgba(0,255,0,0.9)";
                    fetch("https://schoolqr.ru/mark?qr="+encodeURIComponent(code.data));
                    setTimeout(()=>location.href="tg://resolve?domain=Teztmbot",1500);
                }
            }requestAnimationFrame(t);}; t();
        })
        .catch(()=>{document.getElementById('m').innerText="Разреши камеру";});
        </script>
    </body>
    html>
    """)
# ПРИЁМ ОТМЕТКИ
@app.get("/mark")
async def mark(qr: str):
    class_name = qr.strip().upper()
    database_manager.record_attendance(
        telegram_id=0,  # можно потом добавить initData
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

