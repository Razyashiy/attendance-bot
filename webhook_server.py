from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from config import config
from logging_config import logger

app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "ok", "bot": "aiogram running", "time": "November 13, 2025"}

@app.get("/qr_universal")
async def qr_universal():
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head><meta name="viewport" content="width=device-width,initial-scale=1"></head>
    <body style="margin:0;background:#000;">
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
    if(code && code.data.includes('t.me')){
        document.getElementById('s').innerText='Отметка принята!';
        fetch('/record?qr='+encodeURIComponent(code.data));
        setTimeout(()=>location.reload(),1500);
    }},400);});
    </script>
    </body>
    </html>
    """)

@app.get("/record")
async def record(qr: str):
    return {"status": "ok", "qr": qr}
