import asyncio
import aiohttp
import hashlib
import hmac
import json
from typing import Dict

from database_manager import database_manager
from logging_config import logger
from config import config

class TelegramBot:
    def __init__(self):
        self.db = database_manager
        self.user_sessions = {}
        self.webhook_url = config.telegram.webhook_url  # Для отправки уведомлений
        self.secret_token = config.telegram.secret_token
        logger.info("✅ Telegram Bot initialized")
    
    async def process_message(self, user_id: int, message_text: str, user_data: Dict) -> Dict:
        try:
            if message_text.startswith('/'):
                return await self._handle_command(user_id, message_text, user_data)
            else:
                return self._handle_text_message(user_id, message_text, user_data)
        except Exception as e:
            logger.error(f"❌ Message error: {e}")
            return {'status': 'error', 'response': 'Ошибка обработки.'}
    
    async def _handle_command(self, user_id: int, command: str, user_data: Dict) -> Dict:
        command = command.lower().strip()
        first_name = user_data.get('first_name', 'User')
        
        if command == '/start':
            return await self._handle_start(user_id, first_name)
        elif command == '/register':
            return await self._handle_register(user_id, first_name, user_data.get('last_name', ''))
        elif command == '/attendance':
            return await self._handle_attendance(user_id)
        elif command == '/stats':
            return await self._handle_stats(user_id)
        elif command == '/help':
            return self._handle_help()
        else:
            return {'status': 'unknown', 'response': 'Неизвестная команда. /help для помощи.'}
    
    # Методы _handle_start, _handle_register, _handle_attendance, _handle_stats, _handle_help
    # (Скопировал из telegram_bot_webhook.py и старого, объединил)

    async def _handle_start(self, user_id: int, first_name: str) -> Dict:
        response = f"👋 Добро пожаловать, {first_name}! Команды: /register, /attendance, /stats, /help"
        await self._send_webhook('user_start', {'user_id': user_id})
        return {'status': 'success', 'response': response}

    # ... (аналогично для других)

    async def _send_webhook(self, event_type: str, payload: Dict) -> bool:
        # Логика из WebhookManager
        try:
            headers = {'Content-Type': 'application/json'}
            if self.secret_token:
                signature = hmac.new(self.secret_token.encode(), json.dumps(payload).encode(), hashlib.sha256).hexdigest()
                headers['X-Signature'] = signature
            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=payload, headers=headers, timeout=10) as resp:
                    return resp.status == 200
        except Exception as e:
            logger.error(f"❌ Webhook error: {e}")
            return False

telegram_bot = TelegramBot()