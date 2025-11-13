import sqlite3
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

from logging_config import logger

class DatabaseManager:
    def __init__(self, db_path: str = "data/attendance.db"):
        self.db_path = db_path
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._init_tables()

    def _init_tables(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS students (
                telegram_id INTEGER PRIMARY KEY,
                first_name TEXT NOT NULL,
                last_name TEXT,
                registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                method TEXT NOT NULL,
                terminal_id TEXT
            )
        """)
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_telegram ON attendance (telegram_id)")
        self.conn.commit()
        logger.info("База данных инициализирована")

    def register_student(self, telegram_id: int, first_name: str, last_name: str = "") -> bool:
        try:
            self.conn.execute(
                "INSERT OR REPLACE INTO students (telegram_id, first_name, last_name) VALUES (?, ?, ?)",
                (telegram_id, first_name, last_name)
            )
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка регистрации: {e}")
            return False

    def record_attendance(self, telegram_id: int, method: str = "QR", terminal_id: str = None) -> bool:
        try:
            self.conn.execute(
                "INSERT INTO attendance (telegram_id, method, terminal_id) VALUES (?, ?, ?)",
                (telegram_id, method, terminal_id)
            )
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка записи посещения: {e}")
            return False

    def get_student_by_telegram_id(self, telegram_id: int) -> Dict[str, Any]:
        cursor = self.conn.execute("SELECT * FROM students WHERE telegram_id = ?", (telegram_id,))
        row = cursor.fetchone()
        if row:
            return {"telegram_id": row[0], "first_name": row[1], "last_name": row[2]}
        return {}

    def get_attendance_stats(self) -> Dict[str, Any]:
        total = self.conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        today = self.conn.execute(
            "SELECT COUNT(DISTINCT telegram_id) FROM attendance WHERE date(timestamp) = date('now')"
        ).fetchone()[0]
        return {"total_students": total, "today_attendance": today}

database_manager = DatabaseManager()

