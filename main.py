import asyncio
import signal
import sys
from datetime import datetime

# ✅ ПРАВИЛЬНЫЙ ИМПОРТ
from webhook_server import webhook_server
from logging_config import logger

class AttendanceSystem:
    def __init__(self):
        self.is_running = False
        logger.info("Attendance System initialized")
    
    async def start(self):
        """Запуск системы"""
        if self.is_running:
            logger.warning("System is already running")
            return
        
        self.is_running = True
        logger.info("🚀 Starting Attendance System...")
        
        # Обработка сигналов завершения
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        try:
            await webhook_server.start()  # ✅ ПРАВИЛЬНОЕ ИМЯ
        except Exception as e:
            logger.error(f"Failed to start system: {e}")
            self.is_running = False
            sys.exit(1)
    
    def _signal_handler(self, signum, frame):
        """Обработчик сигналов завершения"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.is_running = False
        sys.exit(0)

async def main():
    system = AttendanceSystem()
    await system.start()  # Запускает webhook_server.start()
    if __name__ == "__main__":
        asyncio.run(main())
    
    print("=" * 50)
    print("🎓 SYSTEMA CONTROLA POSESHCHAEMOSTI")
    print("🤖 AI-Powered Attendance System")
    print("=" * 50)
    print(f"🚀 Starting at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("📍 Webhook Server: http://localhost:8080")
    print("🔍 Health Check: http://localhost:8080/health")
    print("=" * 50)
    
    try:
        await system.start()
    except KeyboardInterrupt:
        logger.info("System stopped by user")
    except Exception as e:
        logger.error(f"System error: {e}")
    finally:
        system.is_running = False

if __name__ == "__main__":
    # Проверка версии Python
    if sys.version_info < (3, 7):
        print("❌ Error: Python 3.7 or higher is required")
        sys.exit(1)
    
    # Запуск системы
    asyncio.run(main())