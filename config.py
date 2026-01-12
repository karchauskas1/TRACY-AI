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
GOOGLE_CLIENT_ID = (os.getenv("GOOGLE_CLIENT_ID") or "").strip()
GOOGLE_CLIENT_SECRET = (os.getenv("GOOGLE_CLIENT_SECRET") or "").strip()
# Для production используем главную страницу веб-приложения
# Пользователь скопирует URL из адресной строки (с параметром code) и отправит боту
GOOGLE_REDIRECT_URI = (os.getenv("GOOGLE_REDIRECT_URI") or "https://karchauskas1.github.io/TRACY-AI/").strip()

# Database
# Поддержка PostgreSQL (приоритет) и SQLite (fallback для совместимости)
DATABASE_URL = os.getenv("DATABASE_URL")  # PostgreSQL: postgresql://user:password@host:port/dbname
DATABASE_PATH = os.getenv("DATABASE_PATH", "./data/tracy.db")  # SQLite fallback
if DATABASE_PATH:
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

# Server
HOST = os.getenv("HOST", "localhost")
# Обрабатываем PORT, учитывая что он может быть пустой строкой
_port_str = os.getenv("PORT", "8080")
try:
    PORT = int(_port_str) if _port_str else 8080
except ValueError:
    PORT = 8080

# Defaults
DEFAULT_TIMEZONE = os.getenv("DEFAULT_TIMEZONE", "Europe/Moscow")

# Paths
TOKENS_DIR = "./tokens"
os.makedirs(TOKENS_DIR, exist_ok=True)

# Web App
WEB_APP_URL = os.getenv("WEB_APP_URL")  # HTTPS URL веб-приложения (GitHub Pages)

# Feedback Service (Google Sheets/Drive)
FEEDBACK_SPREADSHEET_ID = os.getenv("FEEDBACK_SPREADSHEET_ID", "")
FEEDBACK_SHEET_MAPPING = {}  # Маппинг user_id -> название листа
# Парсим из переменной окружения (формат: "user_id1:лист1,user_id2:лист2")
env_feedback_mapping = os.getenv("FEEDBACK_SHEET_MAPPING", "")
if env_feedback_mapping:
    for pair in env_feedback_mapping.split(","):
        if ":" in pair:
            user_id_str, sheet_name = pair.split(":", 1)
            try:
                FEEDBACK_SHEET_MAPPING[int(user_id_str.strip())] = sheet_name.strip()
            except ValueError:
                pass  # Игнорируем неверные форматы

# Apps Script Webhook для обратной связи (альтернативный способ записи)
FEEDBACK_APPS_SCRIPT_URL = os.getenv(
    "FEEDBACK_APPS_SCRIPT_URL",
    "https://script.google.com/macros/s/AKfycbwjG0PJw_VRuWY2RQsc6jneSwOETURVv_3g3ROq5rp3e6kd5siC-cXUkqAmmcrMqCO8YA/exec"
)

# Супер-пользователь (может просматривать всю обратную связь)
SUPER_USER_ID = int(os.getenv("SUPER_USER_ID", "308477378"))

