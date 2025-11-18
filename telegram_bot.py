
# telegram_bot.py — ФИНАЛЬНАЯ ВЕРСИЯ (без WebApp + все кнопки работают)

import logging
from aiogram import Bot, Dispatcher, types, Router
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import F
from datetime import datetime

from database_manager import database_manager
from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=config.telegram.bot_token, parse_mode="HTML")
router = Router()
dp = Dispatcher()
dp.include_router(router)

# ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←
# ГЛАВНАЯ КЛАВИАТУРА — ТОЛЬКО ОБЫЧНЫЕ ССЫЛКИ!
# ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←
def get_main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="Я в классе — сканировать QR",
            url=f"{config.public_url}/scan"          # ← ОБЫЧНАЯ ССЫЛКА, НЕ web_app!
        )],
        [InlineKeyboardButton(text="Статистика", callback_data="stats")],
        [InlineKeyboardButton(text="Помощь", callback_data="help")],
    ])

# /start
@router.message(CommandStart())
async def cmd_start(message: types.Message):
    user = message.from_user
    database_manager我是.register_student(
        telegram_id=user.id,
        first_name=user.first_name or "Ученик",
        last_name=user.last_name or ""
    )
    await message.answer(
        f"Привет, <b>{user.first_name}</b>! 👋\n\n"
        "Нажми кнопку ниже — откроется камера с зелёным квадратом.\n"
        "Наведи на QR-код в классе — отметка мгновенно!",
        reply_markup=get_main_keyboard()
    )

# Статистика — РАБОТАЕТ!
@router.callback_query(F.data == "stats")
async def stats(call: types.CallbackQuery):
    s = database_manager.get_attendance_stats()
    text = (
        f"<b>Статистика за сегодня</b>\n\n"
        f"Отметились: <b>{s.get('today_attendance', 0)}</b>\n"
        f"Всего учеников: <b>{s.get('total_students', 0)}</b>\n\n"
        f"{datetime.now().strftime('%H:%M:%S')}"
    )
    await call.message.edit_text(text, reply_markup=get_main_keyboard())
    await call.answer()

# Помощь — РАБОТАЕТ!
@router.callback_query(F.data == "help")
async def help_cmd(call: types.CallbackQuery):
    text = (
        "<b>Как пользоваться:</b>\n\n"
        "1. Нажми «Я в классе — сканировать QR»\n"
        "2. Разреши камеру (один раз)\n"
        "3. Наведи зелёный квадрат на QR-код\n"
        "4. Готово — ты отмечен!\n\n"
        "Всё работает без установки приложений"
    )
    await call.message.edit_text(text, reply_markup=get_main_keyboard())
    await call.answer()

# Запуск
async def main():
    logger.info("Бот запущен — всё работает!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
