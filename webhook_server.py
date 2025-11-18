from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from config import config
from database_manager import database_manager
from telegram_bot import bot
from datetime import datetime
import urllib.parse
import json
import logging

logger = logging.getLogger(__name__)

# ← ЭТОТ app — ГЛАВНЫЙ! ОБЯЗАТЕЛЬНО ДОЛЖЕН БЫТЬ!
app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "ok"}

# Принимает и GET, и POST от сканера
@app.post("/record")
@app.get("/record")
async def record_attendance(request: Request):
    try:
        # Получаем QR и данные пользователя
        if request.method == "GET":
            qr = request.query_params.get("qr")
            init_data = request.headers.get("X-Telegram-WebApp-Init-Data", "")
        else:
            body = await request.json()
            qr = body.get("qr")
            init_data = body.get("initData", "")

        if not qr or not init_data:
            return JSONResponse({"status": "error", "message": "no data"}, status_code=400)

        # Расшифровка Telegram initData
        params = dict(urllib.parse.parse_qsl(init_data))
        user_data = json.loads(params.get("user", "{}"))
        user_id = user_data.get("id")
        first_name = user_data.get("first_name", "Ученик")
        last_name = user_data.get("last_name", "")

        if not user_id:
            return JSONResponse({"status": "error", "message": "no user"}, status_code=400)

        # Запись в БД
        class_name = qr.strip().upper()
        database_manager.record_attendance(
            telegram_id=user_id,
            method="QR",
            class_name=class_name
        )

        # Уведомление админу
        full_name = f"{first_name} {last_name}".strip() or "Ученик"
        await bot.send_message(
            chat_id=config.telegram.admin_chat_id,
            text=f"ВХОД\n"
                 f"{full_name}\n"
                 f"{datetime.now().strftime('%H:%M:%S')} | QR\n"
                 f"Класс: {class_name}"
        )

        return JSONResponse({"status": "ok"})

    except Exception as e:
        logger.error(f"Ошибка в /record: {e}")
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
