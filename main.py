import asyncio
import signal
import sys
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
import uvicorn
import os

# Импортируем после app
from webhook_server import webhook_server
from logging_config import logger

app = FastAPI(title="СИСТЕМА КОНТРОЛЯ ПОСЕЩАЕМОСТИ")

class AttendanceSystem:
    def __init__(self):
        self.is_running = False
        logger.info("Attendance System initialized")

    async def start(self):
        if self.is_running:
            return
        self.is_running = True
        logger.info("Starting system...")

        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, self._signal_handler)

        try:
            await webhook_server.start()
            logger.info("Webhook server started")
        except Exception as e:
            logger.error(f"Start failed: {e}")
            self.is_running = False
            raise

    def _signal_handler(self, signum, frame):
        logger.info(f"Signal {signum} → shutdown")
        self.is_running = False
        asyncio.create_task(self.shutdown())

    async def shutdown(self):
        await webhook_server.stop()
        logger.info("Shutdown complete")

# ГЛАВНАЯ СТРАНИЦА — КРАСИВАЯ, ЗЕЛЁНАЯ, БЕЗ static
@app.get("/")
async def root():
    return HTMLResponse("""
    <html>
        <head>
            <title>СИСТЕМА КОНТРОЛЯ ПОСЕЩАЕМОСТИ</title>
            <meta charset="utf-8">
            <style>
                body {font-family: Arial; text-align: center; margin-top: 10%; background: #000; color: #0f0;}
                h1 {font-size: 3.5em; text-shadow: 0 0 20px #0f0;}
                h2 {font-size: 2em; color: #0f8;}
                a {color: #0f0; font-size: 1.5em; text-decoration: none;}
                a:hover {text-shadow: 0 0 10px #0f0;}
            </style>
        </head>
        <body>
            <h1>СИСТЕМА КОНТРОЛЯ ПОСЕЩАЕМОСТИ</h1>
            <h2>БОТ ЖИВОЙ 24/7 НА RAILWAY</h2>
            <p>Вебхук: <code>/webhook/telegram</code></p>
            <p><a href="/health">Health Check</a></p>
        </body>
    </html>
    """)

@app.get("/health")
async def health():
    return {"status": "OK", "time": datetime.now().isoformat(), "bot": "ЖИВОЙ"}

@app.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    try:
        update = await request.json()
        logger.info(f"Update: {update.get('message', {}).get('text', 'no text')}")
    except:
        logger.error("Bad update")
    return JSONResponse({"ok": True})

async def main():
    system = AttendanceSystem()
    print("="*60)
    print("   СИСТЕМА КОНТРОЛЯ ПОСЕЩАЕМОСТИ v3.0")
    print("   БОТ ЖИВОЙ НА RAILWAY")
    print("="*60)
    print(f"   URL: https://{os.getenv('RAILWAY_STATIC_URL', 'localhost:8080')}")
    print("="*60)

    await system.start()
    try:
        while system.is_running:
            await asyncio.sleep(1)
    finally:
        await system.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
