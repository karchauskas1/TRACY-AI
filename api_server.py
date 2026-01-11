"""
Простой API сервер для Render.com
Использует существующий код из http_server.py
"""
import os
import sys
import logging
import asyncio
import threading
from aiohttp import web

# Добавляем текущий каталог в Python path для поиска модулей
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from http_server import create_app, set_database
from database import Database
from bot import main as start_bot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация БД
db = Database()
set_database(db)

# Создаем приложение
app = create_app()

def run_bot():
    """Функция для запуска бота в отдельном потоке."""
    try:
        logger.info("🤖 Запуск Telegram бота в фоновом режиме...")
        start_bot()
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске бота: {e}", exc_info=True)

if __name__ == '__main__':
    # Запускаем бота в фоновом потоке
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Получаем PORT из переменных окружения, обрабатываем пустую строку
    port_str = os.getenv('PORT', '8080')
    try:
        port = int(port_str) if port_str else 8080
    except ValueError:
        port = 8080
        logger.warning(f"⚠️ Неверное значение PORT: '{port_str}', используем 8080")
    
    logger.info(f"🚀 Запуск API сервера на порту {port}")
    web.run_app(app, port=port, host='0.0.0.0')

