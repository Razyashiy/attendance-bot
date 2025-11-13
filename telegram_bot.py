from database_manager import database_manager
from logging_config import logger
from config import config
from datetime import datetime
from typing import Dict

class TelegramBot:
    def __init__(self):
        self.db = database_manager
        logger.info("TelegramBot инициализирован")

    async def process_message(self, user_id: int, text: str, user_data: dict) -> dict:
        first_name = user_data.get("first_name", "Студент")
        last_name = user_data.get("last_name", "")
        full_name = f"{first_name} {last_name}".strip()

        # Регистрация при первом сообщении
        if not self.db.get_student_by_telegram_id(user_id):
            self.db.register_student(user_id, first_name, last_name)

        if text == "/start":
            return {
                "response": f"Привет, {full_name}!\n\nЯ в классе — отметка\nСтатистика — сколько пришло\nПомощь — инструкция",
                "keyboard": [
                    [{"text": "Я в классе (QR)", "web_app": {"url": f"{config.public_url}/qr_universal"}}],
                    [{"text": "Статистика"}, {"text": "Помощь"}]
                ]
            }

        if text == "Я в классе (QR)":
            self.db.record_attendance(user_id, "QR")
            await self._send_admin(f"ВХОД\n{full_name}\n{datetime.now().strftime('%H:%M:%S')} | QR")
            return {"response": f"Отметка принята!\n{datetime.now().strftime('%H:%M:%S')}\nСпасибо, {first_name}!"}

        if text == "Статистика":
            stats = self.db.get_attendance_stats()
            return {"response": f"Статистика:\nВсего: {stats['total_students']}\nСегодня: {stats['today_attendance']}"}

        if text == "Помощь":
            return {"response": "Наведи камеру на QR в классе → отметка за 1 сек!\n\nКоманды:\n/start — главное меню\n/my — твоя посещаемость"}

        return {"response": "Нажми кнопку ниже или /start"}

    async def _send_admin(self, text: str):
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                url = f"https://api.telegram.org/bot{config.telegram.bot_token}/sendMessage"
                await session.post(url, json={"chat_id": config.telegram.admin_chat_id, "text": text})
        except:
            pass

telegram_bot = TelegramBot()
