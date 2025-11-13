import asyncio
import aiohttp
import hashlib
import hmac
import json
from typing import Dict, Any, Optional
from datetime import datetime

from aiogram import Bot, Dispatcher, types, Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from database_manager import database_manager
from config import config

# Настройка логирования
logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self):
        try:
            # Инициализация бота с правильными параметрами
            self.bot = Bot(
                token=config.telegram.bot_token,
                default=DefaultBotProperties(parse_mode=ParseMode.HTML)
            )
            self.dp = Dispatcher()
            self.router = Router()
            self.db = database_manager
            
            self._register_handlers()
            self.dp.include_router(self.router)
            logger.info("✅ Telegram Bot initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Telegram Bot initialization failed: {e}")
            raise

    def _register_handlers(self):
        """Регистрация всех обработчиков"""
        # Обработчики команд
        self.router.message.register(self._start_handler, CommandStart())
        self.router.message.register(self._register_handler, Command("register"))
        self.router.message.register(self._attendance_handler, Command("attendance"))
        self.router.message.register(self._stats_handler, Command("stats"))
        self.router.message.register(self._help_handler, Command("help"))
        self.router.message.register(self._qr_handler, Command("qr"))
        self.router.message.register(self._admin_handler, Command("admin"))
        self.router.message.register(self._status_handler, Command("status"))
        
        # Обработчики callback запросов
        self.router.callback_query.register(self._stats_callback_handler, F.data == "my_stats")
        self.router.callback_query.register(self._nfc_info_handler, F.data == "nfc_info")
        self.router.callback_query.register(self._refresh_handler, F.data == "refresh_stats")

    def _create_main_menu(self) -> InlineKeyboardMarkup:
        """Создание главного меню"""
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📱 ВХОД ПО QR", 
                    web_app=WebAppInfo(url=f"{config.server.public_url}/qr_universal")
                )
            ],
            [
                InlineKeyboardButton(
                    text="📊 МОЯ СТАТИСТИКА", 
                    callback_data="my_stats"
                ),
                InlineKeyboardButton(
                    text="🔄 ОБНОВИТЬ", 
                    callback_data="refresh_stats"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔐 NFC ИНФО", 
                    callback_data="nfc_info"
                )
            ],
            [
                InlineKeyboardButton(
                    text="👨‍🎓 АДМИН ПАНЕЛЬ", 
                    web_app=WebAppInfo(url=f"{config.server.public_url}/admin")
                )
            ]
        ])

    async def _start_handler(self, message: types.Message):
        """Обработчик команды /start"""
        try:
            user_id = message.from_user.id
            first_name = message.from_user.first_name or "Пользователь"
            last_name = message.from_user.last_name or ""
            username = message.from_user.username or ""
            
            logger.info(f"User started bot: {first_name} {last_name} (ID: {user_id}, @{username})")
            
            # Автоматическая регистрация пользователя
            registration_success = self.db.register_student(user_id, first_name, last_name)
            
            # Обработка deep link для QR кодов
            command_parts = message.text.split()
            response_text = ""
            
            if len(command_parts) > 1:
                class_code = command_parts[1].upper().replace("CLASS_", "")
                if class_code in config.qr.supported_classes:
                    await self._process_qr_entry(user_id, f"{first_name} {last_name}", class_code, message)
                    response_text = f"✅ <b>ВХОД В КЛАСС {class_code} ЗАПИСАН!</b>"
                else:
                    response_text = f"❌ <b>Класс {class_code} не поддерживается</b>"
            else:
                if registration_success:
                    response_text = f"""👋 <b>Добро пожаловать, {first_name}!</b>

🎯 <b>СИСТЕМА ПОСЕЩАЕМОСТИ 24/7</b>

✅ Вы успешно зарегистрированы в системе!
📊 Ваш ID: <code>{user_id}</code>

Выберите способ отметки:"""
                else:
                    response_text = f"""👋 <b>Добро пожаловать, {first_name}!</b>

🎯 <b>СИСТЕМА ПОСЕЩАЕМОСТИ 24/7</b>

Выберите способ отметки:"""
            
            await message.answer(response_text, reply_markup=self._create_main_menu())
            
        except Exception as e:
            logger.error(f"Error in start handler: {e}")
            await message.answer("❌ Произошла ошибка. Попробуйте позже.")

    async def _process_qr_entry(self, user_id: int, name: str, class_code: str, message: types.Message):
        """Обработка входа по QR коду"""
        try:
            logger.info(f"Processing QR entry: {name} in {class_code}")
            
            # Проверка анти-спама
            if self.db.check_recent_entry(user_id, class_code):
                await message.answer("⏳ <b>Слишком частый запрос.</b>\nПопробуйте через 2 минуты.")
                return
            
            # Запись посещения
            result = self.db.record_attendance(
                student_name=name,
                method="QR",
                class_name=class_code,
                telegram_id=user_id
            )
            
            if result.get("status") == "success":
                success_message = f"""✅ <b>ПОСЕЩЕНИЕ ЗАПИСАНО!</b>

👤 Студент: <b>{name}</b>
🏫 Класс: <b>{class_code}</b>
⏰ Время: <b>{result.get('timestamp', 'текущее')}</b>
📱 Метод: <b>QR код</b>"""
                
                await message.answer(success_message)
                await self._send_admin_notification(
                    f"📱 <b>QR ВХОД</b>\n"
                    f"👤 {name}\n"
                    f"🏫 {class_code}\n"
                    f"⏰ {result.get('timestamp')}\n"
                    f"🆔 {user_id}"
                )
            else:
                await message.answer("❌ <b>Ошибка записи посещения.</b>\nОбратитесь к администратору.")
                
        except Exception as e:
            logger.error(f"QR entry processing error: {e}")
            await message.answer("❌ <b>Ошибка системы</b> при обработке QR кода.")

    async def _register_handler(self, message: types.Message):
        """Обработчик команды /register"""
        try:
            user_id = message.from_user.id
            first_name = message.from_user.first_name or "Пользователь"
            last_name = message.from_user.last_name or ""
            
            success = self.db.register_student(user_id, first_name, last_name)
            
            if success:
                response_text = f"""✅ <b>РЕГИСТРАЦИЯ УСПЕШНА!</b>

👤 <b>{first_name} {last_name}</b>
🆔 ID: <code>{user_id}</code>
📅 Дата: <b>{datetime.now().strftime('%d.%m.%Y %H:%M')}</b>
✅ Вы зарегистрированы в системе посещаемости"""
            else:
                response_text = "❌ <b>Ошибка регистрации</b>\nПопробуйте позже или обратитесь к администратору."
            
            await message.answer(response_text, reply_markup=self._create_main_menu())
            
        except Exception as e:
            logger.error(f"Registration error: {e}")
            await message.answer("❌ <b>Ошибка при регистрации.</b>")

    async def _attendance_handler(self, message: types.Message):
        """Обработчик команды /attendance"""
        try:
            user_id = message.from_user.id
            stats = self.db.get_student_stats(user_id)
            
            if stats.get("status") != "success":
                await message.answer("❌ <b>Сначала зарегистрируйтесь в системе:</b> /register")
                return
            
            last_attendance = stats.get('last_attendance', 'еще не было')
            if last_attendance and not isinstance(last_attendance, str):
                try:
                    last_attendance = datetime.fromisoformat(last_attendance).strftime('%d.%m.%Y %H:%M')
                except:
                    last_attendance = str(last_attendance)
            
            response_text = f"""📊 <b>ВАША СТАТИСТИКА</b>

👤 Студент: <b>{stats['name']}</b>
🎯 Всего посещений: <b>{stats['total_entries']}</b>
📅 За этот месяц: <b>{stats['month_entries']}</b>
✅ Сегодня: <b>{stats['today_entries']}</b>
🏆 Рейтинг активности: <b>{stats['rank']}</b> место
⏰ Последний вход: <b>{last_attendance}</b>"""
            
            await message.answer(response_text, reply_markup=self._create_main_menu())
            
        except Exception as e:
            logger.error(f"Attendance stats error: {e}")
            await message.answer("❌ <b>Ошибка получения статистики.</b>")

    async def _stats_callback_handler(self, callback: types.CallbackQuery):
        """Обработчик callback для статистики"""
        try:
            user_id = callback.from_user.id
            stats = self.db.get_student_stats(user_id)
            
            if stats.get("status") != "success":
                await callback.answer("❌ Сначала зарегистрируйтесь", show_alert=True)
                return
            
            response_text = f"""📊 <b>ВАША СТАТИСТИКА</b>

👤 {stats['name']}
🎯 Всего: {stats['total_entries']}
📅 Месяц: {stats['month_entries']}
✅ Сегодня: {stats['today_entries']}
🏆 Рейтинг: {stats['rank']}"""
            
            await callback.message.edit_text(response_text, reply_markup=self._create_main_menu())
            await callback.answer("✅ Статистика обновлена")
            
        except Exception as e:
            logger.error(f"Callback stats error: {e}")
            await callback.answer("❌ Ошибка обновления", show_alert=True)

    async def _refresh_handler(self, callback: types.CallbackQuery):
        """Обработчик обновления статистики"""
        try:
            user_id = callback.from_user.id
            stats = self.db.get_student_stats(user_id)
            
            if stats.get("status") != "success":
                await callback.answer("❌ Сначала зарегистрируйтесь", show_alert=True)
                return
            
            response_text = f"""🔄 <b>СТАТИСТИКА ОБНОВЛЕНА</b>

👤 {stats['name']}
🎯 Всего: {stats['total_entries']}
📅 Месяц: {stats['month_entries']}
✅ Сегодня: {stats['today_entries']}
🏆 Рейтинг: {stats['rank']}"""
            
            await callback.message.edit_text(response_text, reply_markup=self._create_main_menu())
            await callback.answer("✅ Данные обновлены")
            
        except Exception as e:
            logger.error(f"Refresh stats error: {e}")
            await callback.answer("❌ Ошибка обновления", show_alert=True)

    async def _nfc_info_handler(self, callback: types.CallbackQuery):
        """Обработчик callback для NFC информации"""
        try:
            response_text = """🔐 <b>NFC ВХОД</b>

Для входа через NFC:
1. 📱 Поднесите телефон к NFC считывателю
2. 🔊 Дождитесь звукового сигнала  
3. ✅ Ваше присутствие будет автоматически записано

📍 <b>NFC терминалы расположены:</b>
• 🚪 У входа в каждый класс
• 🏫 В холле учебного корпуса
• 📚 У библиотеки

❓ <b>Проблемы с NFC?</b>
Обратитесь к техническому специалисту."""
            
            await callback.message.answer(response_text)
            await callback.answer()
            
        except Exception as e:
            logger.error(f"NFC info error: {e}")
            await callback.answer("❌ Ошибка загрузки информации", show_alert=True)

    async def _stats_handler(self, message: types.Message):
        """Обработчик команды /stats (общая статистика)"""
        try:
            stats = self.db.get_attendance_stats()
            
            if stats.get("status") != "success":
                await message.answer("❌ <b>Ошибка получения системной статистики</b>")
                return
            
            methods_text = ""
            for method, count in stats.get('methods_stats', {}).items():
                methods_text += f"• {method}: {count}\n"
            
            response_text = f"""📈 <b>СТАТИСТИКА СИСТЕМЫ</b>

👥 Всего студентов: <b>{stats['total_students']}</b>
📊 Активных: <b>{stats['active_students']}</b>
🎯 Сегодня на занятиях: <b>{stats['today_attendance']}</b>
📁 Всего записей: <b>{stats['total_entries']}</b>
🔄 Терминалов онлайн: <b>{stats['online_terminals']}</b>

<b>Методы входа:</b>
{methods_text or '• Нет данных'}

⏰ Обновлено: <b>{stats.get('timestamp', 'только что')}</b>"""
            
            await message.answer(response_text)
            
        except Exception as e:
            logger.error(f"System stats error: {e}")
            await message.answer("❌ <b>Ошибка получения системной статистики.</b>")

    async def _status_handler(self, message: types.Message):
        """Обработчик команды /status"""
        try:
            db_status = "✅ Подключена" if self.db.test_connection() else "❌ Ошибка"
            stats = self.db.get_attendance_stats()
            
            response_text = f"""🖥️ <b>СТАТУС СИСТЕМЫ</b>

📊 База данных: <b>{db_status}</b>
🌐 Окружение: <b>{config.environment}</b>
🔄 Терминалов: <b>{stats.get('online_terminals', 0)}</b>
👤 Пользователей: <b>{stats.get('total_students', 0)}</b>

<b>Версия:</b> {config.version}
<b>Система:</b> {config.system_name}"""
            
            await message.answer(response_text)
            
        except Exception as e:
            logger.error(f"Status handler error: {e}")
            await message.answer("❌ <b>Ошибка проверки статуса</b>")

    async def _help_handler(self, message: types.Message):
        """Обработчик команды /help"""
        response_text = """🆘 <b>СПРАВКА ПО КОМАНДАМ</b>

/start - Главное меню
/register - Регистрация в системе  
/attendance - Моя посещаемость
/stats - Общая статистика
/status - Статус системы
/qr - Получить QR код класса
/admin - Админ панель
/help - Эта справка

<b>СПОСОБЫ ОТМЕТКИ:</b>
📱 QR код - наведите камеру на код в классе
📷 Face ID - посмотрите в камеру терминала  
🔐 NFC - поднесите телефон к считывателю

<b>ПОДДЕРЖКА:</b>
По всем вопросам обращайтесь к администратору системы."""
        
        await message.answer(response_text)

    async def _qr_handler(self, message: types.Message):
        """Обработчик команды /qr"""
        try:
            command_parts = message.text.split()
            if len(command_parts) > 1:
                class_name = command_parts[1].upper()
                if class_name in config.qr.supported_classes:
                    qr_url = f"{config.server.public_url}/qr_class/{class_name}"
                    response_text = f"""📱 <b>QR КОД ДЛЯ КЛАССА {class_name}</b>

🔗 Ссылка для сканирования:
<code>{qr_url}</code>

🌐 Или откройте в браузере:
{qr_url}

📸 <b>Как использовать:</b>
1. Откройте ссылку на телефоне
2. Наведите камеру на QR код в классе
3. Нажмите на уведомление для подтверждения входа"""
                else:
                    supported = ", ".join(config.qr.supported_classes)
                    response_text = f"""❌ <b>Класс {class_name} не поддерживается</b>

📋 <b>Поддерживаемые классы:</b>
{supported}

💡 <b>Пример использования:</b>
<code>/qr 9A</code> - QR код для класса 9А"""
            else:
                supported = ", ".join(config.qr.supported_classes)
                response_text = f"""📱 <b>ГЕНЕРАЦИЯ QR КОДОВ</b>

📋 <b>Поддерживаемые классы:</b>
{supported}

💡 <b>Использование:</b>
<code>/qr 9A</code> - QR код для класса 9А
<code>/qr 10B</code> - QR код для класса 10Б
<code>/qr 11</code> - QR код для класса 11

🎯 <b>Класс по умолчанию:</b> {config.qr.default_class}"""
            
            await message.answer(response_text)
            
        except Exception as e:
            logger.error(f"QR handler error: {e}")
            await message.answer("❌ <b>Ошибка генерации QR кода.</b>")

    async def _admin_handler(self, message: types.Message):
        """Обработчик команды /admin"""
        try:
            admin_url = f"{config.server.public_url}/admin"
            response_text = f"""👨‍💻 <b>АДМИН ПАНЕЛЬ</b>

🔗 Ссылка для доступа:
<a href="{admin_url}">{admin_url}</a>

📊 <b>В админ панели доступно:</b>
• Просмотр всех записей посещений
• Экспорт данных в Excel
• Управление студентами
• Мониторинг статистики в реальном времени
• Настройка системы

⚡ <b>Быстрый доступ:</b>
Нажмите на кнопку «АДМИН ПАНЕЛЬ» в главном меню"""
            
            await message.answer(response_text)
            
        except Exception as e:
            logger.error(f"Admin handler error: {e}")
            await message.answer("❌ <b>Ошибка доступа к админ панели.</b>")

    async def _send_admin_notification(self, text: str):
        """Отправка уведомления администратору"""
        try:
            await self.bot.send_message(
                chat_id=config.telegram.admin_chat_id,
                text=text,
                parse_mode=ParseMode.HTML
            )
            logger.info("✅ Admin notification sent successfully")
        except Exception as e:
            logger.error(f"❌ Failed to send admin notification: {e}")

    async def start_polling(self):
        """Запуск бота в режиме polling"""
        try:
            logger.info("🔄 Starting Telegram bot polling...")
            await self.dp.start_polling(self.bot)
        except Exception as e:
            logger.error(f"❌ Bot polling failed: {e}")
            raise

    async def setup_webhook(self, webhook_url: str):
        """Настройка вебхука"""
        try:
            await self.bot.set_webhook(
                url=webhook_url,
                secret_token=config.telegram.webhook_secret
            )
            logger.info(f"✅ Webhook set up: {webhook_url}")
        except Exception as e:
            logger.error(f"❌ Webhook setup failed: {e}")
            raise

# Глобальный экземпляр бота
telegram_bot = TelegramBot()

