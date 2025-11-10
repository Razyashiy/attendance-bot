from dataclasses import dataclass, field
from typing import Optional

@dataclass
class DatabaseConfig:
    path: str = "data/attendance.db"
    timeout: int = 30
    init_timeout: int = 10
    retry_attempts: int = 3

@dataclass
class ServerConfig:
    host: str = "localhost"
    port: int = 8080
    debug: bool = True
    workers: int = 1
    max_requests: int = 1000
    request_timeout: int = 30

@dataclass
class TelegramConfig:
    webhook_url: str = "http://localhost:8080/webhook/telegram"
    secret_token: str = "8399420502:AAHqJPTmsD0K7r1spXziNOS3JDCjiH5lDkI"  # Замени на реальный!
    max_message_length: int = 4096
    allowed_commands: list = field(default_factory=lambda: ['/start', '/register', '/stats', '/help'])

@dataclass
class SecurityConfig:
    cors_origins: list = field(default_factory=lambda: ["http://localhost:3000"])
    rate_limit_per_minute: int = 10
    max_request_size: int = 1024 * 1024  # 1MB

@dataclass
class SystemConfig:
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    server: ServerConfig = field(default_factory=ServerConfig)
    telegram: TelegramConfig = field(default_factory=TelegramConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    system_name: str = "Attendance Control System"
    version: str = "1.0.0"
    environment: str = "development"
    
    @classmethod
    def load(cls) -> 'SystemConfig':
        return cls()

# Глобальный конфиг
config = SystemConfig.load()