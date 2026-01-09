"""Конфигурация приложения."""
import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# OpenRouter
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "gpt-4o-mini")

# Google Calendar
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8080/callback")

# Database
# Поддержка PostgreSQL (приоритет) и SQLite (fallback для совместимости)
DATABASE_URL = os.getenv("DATABASE_URL")  # PostgreSQL: postgresql://user:password@host:port/dbname
DATABASE_PATH = os.getenv("DATABASE_PATH", "./data/tracy.db")  # SQLite fallback
if DATABASE_PATH:
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

# Server
HOST = os.getenv("HOST", "localhost")
PORT = int(os.getenv("PORT", 8080))

# Defaults
DEFAULT_TIMEZONE = os.getenv("DEFAULT_TIMEZONE", "Europe/Moscow")

# Paths
TOKENS_DIR = "./tokens"
os.makedirs(TOKENS_DIR, exist_ok=True)

# Web App
WEB_APP_URL = os.getenv("WEB_APP_URL")  # HTTPS URL веб-приложения (GitHub Pages)

