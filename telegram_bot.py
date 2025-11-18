import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram import F
from datetime import datetime

from database_manager import database_manager
from config import config

logger = logging.getLogger(__name__)

bot = Bot(token=config.telegram.bot_token)
dp = Dispatcher()

# ТВОЯ РАБОЧАЯ ССЫЛКА — 100% РАБОТАЕТ
QR_SCANNER_URL = "https://tgqr1.netlify.app/?webhook=https://attendance-bot.up.railway.app/record"

def get_main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="Я в классе (QR)",
            web_app=WebAppInfo(url=QR_SCANNER_URL)
        )],
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
        "Нажми кнопку ниже — откроется камера.\n"
        "Наведи на QR-код в классе — и ты отмечен за 1 секунду!",
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
        "2. Разреши камеру (один раз)\n"
        "3. Наведи на QR-код\n"
        "4. Готово!\n\n"
        "Работает на любом телефоне.",
        reply_markup=get_main_keyboard()
    )
    await call.answer()

async def start_bot():
    logger.info("Бот запущен — всё работает")
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(start_bot())


