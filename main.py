import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram import F

from database_manager import database_manager
from config import config

logger = logging.getLogger(__name__)

# Бот и диспетчер
bot = Bot(token=config.telegram.bot_token)
dp = Dispatcher()

# Клавиатура
def get_main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="Я в классе (QR)",
            web_app=WebAppInfo(url="https://russia-qr-school.netlify.app")
        )],
        [InlineKeyboardButton(text="Статистика", callback_data="stats")],
        [InlineKeyboardButton(text="Помощь", callback_data="help")],
    ])

# /start — РАБОТАЕТ СРАЗУ
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

# Статистика
@dp.callback_query(F.data == "stats")
async def stats(call: types.CallbackQuery):
    stats = database_manager.get_attendance_stats()
    await call.message.edit_text(
        f"Статистика за сегодня:\n"
        f"Всего учеников: {stats.get('total_students', 0)}\n"
        f"Отметились: {stats.get('today_attendance', 0)}\n\n"
        f"Время: {datetime.now().strftime('%H:%M:%S')}",
        reply_markup=get_main_keyboard()
    )
    await call.answer()

# Помощь
@dp.callback_query(F.data == "help")
async def help_cmd(call: types.CallbackQuery):
    await call.message.edit_text(
        "Как пользоваться:\n\n"
        "1. Нажми «Я в классе (QR)»\n"
        "2. Наведи камеру на QR-код в классе\n"
        "3. Готово — ты отмечен!\n\n"
        "Всё работает без установки приложений.",
        reply_markup=get_main_keyboard()
    )
    await call.answer()

# ЭТО САМОЕ ГЛАВНОЕ — ЗАПУСК POLLING
async def start_bot():
    logger.info("Бот запущен и слушает сообщения...")
    await dp.start_polling(bot)

# Если запускаешь локально
if __name__ == "__main__":
    import asyncio
    asyncio.run(start_bot())
