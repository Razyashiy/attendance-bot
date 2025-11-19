import logging
from datetime import datetime                     # ← ДОБАВИЛ!
from aiogram import Bot, Dispatcher, types, Router
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import F

from database_manager import database_manager
from config import config

logging.basicConfig(level=logging.INFO)

bot = Bot(token=config.telegram.bot_token, parse_mode="HTML")
router = Router()
dp = Dispatcher()
dp.include_router(router)

def get_main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
    text="Я в классе — сканировать QR",
    url="https://qr.school2025.ru"      # ← 100% чистый домен, без кэша
)],
        [InlineKeyboardButton(text="Статистика", callback_data="stats")],
        [InlineKeyboardButton(text="Помощь", callback_data="help")],
    ])

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
        "Нажми кнопку ниже — откроется сканер в браузере.\n"
        "Наведи квадрат на QR-код — отметка мгновенно!",
        reply_markup=get_main_keyboard()
    )

@router.callback_query(F.data == "stats")
async def stats(call: types.CallbackQuery):
    s = database_manager.get_attendance_stats()
    await call.message.edit_text(
        f"<b>Статистика за сегодня</b>\n\n"
        f"Отметились: <b>{s.get('today_attendance', 0)}</b>\n"
        f"Всего учеников: <b>{s.get('total_students', 0)}</b>\n\n"
        f"<i>{datetime.now().strftime('%H:%M:%S')}</i>",
        reply_markup=get_main_keyboard()
    )
    await call.answer()

@router.callback_query(F.data == "help")
async def help_cmd(call: types.CallbackQuery):
    await call.message.edit_text(
        "<b>Как пользоваться</b>\n\n"
        "1. Нажми «Я в классе — сканировать QR»\n"
        "2. Разреши камеру (один раз)\n"
        "3. Наведи зелёный квадрат на QR-код\n"
        "4. Готово!\n\n"
        "Работает на любом телефоне",
        reply_markup=get_main_keyboard()
    )
    await call.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())


