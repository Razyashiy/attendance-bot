from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import F
from database_manager import database_manager
from logging_config import logger
from config import config
from datetime import datetime

bot = Bot(token=config.telegram.bot_token)
dp = Dispatcher()

@dp.message(CommandStart())
async def start(message: types.Message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name or "Студент"
    last_name = message.from_user.last_name or ""

    # Регистрация
    cursor = database_manager.conn.execute("SELECT telegram_id FROM students WHERE telegram_id = ?", (user_id,))
    if not cursor.fetchone():
        database_manager.register_student(user_id, first_name, last_name)

    # КНОПКА С ССЫЛКОЙ НА СКАНЕР (НЕ MINI APP!)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📱 Я в классе (QR)", url=f"{config.public_url}/scan")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton(text="❓ Помощь", callback_data="help")],
    ])

    await message.answer(
        f"Привет, {first_name}!\nТы зарегистрирован в системе посещаемости!",
        reply_markup=kb
    )

@dp.callback_query(F.data == "stats")
async def stats(call: types.CallbackQuery):
    stats = database_manager.get_attendance_stats()
    await call.message.edit_text(
        f"Статистика:\nВсего студентов: {stats['total_students']}\nСегодня на уроке: {stats['today_attendance']}",
        reply_markup=call.message.reply_markup
    )
    await call.answer()

@dp.callback_query(F.data == "help")
async def help_cmd(call: types.CallbackQuery):
    await call.message.edit_text(
        "📱 Нажми кнопку «Я в классе (QR)» — откроется камера в браузере.\nНаведи на QR в классе → отметка за 1 секунду!",
        reply_markup=call.message.reply_markup
    )
    await call.answer()

async def start_polling():
    logger.info("Бот запущен в polling-режиме")
    await dp.start_polling(bot)



