# telegram_bot.py — ФИНАЛЬНАЯ РАБОЧАЯ ВЕРСИЯ (без WebApp, все кнопки работают)

import logging
from aiogram import Bot, Dispatcher, types, Router
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram import F
from datetime import datetime
import asyncio

from database_manager import database_manager
from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация
bot = Bot(token=config.telegram.bot_token, parse_mode="HTML")
router = Router()
dp = Dispatcher()
dp.include_router(router)

# ГЛАВНАЯ КЛАВИАТУРА — ТОЛЬКО ОБЫЧНЫЕ ССЫЛКИ!
def get_main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="Я в классе — сканировать QR",
            url=f"{config.public_url}/scan"   # ← ЭТО ОБЫЧНАЯ ССЫЛКА!
        )],
        [InlineKeyboardButton(text="Статистика", callback_data="show_stats")],
        [InlineKeyboardButton(text="Помощь", callback_data="show_help")],
    ])

# Команда /start
@router.message(CommandStart())
async def cmd_start(message: types.Message):
    user = message.from_user
    database_manager.register_student(
        telegram_id=user.id,
        first_name=user.first_name or "Ученик",
        last_name=user.last_name or ""
    )
    
    await message.answer(
        f"Привет, <b>{user.first_name}</b>! 🇷🇺\n\n"
        "Нажми кнопку ниже — откроется камера с зелёным квадратом.\n"
        "Наведи на QR-код в классе — отметка мгновенно!",
        reply_markup=get_main_keyboard()
    )

# Статистика — РАБОТАЕТ!
@router.callback_query(F.data == "show_stats")
async def show_stats(call: types.CallbackQuery):
    stats = database_manager.get_attendance_stats()
    text = (
        "Статистика за сегодня\n\n"
        f"Отметились: <b>{stats.get('today_attendance', 0)}</b>\n"
        f"Всего учеников: <b>{stats.get('total_students', 0)}</b>\n\n"
        f"<i>{datetime.now().strftime('%d.%m.%Y %H:%M:%S')}</i>"
    )
    try:
        await call.message.edit_text(text, reply_markup=get_main_keyboard())
    except:
        await call.message.answer(text, reply_markup=get_main_keyboard())
    await call.answer()

# Помощь — РАБОТАЕТ!
@router.callback_query(F.data == "show_help")
async def show_help(call: types.CallbackQuery):
    text = (
        "Как пользоваться:\n\n"
        "1. Нажми «Я в классе — сканировать QR»\n"
        "2. Разреши доступ к камере (один раз)\n"
        "3. Наведи зелёный квадрат на QR-код\n"
        "4. Готово — отметка принята!\n\n"
        "Работает на любом телефоне • Россия 2025"
    )
    try:
        await call.message.edit_text(text, reply_markup=get_main_keyboard())
    except:
        await call.message.answer(text, reply_markup=get_main_keyboard())
    await call.answer()

# Запуск бота
async def start_bot():
    logger.info("Бот запущен — всё работает идеально!")
    await dp.start_polling(bot)

# Запуск (если запускаешь локально)
if __name__ == "__main__":
    asyncio.run(start_bot())

