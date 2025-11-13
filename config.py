from dataclasses import dataclass, field
import os
from typing import List

@dataclass
class TelegramConfig:
    bot_token: str = field(default_factory=lambda: os.getenv("BOT_TOKEN"))
    webhook_secret: str = os.getenv("WEBHOOK_SECRET", "super_secret_2025")
    admin_chat_id: int = int(os.getenv("ADMIN_CHAT_ID", "0"))

    def __post_init__(self):
        if not self.bot_token:
            raise ValueError("BOT_TOKEN обязателен в .env!")
        if self.admin_chat_id == 0:
            raise ValueError("ADMIN_CHAT_ID обязателен в .env!")

@dataclass
class SystemConfig:
    telegram: TelegramConfig = field(default_factory=TelegramConfig)
    public_url: str = os.getenv("PUBLIC_URL", "http://localhost:8080")

config = SystemConfig()
