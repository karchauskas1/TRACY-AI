"""
API сервер и Telegram бот для Render.com
Запускает бота в основном потоке и HTTP сервер в фоновом.
"""
import os
import sys
import logging

# Добавляем текущий каталог в Python path для поиска модулей
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot import main as start_bot

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    logger.info("🚀 Запуск единого процесса (Бот + API) для Render.com")
    try:
        # bot.main() сам запускает HTTP сервер в фоновом потоке 
        # и оставляет основной поток для Telegram бота (run_polling)
        start_bot()
    except Exception as e:
        logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}", exc_info=True)
        sys.exit(1)
