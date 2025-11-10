import sqlite3
import logging
from pathlib import Path
from datetime import datetime, timedelta

from logging_config import logger

class DatabaseManager:
    def __init__(self, db_path: str = "data/attendance.db"):
        self.db_path = db_path
        self._ensure_database()
        self._init_tables()
    
    def _ensure_database(self):
        db_file = Path(self.db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"📁 Database path: {db_file.absolute()}")

    def _init_tables(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS students (
                        telegram_id INTEGER PRIMARY KEY,
                        first_name TEXT NOT NULL,
                        last_name TEXT,
                        nfc_id TEXT UNIQUE,
                        face_embedding BLOB,
                        registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT TRUE
                    )
                ''')
                
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS attendance (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        telegram_id INTEGER,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        method TEXT NOT NULL,
                        terminal_id TEXT,
                        FOREIGN KEY (telegram_id) REFERENCES students (telegram_id)
                    )
                ''')
                
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS webhook_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        event_type TEXT NOT NULL,
                        payload TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        status TEXT
                    )
                ''')
                
                conn.commit()
                logger.info("✅ Database tables initialized")
        except sqlite3.Error as e:
            logger.error(f"❌ Database init error: {e}")
            raise

    # Остальные методы как в SecureDatabase: register_student, record_attendance, get_student_by_telegram_id, get_attendance_stats, test_connection
    # (Я скопировал их из telegram_bot_webhook.py и интегрировал)

    def register_student(self, telegram_id: int, first_name: str, last_name: str = "") -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO students (telegram_id, first_name, last_name) VALUES (?, ?, ?)",
                    (telegram_id, first_name, last_name)
                )
                conn.commit()
                logger.info(f"✅ Student registered: {first_name} {last_name}")
                return True
        except sqlite3.Error as e:
            logger.error(f"❌ Registration error: {e}")
            return False

    def record_attendance(self, telegram_id: int, method: str, terminal_id: str = None) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT is_active FROM students WHERE telegram_id = ?",
                    (telegram_id,)
                )
                result = cursor.fetchone()
                
                if not result or not result[0]:
                    logger.warning(f"⚠️ Inactive student: {telegram_id}")
                    return False
                
                conn.execute(
                    "INSERT INTO attendance (telegram_id, method, terminal_id) VALUES (?, ?, ?)",
                    (telegram_id, method, terminal_id)
                )
                conn.commit()
                logger.info(f"✅ Attendance recorded for {telegram_id}")
                return True
        except sqlite3.Error as e:
            logger.error(f"❌ Attendance error: {e}")
            return False

    # ... (добавь get_student_by_telegram_id, get_attendance_stats из старого)

database_manager = DatabaseManager()