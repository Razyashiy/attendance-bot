

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import F
from datetime import datetime
import logging

from database_manager import database_manager
from config import config

logging.basicConfig(level=logging.INFO)
bot = Bot(token=config.telegram.bot_token)
dp = Dispatcher()

def get_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="Я в классе — сканировать QR",
            switch_inline_query_current_chat="CLASS_"   # ← нативный сканер Telegram
        )],
        [InlineKeyboardButton(text="Статистика", callback_data="stats")],
    ])

@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer(
        "Привет! Нажми кнопку ниже — откроется камера Telegram.\n"
        "Наведи на QR-код в классе — и ты отмечен за полсекунды!",
        reply_markup=get_keyboard()
    )

# Ловим результат нативного сканирования
@dp.chosen_inline_result()
async def qr_scanned(chosen: types.ChosenInlineResult):
    qr_text = chosen.query.strip().upper()
    user = chosen.from_user

    database_manager.record_attendance(
        telegram_id=user.id,
        method="QR",
        class_name=qr_text
    )

    # Админу
    await bot.send_message(
        config.telegram.admin_chat_id,
        f"ВХОД\n"
        f"{user.full_name}\n"
        f"{datetime.now().strftime('%H:%M:%S')} | QR\n"
        f"Класс: {qr_text}"
    )

@dp.callback_query(F.data == "stats")
async def stats(call: types.CallbackQuery):
    s = database_manager.get_attendance_stats()
    await call.message.edit_text(
        f"Сегодня отметились: {s['today_attendance']}\n"
        f"Всего учеников: {s['total_students']}",
        reply_markup=get_keyboard()
    )

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
