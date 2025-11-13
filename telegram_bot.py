import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram import F
from database_manager import database_manager
from logging_config import logger
from config import config

bot = Bot(token=config.telegram.bot_token)
dp = Dispatcher()

@dp.message(CommandStart())
async def start(message: types.Message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name or "Студент"
    last_name = message.from_user.last_name or ""
    
    database_manager.register_student(user_id, first_name, last_name)
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Я в классе (QR)", web_app=WebAppInfo(url=f"{config.public_url}/qr_universal"))],
        [InlineKeyboardButton(text="Статистика", callback_data="stats")],
        [InlineKeyboardButton(text="Помощь", callback_data="help")],
    ])
    
    await message.answer(
        f"Привет, {first_name}!\nТы зарегистрирован!\n\nВыбери действие:",
        reply_markup=kb
    )

@dp.callback_query(F.data == "stats")
async def stats(call: types.CallbackQuery):
    user_id = call.from_user.id
    stats = database_manager.get_attendance_stats()
    await call.message.edit_text(
        f"Статистика системы:\nВсего студентов: {stats['total_students']}\nСегодня: {stats['today_attendance']}",
        reply_markup=call.message.reply_markup
    )
    await call.answer()

@dp.callback_query(F.data == "help")
async def help(call: types.CallbackQuery):
    await call.message.edit_text(
        "/start — главное меню\n/stats — статистика\nЯ в классе — отметка по QR",
        reply_markup=call.message.reply_markup
    )
    await call.answer()

async def start_bot():
    logger.info("Бот запущен в polling режиме")
    await dp.start_polling(bot)
