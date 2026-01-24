"""
==============================================================================
COMMANDS.PY - ОБРАБОТЧИКИ КОМАНД TELEGRAM
==============================================================================

Обработчики slash-команд бота:
- /start - начало работы, онбординг
- /menu - главное меню
- /help - справка
- /web - веб-приложение
- /settings - настройки
- /search - поиск событий
- /share - поделиться

ИСПОЛЬЗОВАНИЕ:
    from tracy.handlers.commands import register_command_handlers

    # В main()
    register_command_handlers(application, container)

МИГРАЦИЯ:
    Этот модуль постепенно заменяет команды из bot.py.
    Для обратной совместимости функции могут вызываться напрямую.

==============================================================================
"""
import logging
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
    WebAppInfo
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes
)

if TYPE_CHECKING:
    from tracy.core.container import Container

logger = logging.getLogger(__name__)


# =============================================================================
# Helper Functions
# =============================================================================

def get_reply_keyboard(context: ContextTypes.DEFAULT_TYPE) -> ReplyKeyboardMarkup:
    """
    Получить постоянную клавиатуру в зависимости от режима.

    Args:
        context: Telegram context

    Returns:
        ReplyKeyboardMarkup
    """
    is_meeting_mode = context.user_data.get('waiting_meeting_audio', False)

    if is_meeting_mode:
        keyboard = [
            [KeyboardButton("📅 Планировщик"), KeyboardButton("📋 Меню")]
        ]
    else:
        keyboard = [
            [KeyboardButton("🎤 Резюмирование встреч"), KeyboardButton("📋 Меню")]
        ]

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        is_persistent=True
    )


def get_container(context: ContextTypes.DEFAULT_TYPE) -> Optional['Container']:
    """Получить контейнер из context.bot_data."""
    return context.bot_data.get('container')


