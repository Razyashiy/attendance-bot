

# telegram_bot.py — ФИНАЛЬНАЯ ВЕРСИЯ

import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import F
from datetime import datetime

from database_manager import database_manager
from config import config

logging.basicConfig(level=logging.INFO)
bot = Bot(token=config.telegram.bot_token)
dp = Dispatcher()

def get_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="Я в классе — сканировать QR",
            url=f"{config.public_url}/scan"      # ← обычная ссылка, НЕ web_app!
        )],
        [InlineKeyboardButton(text="Статистика", callback_data="stats")],
        [InlineKeyboardButton(text="Помощь", callback_data="help")],
    ])

@dp.message(CommandStart())
async def start(message: types.Message):
    user = message.from_user
    database_manager.register_student(
        telegram_id=user.id,
        first_name=user.first_name or "Ученик",
        last_name=user.last_name or ""
    )
    await message.answer(
        "Привет, " + user.first_name + "!\n\n"
        "Нажми кнопку ниже → откроется камера с квадратом.\n"
        "Наведи квадрат на QR-код в классе — отметка за 1 секунду!",
        reply_markup=get_keyboard()
    )

@dp.callback_query(F.data == "stats")
async def stats(call: types.CallbackQuery):
    s = database_manager.get_attendance_stats()
    await call.message.edit_text(
        f"Статистика за сегодня\n\n"
        f"Отметились: {s.get('today_attendance', 0)}\n"
        f"Всего учеников: {s.get('total_students', 0)}\n\n"
        f"Время: {datetime.now().strftime('%H:%M:%S')}",
        reply_markup=get_keyboard()
    )
    await call.answer()

@dp.callback_query(F.data == "help")
async def help_cmd(call: types.CallbackQuery):
    await call.message.edit_text(
        "Как пользоваться:\n\n"
        "1. Нажми кнопку «Я в классе — сканировать QR»\n"
        "2. Разреши доступ к камере (один раз)\n"
        "3. Наведи зелёный квадрат на QR-код\n"
        "4. Готово — ты отмечен!\n\n"
        "Работает на любом телефоне",
        reply_markup=get_keyboard()
    )
    await call.answer()

async def main():
    logging.info("Бот запущен — посредник готов")
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

