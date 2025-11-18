import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram import F

from database_manager import database_manager
from config import config

logger = logging.getLogger(__name__)

bot = Bot(token=config.telegram.bot_token)
dp = Dispatcher()

# ГЛАВНОЕ МЕНЮ — РАБОТАЕТ СРАЗУ
def get_main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Я в классе (QR)",
                web_app=WebAppInfo(url="https://russia-qr-school.netlify.app")
            )
        ],
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
        "Нажми кнопку ниже и отсканируй QR-код в классе — отметка придёт мгновенно!",
        reply_markup=get_main_keyboard()
    )

@dp.callback_query(F.data == "stats")
async def stats(call: types.CallbackQuery):
    stats = database_manager.get_attendance_stats()
    await call.message.edit_text(
        f"Статистика за сегодня:\n"
        f"Всего учеников: {stats['total_students']}\n"
        f"Отметились: {stats['today_attendance']}\n\n"
        f"Последняя активность: {stats.get('last_entry', '—')}",
        reply_markup=get_main_keyboard()
    )
    await call.answer()

@dp.callback_query(F.data == "help")
async def help_cmd(call: types.CallbackQuery):
    await call.message.edit_text(
        "Как пользоваться:\n\n"
        "1. Нажми «Я в классе (QR)»\n"
        "2. Наведи камеру на QR-код в классе\n"
        "3. Готово! Ты отмечен\n\n"
        "Всё работает без установки приложений!",
        reply_markup=get_main_keyboard()
    )
    await call.answer()

async def start_bot():
    logger.info("Запуск бота в режиме polling...")
    await dp.start_polling(bot)

