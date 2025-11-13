import sqlite3
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json

from logging_config import logger

class DatabaseManager:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or "data/attendance.db"
        self._init_database()
    
    def _init_database(self):
        """Инициализация базы данных с единой структурой"""
        try:
            db_file = Path(self.db_path)
            db_file.parent.mkdir(parents=True, exist_ok=True)
            
            with sqlite3.connect(self.db_path) as conn:
                # Основная таблица посещений
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS attendance_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        student_name TEXT NOT NULL,
                        action_type TEXT DEFAULT 'ВХОД',
                        timestamp TEXT NOT NULL,
                        method TEXT DEFAULT 'manual',
                        class_name TEXT,
                        telegram_id INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Таблица студентов
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS students (
                        telegram_id INTEGER PRIMARY KEY,
                        first_name TEXT NOT NULL,
                        last_name TEXT,
                        nfc_id TEXT UNIQUE,
                        face_embedding BLOB,
                        registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT TRUE,
                        last_attendance TIMESTAMP,
                        total_entries INTEGER DEFAULT 0
                    )
                ''')
                
                # Таблица системных логов
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS system_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        log_type TEXT NOT NULL,
                        message TEXT,
                        details TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Индексы для производительности
                conn.execute("CREATE INDEX IF NOT EXISTS idx_attendance_telegram_id ON attendance_log (telegram_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_attendance_timestamp ON attendance_log (timestamp)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_students_nfc_id ON students (nfc_id)")
                
                conn.commit()
                logger.info("✅ Database initialized successfully")
                
        except sqlite3.Error as e:
            logger.error(f"❌ Database initialization failed: {e}")
            raise

    def register_student(self, telegram_id: int, first_name: str, last_name: str = "") -> bool:
        """Регистрация студента в системе"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """INSERT OR REPLACE INTO students 
                    (telegram_id, first_name, last_name, is_active) 
                    VALUES (?, ?, ?, ?)""",
                    (telegram_id, first_name, last_name, True)
                )
                conn.commit()
                logger.info(f"✅ Student registered: {first_name} {last_name} (ID: {telegram_id})")
                return True
        except sqlite3.Error as e:
            logger.error(f"❌ Student registration error: {e}")
            return False

    def record_attendance(self, 
                         student_name: str, 
                         method: str = "manual", 
                         class_name: Optional[str] = None, 
                         telegram_id: Optional[int] = None) -> Dict[str, Any]:
        """Запись посещения в систему"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            with sqlite3.connect(self.db_path) as conn:
                # Записываем посещение
                cursor = conn.execute(
                    """INSERT INTO attendance_log 
                    (student_name, action_type, timestamp, method, class_name, telegram_id) 
                    VALUES (?, ?, ?, ?, ?, ?)""",
                    (student_name, "ВХОД", timestamp, method, class_name, telegram_id)
                )
                
                # Обновляем статистику студента если есть telegram_id
                if telegram_id:
                    conn.execute(
                        """UPDATE students 
                        SET last_attendance = CURRENT_TIMESTAMP,
                            total_entries = total_entries + 1
                        WHERE telegram_id = ?""",
                        (telegram_id,)
                    )
                
                conn.commit()
                
                log_id = cursor.lastrowid
                logger.info(f"✅ Attendance recorded: {student_name} via {method} in {class_name}")
                
                return {
                    "status": "success",
                    "log_id": log_id,
                    "student_name": student_name,
                    "timestamp": timestamp,
                    "method": method,
                    "class_name": class_name
                }
                
        except sqlite3.Error as e:
            logger.error(f"❌ Attendance recording error: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

    def check_recent_entry(self, telegram_id: int, class_name: str, minutes: int = 2) -> bool:
        """Проверка наличия недавней записи (анти-спам)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """SELECT 1 FROM attendance_log 
                    WHERE telegram_id = ? AND class_name = ? 
                    AND datetime(timestamp) > datetime('now', ?)""",
                    (telegram_id, class_name, f'-{minutes} minutes')
                )
                result = cursor.fetchone() is not None
                logger.debug(f"Recent entry check: {result} for {telegram_id} in {class_name}")
                return result
                
        except sqlite3.Error as e:
            logger.error(f"❌ Recent entry check error: {e}")
            return False

    def get_student_stats(self, telegram_id: int) -> Dict[str, Any]:
        """Получение статистики студента"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Получаем информацию о студенте
                student_cursor = conn.execute(
                    "SELECT first_name, last_name, total_entries, last_attendance FROM students WHERE telegram_id = ?",
                    (telegram_id,)
                )
                student = student_cursor.fetchone()
                
                if not student:
                    return {
                        'status': 'error', 
                        'message': 'Student not found', 
                        'telegram_id': telegram_id
                    }
                
                first_name, last_name, total_entries, last_attendance = student
                full_name = f"{first_name} {last_name}".strip()
                
                # Статистика посещений
                today_cursor = conn.execute(
                    """SELECT COUNT(*) FROM attendance_log 
                    WHERE telegram_id = ? AND action_type = 'ВХОД' 
                    AND date(timestamp) = date('now')""",
                    (telegram_id,)
                )
                today_entries = today_cursor.fetchone()[0] or 0
                
                month_cursor = conn.execute(
                    """SELECT COUNT(*) FROM attendance_log 
                    WHERE telegram_id = ? AND action_type = 'ВХОД' 
                    AND strftime('%Y-%m', timestamp) = strftime('%Y-%m', 'now')""",
                    (telegram_id,)
                )
                month_entries = month_cursor.fetchone()[0] or 0
                
                # Рейтинг среди всех студентов
                rank_cursor = conn.execute(
                    """SELECT COUNT(*) + 1 FROM students 
                    WHERE total_entries > (SELECT total_entries FROM students WHERE telegram_id = ?)""",
                    (telegram_id,)
                )
                rank = rank_cursor.fetchone()[0] or 1
                
                stats = {
                    'status': 'success',
                    'name': full_name,
                    'telegram_id': telegram_id,
                    'total_entries': total_entries,
                    'today_entries': today_entries,
                    'month_entries': month_entries,
                    'rank': rank,
                    'last_attendance': last_attendance
                }
                
                logger.debug(f"Stats retrieved for {full_name}: {stats}")
                return stats
                
        except sqlite3.Error as e:
            logger.error(f"❌ Student stats error: {e}")
            return {
                'status': 'error',
                'message': 'Database error', 
                'telegram_id': telegram_id
            }

    def get_attendance_stats(self) -> Dict[str, Any]:
        """Получение общей статистики системы"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Основная статистика
                total_students_cursor = conn.execute("SELECT COUNT(*) FROM students")
                total_students = total_students_cursor.fetchone()[0] or 0
                
                active_students_cursor = conn.execute("SELECT COUNT(*) FROM students WHERE is_active = TRUE")
                active_students = active_students_cursor.fetchone()[0] or 0
                
                today_attendance_cursor = conn.execute(
                    """SELECT COUNT(DISTINCT telegram_id) FROM attendance_log 
                    WHERE action_type = 'ВХОД' AND date(timestamp) = date('now')"""
                )
                today_attendance = today_attendance_cursor.fetchone()[0] or 0
                
                total_entries_cursor = conn.execute("SELECT COUNT(*) FROM attendance_log")
                total_entries = total_entries_cursor.fetchone()[0] or 0
                
                # Методы входа
                methods_cursor = conn.execute(
                    "SELECT method, COUNT(*) FROM attendance_log GROUP BY method"
                )
                methods_stats = {row[0]: row[1] for row in methods_cursor.fetchall()}
                
                stats = {
                    'status': 'success',
                    'total_students': total_students,
                    'active_students': active_students,
                    'today_attendance': today_attendance,
                    'total_entries': total_entries,
                    'online_terminals': 3,
                    'methods_stats': methods_stats,
                    'timestamp': datetime.now().isoformat()
                }
                
                logger.info(f"System stats retrieved: {stats}")
                return stats
                
        except sqlite3.Error as e:
            logger.error(f"❌ System stats error: {e}")
            return {
                'status': 'error',
                'message': 'Database error',
                'total_students': 0,
                'active_students': 0, 
                'today_attendance': 0,
                'online_terminals': 0
            }

    def get_recent_activity(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Получение последней активности"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """SELECT student_name, action_type, method, class_name, timestamp 
                    FROM attendance_log 
                    ORDER BY timestamp DESC LIMIT ?""",
                    (limit,)
                )
                
                activity = []
                for row in cursor.fetchall():
                    activity.append({
                        'student_name': row[0],
                        'action_type': row[1],
                        'method': row[2],
                        'class_name': row[3],
                        'timestamp': row[4]
                    })
                
                return activity
                
        except sqlite3.Error as e:
            logger.error(f"❌ Recent activity error: {e}")
            return []

    def test_connection(self) -> bool:
        """Тест подключения к базе данных"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("SELECT 1")
                return True
        except sqlite3.Error as e:
            logger.error(f"❌ Database connection test failed: {e}")
            return False

    def add_system_log(self, log_type: str, message: str, details: Optional[Dict] = None):
        """Добавление системного лога"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO system_logs (log_type, message, details) VALUES (?, ?, ?)",
                    (log_type, message, json.dumps(details) if details else None)
                )
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"❌ System log error: {e}")

# Глобальный экземпляр менеджера базы данных
database_manager = DatabaseManager()
