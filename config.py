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
# Telegram Mini App ВСЕГДА использует production domain.
# Preview deployments ЗАПРЕЩЕНЫ.
# 
# Production URL должен быть явно указан в .env:
# WEB_APP_URL=https://tracy-ai.vercel.app
#
# НЕ используйте:
# - preview URLs (содержат -projects.vercel.app или hash)
# - branch deployments
# - автоматическую генерацию URL
WEB_APP_URL = os.getenv("WEB_APP_URL")  # HTTPS URL веб-приложения (только production)

# Разрешенные production домены (allowlist)
ALLOWED_PRODUCTION_DOMAINS = [
    "tracy-ai.vercel.app",  # Основной production domain
    # Добавьте другие production домены здесь, если нужно
]

def is_valid_production_url(url: str) -> bool:
    """
    Валидация production URL для Telegram Mini App.
    
    Запрещает:
    - preview URLs (содержат -projects.vercel.app)
    - URLs с hash/slug (например, tracy-abc123.vercel.app)
    - localhost
    - не-HTTPS URLs
    
    Разрешает только:
    - Явные production домены из allowlist
    """
    if not url:
        return False
    
    # Должен быть HTTPS
    if not url.startswith("https://"):
        return False
    
    # Запрещаем localhost
    if "localhost" in url.lower():
        return False
    
    # Запрещаем preview URLs (содержат -projects.vercel.app)
    if "-projects.vercel.app" in url:
        return False
    
    # Запрещаем URLs с hash/slug (например, tracy-abc123.vercel.app)
    # Проверяем, что это не preview deployment
    import re
    # Preview deployments обычно имеют формат: project-hash-username.vercel.app
    # Production: project.vercel.app или custom domain
    if re.search(r'-[a-z0-9]{8,}-[a-z0-9-]+\.vercel\.app', url):
        return False
    
    # Проверяем allowlist production доменов
    for domain in ALLOWED_PRODUCTION_DOMAINS:
        if domain in url:
            return True
    
    # Если URL не в allowlist, но это явный production domain (без hash)
    # Разрешаем только если это vercel.app без hash или custom domain
    if ".vercel.app" in url:
        # Проверяем, что это не preview (нет hash в поддомене)
        parts = url.replace("https://", "").split(".")[0]
        # Если поддомен содержит только буквы, цифры и дефисы (но не длинный hash)
        if len(parts.split("-")) <= 2:  # project или project-username, но не project-hash-username
            return True
    
    return False

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

