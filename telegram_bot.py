# telegram_bot.py — РАБОЧИЙ ССЫЛКА НА СКАНЕР (НЕ Mini App)

import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import F
from datetime import datetime

from database_manager import database_manager
from config import config

logger = logging.getLogger(__name__)

bot = Bot(token=config.telegram.bot_token)
dp = Dispatcher()

# ССЫЛКА НА ОТДЕЛЬНЫЙ СКАНЕР (КАМЕРА РАБОТАЕТ НА 100%)
QR_SCANNER_URL = f"{config.public_url}/scan"

def get_main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Я в классе (QR)", url=QR_SCANNER_URL)],
        [InlineKeyboardButton(text="Статистика", callback_data="stats")],
        [InlineKeyboardButton(text="Помощь", callback_data="help")],
    ])

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    user = message.from_user
    database_manager.register_student(
        telegram_id=user.id,
        first_name=user.first_name or "Ученик",
        last_name=user.last_name or ""
    )
    await message.answer(
        f"Привет, {user.first_name}!\n\n"
        "Нажми кнопку ниже — откроется камера в браузере.\n"
        "Наведи на QR-код в классе — отметка за 1 секунду!",
        reply_markup=get_main_keyboard()
    )

@dp.callback_query(F.data == "stats")
async def stats(call: types.CallbackQuery):
    stats = database_manager.get_attendance_stats()
    await call.message.edit_text(
        f"Статистика за сегодня:\n\n"
        f"Учеников в системе: {stats.get('total_students', 0)}\n"
        f"Отметились: {stats.get('today_attendance', 0)}\n"
        f"Время: {datetime.now().strftime('%H:%M:%S')}",
        reply_markup=get_main_keyboard()
    )
    await call.answer()

@dp.callback_query(F.data == "help")
async def help_cmd(call: types.CallbackQuery):
    await call.message.edit_text(
        "Как пользоваться:\n\n"
        "1. Нажми «Я в классе (QR)»\n"
        "2. Разреши доступ к камере\n"
        "3. Наведи на QR-код в классе\n"
        "4. Готово — ты отмечен!\n\n"
        "Работает на любом телефоне.",
        reply_markup=get_main_keyboard()
    )
    await call.answer()

async def start_bot():
    logger.info("Бот запущен — ссылка на сканер готова")
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(start_bot())
