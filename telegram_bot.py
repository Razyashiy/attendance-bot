# telegram_bot.py — СТРЕЛОЧКА КАК В ТОМ РАБОЧЕМ БОТЕ (БЕЗ Mini App!)

import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, types, Router
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram import F

from database_manager import database_manager
from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=config.telegram.bot_token, parse_mode="HTML")
router = Router()
dp = Dispatcher()
dp.include_router(router)

@router.message(CommandStart())
async def start(message: types.Message):
    user = message.from_user
    database_manager.register_student(
        telegram_id=user.id,
        first_name=user.first_name or "Ученик",
        last_name=user.last_name or ""
    )
    
    await message.answer(
        f"Привет, <b>{user.first_name}</b>!\n\n"
        "Нажми кнопку ниже — откроется сканер с зелёным квадратом:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="Я в классе — сканировать QR",
                callback_data="open_scanner"   # ← СТРЕЛОЧКА!
            )],
            [InlineKeyboardButton(text="Статистика", callback_data="stats")],
            [InlineKeyboardButton(text="Помощь", callback_data="help")],
        ])
    )

# ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←
# ВОТ ОНА — СТРЕЛОЧКА ИЗ ПРОШЛОГО БОТА!
# ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←
@router.callback_query(F.data == "open_scanner")
async def open_scanner(call: types.CallbackQuery):
    await call.message.answer()
    await bot.answer_callback_query(
        call.id,
        url="https://qr.school2025.ru"
    )

@router.callback_query(F.data == "stats")
async def stats(call: types.CallbackQuery):
    s = database_manager.get_attendance_stats()
    await call.message.edit_text(
        f"<b>Статистика за сегодня</b>\n\n"
        f"Отметились: <b>{s.get('today_attendance', 0)}</b>\n"
        f"Всего учеников: <b>{s.get('total_students', 0)}</b>\n\n"
        f"{datetime.now().strftime('%H:%M:%S')}",
        reply_markup=call.message.reply_markup
    )
    await call.answer()

@router.callback_query(F.data == "help")
async def help_cmd(call: types.CallbackQuery):
    await call.message.edit_text(
        "<b>Как пользоваться</b>\n\n"
        "1. Нажми кнопку «Я в классе — сканировать QR»\n"
        "2. Разреши камеру\n"
        "3. Наведи квадрат на QR-код\n"
        "4. Готово!",
        reply_markup=call.message.reply_markup
    )
    await call.answer()

async def main():
    logger.info("Бот запущен — стрелочка как в прошлом боте")
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

