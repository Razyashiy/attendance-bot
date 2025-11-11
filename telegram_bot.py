from database_manager import database_manager
from logging_config import logger
from config import config
from typing import Dict

class TelegramBot:
    def __init__(self):
        self.db = database_manager

    async def process_message(self, user_id: int, text: str, user_data: dict) -> dict:
        first_name = user_data.get("first_name", "Студент")
        last_name = user_data.get("last_name", "")
        full_name = f"{first_name} {last_name}".strip()

        if text == "/start":
            self.db.register_student(user_id, first_name, last_name)
            return {"response": f"Привет, {full_name}!\nТы зарегистрирован в системе посещаемости!"}

        if text == "/stats":
            stats = self.db.get_attendance_stats()
            return {"response": f"Статистика системы:\nВсего студентов: {stats['total_students']}\nСегодня на уроке: {stats['today_attendance']}"}

        if text.startswith("/qr"):
            class_name = text.split()[1].upper() if len(text.split()) > 1 else "9A"
            qr_url = f"{config.public_url}/qr_scan?class={class_name}"
            return {"response": f"QR-код для класса {class_name}:\n{qr_url}"}

        return {"response": "Доступные команды:\n/start — регистрация\n/stats — статистика\n/qr 9A — QR-код класса"}

telegram_bot = TelegramBot()