# =============================================================================
# Command Handlers
# =============================================================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик команды /start с онбордингом.

    Поддерживает deep links:
    - /start meeting_transcribe - режим расшифровки встреч
    """
    user_id = update.effective_user.id
    container = get_container(context)

    # Получаем DB (из контейнера или fallback)
    if container and container.legacy_db:
        db = container.legacy_db
    else:
        # Fallback для обратной совместимости
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        from database import Database
        db = Database()

    # Создаем пользователя в БД
    db.get_or_create_user(user_id)

    # Проверяем параметр start (для deep links)
    start_param = context.args[0] if context.args else None

    if start_param == "meeting_transcribe":
        # Переходим в режим ожидания аудио для расшифровки встречи
        context.user_data['waiting_meeting_audio'] = True

        reply_keyboard = get_reply_keyboard(context)

        await update.message.reply_text(
            "🎤 Режим работы с записями встреч\n\n"
            "Вы вошли в режим расшифровки встреч. Чтобы продолжить и расшифровать встречу, "
            "отправьте голосовое сообщение или аудиофайл с записью встречи.\n\n"
            "Бот обработает запись, создаст расшифровку с тайм-кодами и структурированное резюме.\n\n",
            reply_markup=reply_keyboard,
            parse_mode="Markdown"
        )
        return

    # Проверяем, есть ли подключенные календари
    connections = db.get_calendar_connections(user_id)
    has_connections = len(connections) > 0

    welcome_message = (
        "👋 Привет! Я TRACY — твой AI-ассистент для управления календарем.\n\n"
        "✨ Я умею:\n"
        "• Создавать события из текста, голоса или фото\n"
        "• Распознавать даты и время естественным языком\n"
        "• Напоминать о важных событиях\n"
        "• Синхронизировать с Google Calendar и iCloud (опционально)\n\n"
        "🚀 Ты можешь пользоваться мной прямо сейчас!\n\n"
        "Все работает без подключения календарей — просто напиши или скажи:\n"
        "• \"Встреча завтра в 15:00\"\n"
        "• \"Напомни про доклад в пятницу\"\n"
        "• \"Уборка в среду утром\"\n\n"
        "📅 Подключение календарей (необязательно):\n"
        "Это функция для удобства — ты сможешь видеть события в своем привычном календаре. "
        "Но бот работает и без подключения! Все события сохраняются, напоминания приходят.\n\n"
    )

    keyboard = []

    if has_connections:
        welcome_message += "✅ Твои календари подключены и синхронизируются!\n\n"
    else:
        welcome_message += (
            "💡 Хочешь синхронизировать с календарем? Это опционально — "
            "можешь подключить позже через /settings\n\n"
        )
        keyboard.append([InlineKeyboardButton(
            "📅 Подключить календарь (опционально)",
            callback_data="settings_google"
        )])

    reply_keyboard = get_reply_keyboard(context)
    inline_markup = InlineKeyboardMarkup(keyboard) if keyboard else None

    await update.message.reply_text(
        welcome_message,
        reply_markup=inline_markup,
        parse_mode="Markdown"
    )

    await update.message.reply_text(
        "💡 Используй кнопки внизу экрана для переключения режима или возврата в меню.",
        reply_markup=reply_keyboard
    )


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /menu - главное меню."""
    is_meeting_mode = context.user_data.get('waiting_meeting_audio', False)

    reply_keyboard = get_reply_keyboard(context)

    keyboard = [
        [InlineKeyboardButton("📋 Список всех событий", callback_data="list_events_all")],
        [InlineKeyboardButton("⚙️ Настройки", callback_data="settings_show")],
        [InlineKeyboardButton("❓ Как пользоваться", callback_data="help_show")],
        [InlineKeyboardButton("💬 Обратная связь", callback_data="feedback_show")]
    ]

    inline_markup = InlineKeyboardMarkup(keyboard)

    mode_text = "🎤 Режим резюмирования встреч" if is_meeting_mode else "📅 Режим планировщика"

    await update.message.reply_text(
        f"📋 Главное меню TRACY\n\n"
        f"Текущий режим: {mode_text}\n\n"
        "Выбери действие:",
        reply_markup=inline_markup,
        parse_mode="Markdown"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help."""
    help_text = """📖 Справка по TRACY

🗓 **Создание событий:**
• "Встреча завтра в 15:00"
• "Созвон с командой в понедельник"
• "Напомни про доклад через час"

🎤 **Голосовые сообщения:**
Просто отправь голосовое — я распознаю текст и создам событие.

📸 **Фото расписания:**
Сфотографируй расписание — я извлеку события.

🔔 **Напоминания:**
По умолчанию напоминаю за 15 минут. Можно настроить в /settings

⚙️ **Команды:**
/start - начало работы
/menu - главное меню
/settings - настройки
/help - эта справка
/web - веб-приложение

💡 **Совет:** Используй кнопки внизу для быстрого переключения режимов!
"""

    reply_keyboard = get_reply_keyboard(context)
    await update.message.reply_text(help_text, reply_markup=reply_keyboard, parse_mode="Markdown")


async def web_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /web - открывает веб-приложение."""
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    import config

    web_url = config.WEB_APP_URL

    if not web_url or not config.is_valid_production_url(web_url):
        await update.message.reply_text(
            "⚠️ Веб-приложение временно недоступно.\n"
            "Пожалуйста, попробуйте позже."
        )
        logger.error(f"❌ WEB_APP_URL не валиден для команды /web: {web_url}")
        return

    # Добавляем cache-busting
    app_version = datetime.now().strftime("%Y%m%d%H%M%S")
    web_url_with_version = f"{web_url}?v={app_version}"

    message_text = (
        "🌐 Веб-приложение TRACY\n\n"
        "Откройте веб-приложение для доступа ко всем функциям:\n"
        "• 💬 Чат с AI-ассистентом\n"
        "• 📅 Календарь событий\n"
        "• 📝 История встреч\n"
        "• ✅ Списки задач\n"
        "• ⚙️ Настройки\n\n"
        "Нажмите кнопку ниже, чтобы открыть приложение."
    )

    keyboard = [[InlineKeyboardButton(
        "🌐 Открыть TRACY",
        web_app=WebAppInfo(url=web_url_with_version)
    )]]

    await update.message.reply_text(
        message_text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /settings - меню настроек."""
    user_id = update.effective_user.id
    container = get_container(context)

    # Получаем DB
    if container and container.legacy_db:
        db = container.legacy_db
    else:
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        from database import Database
        db = Database()

    # Получаем настройки пользователя
    user_settings = db.get_user_settings(user_id)
    connections = db.get_calendar_connections(user_id)

    # Формируем статус
    notifications_status = "✅" if user_settings and user_settings.get('notifications_enabled', True) else "❌"
    reminder_minutes = user_settings.get('default_reminder_minutes', 15) if user_settings else 15

    # Подключенные календари
    calendar_status = []
    for conn in connections:
        provider = conn.get('provider', 'unknown')
        if provider == 'google':
            calendar_status.append("📅 Google Calendar: ✅")
        elif provider == 'icloud':
            calendar_status.append("📅 iCloud: ✅")

    if not calendar_status:
        calendar_status.append("📅 Календари: не подключены")

    settings_text = (
        "⚙️ **Настройки TRACY**\n\n"
        f"🔔 Уведомления: {notifications_status}\n"
        f"⏰ Напоминание по умолчанию: {reminder_minutes} мин\n\n"
        + "\n".join(calendar_status) + "\n\n"
        "Выберите, что хотите настроить:"
    )

    keyboard = [
        [InlineKeyboardButton("📅 Подключить Google Calendar", callback_data="settings_google")],
        [InlineKeyboardButton("📅 Подключить iCloud", callback_data="settings_icloud")],
        [InlineKeyboardButton("🔔 Настройки уведомлений", callback_data="settings_notifications")],
        [InlineKeyboardButton("⏰ Время напоминания", callback_data="settings_reminder_time")],
        [InlineKeyboardButton("🔙 Назад", callback_data="settings_back")]
    ]

    await update.message.reply_text(
        settings_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /search - поиск событий."""
    # Проверяем, есть ли параметр поиска
    search_query = ' '.join(context.args) if context.args else None

    if not search_query:
        await update.message.reply_text(
            "🔍 **Поиск событий**\n\n"
            "Используйте команду с запросом:\n"
            "`/search встреча`\n"
            "`/search доклад`\n\n"
            "Или просто напишите, что ищете, и я помогу найти.",
            parse_mode="Markdown"
        )
        return

    user_id = update.effective_user.id
    container = get_container(context)

    if container and container.legacy_db:
        db = container.legacy_db
    else:
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        from database import Database
        db = Database()

    # Поиск событий (простой поиск по title)
    events = db.get_events(user_id)

    # Фильтруем по запросу
    matching_events = [
        e for e in events
        if search_query.lower() in (e.get('title', '') or '').lower()
    ]

    if not matching_events:
        await update.message.reply_text(
            f"🔍 По запросу \"{search_query}\" ничего не найдено.\n\n"
            "Попробуйте другой запрос или создайте новое событие."
        )
        return

    # Форматируем результаты
    result_text = f"🔍 Найдено событий: {len(matching_events)}\n\n"
    for event in matching_events[:10]:  # Максимум 10
        title = event.get('title', 'Без названия')
        start_time = event.get('start_time')
        if start_time:
            try:
                dt = datetime.fromisoformat(str(start_time).replace('Z', '+00:00'))
                date_str = dt.strftime('%d.%m.%Y %H:%M')
            except:
                date_str = str(start_time)[:16]
        else:
            date_str = "Без даты"

        result_text += f"• {title} — {date_str}\n"

    await update.message.reply_text(result_text)


async def share_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /share - поделиться ботом."""
    share_text = (
        "📤 **Поделиться TRACY**\n\n"
        "Расскажи друзьям о своем AI-ассистенте для календаря!\n\n"
        "🔗 Ссылка на бота:\n"
        "https://t.me/TracyCalendarBot\n\n"
        "✨ TRACY умеет:\n"
        "• Создавать события из текста, голоса и фото\n"
        "• Напоминать о важных делах\n"
        "• Расшифровывать записи встреч\n"
        "• Синхронизироваться с Google и iCloud"
    )

    keyboard = [[InlineKeyboardButton(
        "📤 Поделиться",
        switch_inline_query="Попробуй TRACY — AI-ассистент для календаря!"
    )]]

    await update.message.reply_text(
        share_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


# =============================================================================
# Registration
# =============================================================================

def register_command_handlers(
    application: Application,
    container: Optional['Container'] = None
) -> None:
    """
    Зарегистрировать все command handlers в приложении.

    Args:
        application: Telegram Application
        container: DI Container (опционально)
    """
    # Сохраняем контейнер в bot_data если передан
    if container:
        application.bot_data['container'] = container

    # Регистрируем handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("menu", menu_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("web", web_command))
    application.add_handler(CommandHandler("settings", settings_command))
    application.add_handler(CommandHandler("search", search_command))
    application.add_handler(CommandHandler("share", share_command))

    logger.info("✓ Command handlers зарегистрированы")
