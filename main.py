import asyncio
import signal
import sys
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import os

# --------------------- Создаём app ПЕРВЫМ! ---------------------
app = FastAPI(title="SYSTEMA CONTROLA POSESHCHAEMOSTI")

# Монтируем статику только после создания app
app.mount("/static", StaticFiles(directory="static", html=True), name="static")

# Для шаблонов (если будут)
templates = Jinja2Templates(directory="templates")

# --------------------- Импортируем сервер ПОСЛЕ app ---------------------
from webhook_server import webhook_server
from logging_config import logger

# --------------------- Система ---------------------
class AttendanceSystem:
    def __init__(self):
        self.is_running = False
        logger.info("Attendance System initialized")

    async def start(self):
        if self.is_running:
            logger.warning("System is already running")
            return

        self.is_running = True
        logger.info("Starting Attendance System...")

        # Обработка сигналов
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, self._signal_handler)

        try:
            await webhook_server.start()
            logger.info("Webhook server started successfully")
        except Exception as e:
            logger.error(f"Failed to start webhook server: {e}")
            self.is_running = False
            raise

    def _signal_handler(self, signum, frame):
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.is_running = False
        asyncio.create_task(self.shutdown())

    async def shutdown(self):
        await webhook_server.stop()
        logger.info("System shut down complete")

# --------------------- Роуты ---------------------
@app.get("/")
async def root(request: Request):
    return HTMLResponse("""
    <h1>SYSTEMA CONTROLA POSESHCHAEMOSTI</h1>
    <p>БОТ ЖИВОЙ НА RAILWAY!</p>
    <p><a href="/health">Health Check</a> | Webhook: /webhook/telegram</p>
    """)

@app.get("/health")
async def health():
    return {"status": "OK", "time": datetime.now().isoformat()}

@app.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    update = await request.json()
    logger.info(f"Received update: {update.get('message', {}).get('text', 'no text')}")
    return JSONResponse({"ok": True})

# --------------------- Запуск ---------------------
async def main():
    system = AttendanceSystem()
    
    print("=" * 60)
    print("   SYSTEMA CONTROLA POSESHCHAEMOSTI")
    print("   AI-Powered Attendance System v2.0")
    print("=" * 60)
    print(f"   Запущено: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Локально: http://localhost:{os.getenv('PORT', 8080)}")
    print(f"   Health: /health | Webhook: /webhook/telegram")
    print("=" * 60)

    await system.start()

    # Держим приложение живым
    try:
        while system.is_running:
            await asyncio.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down by user...")
    finally:
        await system.shutdown()

if __name__ == "__main__":
    if sys.version_info < (3, 7):
        print("Ошибка: Требуется Python 3.7+")
        sys.exit(1)

    # Убираем дублирование asyncio.run(main())
    asyncio.run(main())
