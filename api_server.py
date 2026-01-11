"""
Простой API сервер для Render.com
Использует существующий код из http_server.py
"""
import os
import sys
import logging
import asyncio
from aiohttp import web

# Добавляем текущий каталог в Python path для поиска модулей
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from http_server import create_app, set_database
from database import Database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация БД
db = Database()
set_database(db)

# Создаем приложение
app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    logger.info(f"🚀 Запуск API сервера на порту {port}")
    web.run_app(app, port=port, host='0.0.0.0')

