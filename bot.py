"""Основной модуль Telegram бота TRACY."""
import logging
import asyncio
import os
from datetime import datetime
from typing import List, Dict, Union
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, MenuButtonWebApp, BotCommand, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)
from database import Database
from media_processor import MediaProcessor
from nlp_extractor import NLPExtractor
from decision_engine import DecisionEngine
from calendar_google import GoogleCalendar
from meeting_processor import MeetingProcessor
from reminder_scheduler import ReminderScheduler
import config

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация компонентов
db = Database()
media_processor = MediaProcessor()
nlp_extractor = NLPExtractor()
meeting_processor = MeetingProcessor(nlp_extractor.client)
reminder_scheduler = None  # Будет инициализирован в main()
decision_engine = None  # Будет инициализирован в main() после scheduler


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start с онбордингом."""
    user_id = update.effective_user.id
    
    # Создаем пользователя в БД
    db.get_or_create_user(user_id)
    
    # Проверяем параметр start (для deep links из веб-приложения)
    start_param = context.args[0] if context.args else None
    
    if start_param == "meeting_transcribe":
        # Переходим в режим ожидания аудио для расшифровки встречи
        context.user_data['waiting_meeting_audio'] = True
        
        # Устанавливаем постоянную клавиатуру для режима расшифровки
        reply_keyboard = get_reply_keyboard(context)
        
        await update.message.reply_text(
            "🎤 **Режим работы с записями встреч**\n\n"
            "Вы вошли в режим расшифровки встреч. Чтобы продолжить и расшифровать встречу, отправьте голосовое сообщение или аудиофайл с записью встречи.\n\n"
            "Бот обработает запись, создаст расшифровку с тайм-кодами и структурированное резюме.\n\n"
            "📎 Поддерживаемые форматы: MP3, M4A, WAV, OGG",
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
        "🚀 **Ты можешь пользоваться мной прямо сейчас!**\n\n"
        "Все работает без подключения календарей — просто напиши или скажи:\n"
        "• \"Встреча завтра в 15:00\"\n"
        "• \"Напомни про доклад в пятницу\"\n"
        "• \"Уборка в среду утром\"\n\n"
        "📅 **Подключение календарей (необязательно):**\n"
        "Это функция для удобства — ты сможешь видеть события в своем привычном календаре (Google, iCloud). "
        "Но бот работает и без подключения! Все события сохраняются, напоминания приходят — можешь пользоваться сразу.\n\n"
    )
    
    keyboard = []
    
    # Если календари подключены, показываем статус, иначе предлагаем (опционально)
    if has_connections:
        welcome_message += "✅ Твои календари подключены и синхронизируются!\n\n"
    else:
        welcome_message += (
            "💡 Хочешь синхронизировать с календарем? Это опционально — можешь подключить позже через /settings\n\n"
        )
        keyboard.append([InlineKeyboardButton(
            "📅 Подключить календарь (опционально)",
            callback_data="settings_google"
        )])
    
    # Устанавливаем постоянную клавиатуру (ReplyKeyboardMarkup) вместо inline кнопок
    reply_keyboard = get_reply_keyboard(context)
    
    # Inline кнопки только для дополнительных действий (если есть)
    inline_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
    
    await update.message.reply_text(
        welcome_message,
        reply_markup=inline_markup,
        parse_mode="Markdown"
    )
    
    # Отправляем отдельное сообщение с постоянной клавиатурой
    # (InlineKeyboardMarkup и ReplyKeyboardMarkup нельзя использовать одновременно)
    await update.message.reply_text(
        "💡 Используй кнопки внизу экрана для переключения режима или возврата в меню.",
        reply_markup=reply_keyboard
    )


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /menu - главное меню с переключателем режимов."""
    user_id = update.effective_user.id
    is_meeting_mode = context.user_data.get('waiting_meeting_audio', False)
    
    # Устанавливаем постоянную клавиатуру
    reply_keyboard = get_reply_keyboard(context)
    
    # Дополнительные кнопки для меню (inline)
    keyboard = []
    keyboard.append([InlineKeyboardButton("⚙️ Настройки", callback_data="settings_show")])
    keyboard.append([InlineKeyboardButton("❓ Как пользоваться", callback_data="help_show")])
    
    inline_markup = InlineKeyboardMarkup(keyboard)
    
    mode_text = "🎤 **Режим резюмирования встреч**" if is_meeting_mode else "📅 **Режим планировщика**"
    
    await update.message.reply_text(
        f"📋 **Главное меню TRACY**\n\n"
        f"Текущий режим: {mode_text}\n\n"
        "Выбери действие:",
        reply_markup=inline_markup,
        parse_mode="Markdown"
    )
    # Отправляем отдельное сообщение с постоянной клавиатурой (если нужно обновить)
    # Но лучше просто установить клавиатуру один раз при входе в режим


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help."""
    # Генерируем структурированный ответ через AI
    help_text = await generate_structured_help_response()
    # Устанавливаем постоянную клавиатуру
    reply_keyboard = get_reply_keyboard(context)
    await update.message.reply_text(help_text, reply_markup=reply_keyboard)


async def web_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /web - открывает веб-приложение."""
    web_url = os.getenv("WEB_APP_URL", "http://localhost:3000")
    
    message_text = (
        "🌐 **Веб-приложение TRACY**\n\n"
        "Веб-интерфейс доступен по адресу:\n"
        f"`{web_url}`\n\n"
        "В веб-приложении ты можешь:\n"
        "• Просматривать календарь\n"
        "• Создавать и редактировать события\n"
        "• Обрабатывать встречи и создавать резюме\n"
        "• Настраивать календари\n\n"
        "Открой этот адрес в браузере для доступа к веб-интерфейсу."
    )
    
    # Пробуем создать Telegram Web App кнопку только для валидных HTTPS URL (не localhost)
    if "localhost" not in web_url.lower() and web_url.startswith("https://"):
        try:
            keyboard = [[InlineKeyboardButton(
                "🌐 Открыть веб-приложение",
                web_app=WebAppInfo(url=web_url)
            )]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                message_text,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            return
        except Exception as e:
            logger.warning(f"Не удалось создать кнопку для веб-приложения: {e}")
    
    # Для localhost или если кнопка не получилась - отправляем просто текст
    await update.message.reply_text(message_text, parse_mode="Markdown")


def format_message_for_user(message: str) -> str:
    """
    Форматирует сообщение для пользователя, улучшая читаемость.
    
    Если сообщение длинное и содержит нумерованные списки или структуру,
    форматирует его для лучшей читаемости.
    """
    # Если сообщение уже хорошо отформатировано, возвращаем как есть
    if '\n' in message and (message.count('\n') > 2 or '1.' in message or '·' in message):
        return message
    
    # Если сообщение длинное, пробуем разбить на абзацы
    if len(message) > 200 and '.' in message:
        # Разбиваем по предложениям и добавляем переносы
        sentences = message.split('. ')
        if len(sentences) > 3:
            formatted = '\n\n'.join([s.strip() + '.' if not s.endswith('.') else s.strip() 
                                     for s in sentences if s.strip()])
            return formatted
    
    return message


async def generate_structured_help_response() -> str:
    """Генерирует структурированный ответ для /help через AI."""
    try:
        prompt = """Объясни пользователю как работает бот TRACY для управления календарем. 

Ответ должен быть структурированным, понятным и использовать нумерованные списки для лучшей читаемости.

Объясни:
1. Что делает бот (кратко)
2. Как пользоваться (пошагово, нумерованный список)
3. Примеры использования
4. Режимы работы

Формат ответа должен быть таким, как в примере:
"Когда ты мне пишешь, я делаю так:

1. Сначала читаю твоё сообщение — текст, голос, аудиофайл, картинку или скриншот.
2. Извлекаю из него ключевую информацию о событии или напоминании (что, когда, где).
3. Создаю или обновляю событие в твоём основном календаре (например, iCloud).
4. Если нужно, устанавливаю напоминание, чтобы вовремя тебя уведомить.
5. Отвечаю тебе, подтверждая, что событие добавлено или изменено.
6. Если ты хочешь, могу искать события, удалять их или делиться ими с друзьями.
7. Если ты отправляешь "setting", показываю меню настроек для управления календарями, уведомлениями и прочим.

Короче, ты просто говоришь, что нужно, а я организую твой график и напомню! 😉"

Используй такой же стиль - дружелюбный, понятный, с нумерованными списками и эмодзи где уместно."""

        response = nlp_extractor.client.chat.completions.create(
            model=config.OPENROUTER_MODEL,
            messages=[
                {"role": "system", "content": "Ты помощник TRACY, дружелюбный AI-ассистент для управления календарем. Отвечай структурированно, используя нумерованные списки для лучшей читаемости. Будь кратким, но информативным."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        logger.error(f"Ошибка генерации help через AI: {e}")
        # Fallback на статический ответ
        return """Когда ты мне пишешь, я делаю так:

1. Сначала читаю твоё сообщение — текст, голос, аудиофайл, картинку или скриншот.
2. Извлекаю из него ключевую информацию о событии или напоминании (что, когда, где).
3. Создаю или обновляю событие в твоём основном календаре (например, iCloud).
4. Если нужно, устанавливаю напоминание, чтобы вовремя тебя уведомить.
5. Отвечаю тебе, подтверждая, что событие добавлено или изменено.
6. Если ты хочешь, могу искать события, удалять их или делиться ими с друзьями.
7. Если ты отправляешь "/settings", показываю меню настроек для управления календарями, уведомлениями и прочим.

📝 Примеры:
• "Встреча с командой завтра в 15:00"
• "Вспомни про доклад в пятницу"
• "Дело на офис в среду утром"

🔧 Команды:
/settings - подключить Google/iCloud календарь
/search <текст> - найти события
/share <событие> - поделиться событием (ICS файл)

Короче, ты просто говоришь, что нужно, а я организую твой график и напомню! 😉"""


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /settings."""
    user_id = update.effective_user.id
    
    # Получаем подключенные календари
    connections = db.get_calendar_connections(user_id)
    
    keyboard = []
    
    # Кнопка для Google Calendar
    google_connected = any(c['provider'] == 'google' for c in connections)
    keyboard.append([InlineKeyboardButton(
        f"Google Calendar {'✓' if google_connected else ''}",
        callback_data="settings_google"
    )])
    
    # Кнопка для iCloud Calendar
    icloud_connected = any(c['provider'] == 'icloud' for c in connections)
    keyboard.append([InlineKeyboardButton(
        f"iCloud Calendar {'✓' if icloud_connected else ''}",
        callback_data="settings_icloud"
    )])
    
    # Кнопка для настроек уведомлений
    keyboard.append([InlineKeyboardButton("Уведомления", callback_data="settings_notifications")])
    
    # Кнопка для открытия веб-приложения (Telegram Web App, только если URL валидный и не localhost)
    web_url = os.getenv("WEB_APP_URL", "http://localhost:3000")
    # Telegram не принимает localhost для inline кнопок, поэтому добавляем только для реальных доменов
    if "localhost" not in web_url.lower() and web_url.startswith("https://"):
        try:
            keyboard.append([InlineKeyboardButton(
                "🌐 Открыть веб-приложение",
                web_app=WebAppInfo(url=web_url)
            )])
        except:
            pass  # Если не получилось, просто не добавляем кнопку
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    status_text = "Настройки TRACY:\n\n"
    status_text += f"Google Calendar: {'подключен' if google_connected else 'не подключен'}\n"
    status_text += f"iCloud Calendar: {'подключен' if icloud_connected else 'не подключен'}\n\n"
    status_text += "Выберите опцию:"
    
    await update.message.reply_text(status_text, reply_markup=reply_markup)


def generate_icloud_instructions() -> str:
    """Генерирует подробную инструкцию для подключения iCloud Calendar через Apple ID сайт."""
    return """📋 **Подключение iCloud Calendar**

🔐 **ШАГ 1: Проверь двухфакторную аутентификацию**
   1. Открой сайт **appleid.apple.com** в браузере
   2. Войди в свой Apple ID
   3. Перейди в раздел **"Безопасность"**
   4. Проверь, что **"Двухфакторная аутентификация"** включена
   5. Если выключена — включи её, следуя инструкциям на экране

🔑 **ШАГ 2: Создай пароль приложения (App-Specific Password)**
   1. На сайте **appleid.apple.com** останься в разделе **"Безопасность"**
   2. Прокрути вниз до раздела **"Пароли приложений"** (App-Specific Passwords)
   3. Нажми кнопку **"Создать пароль..."** (или "Generate Password...")
   4. В появившемся окне введи название: **"TRACY Bot"**
   5. Нажми **"Создать"** (или "Create")
   6. ⚠️ **КРИТИЧЕСКИ ВАЖНО:** Скопируй пароль **СРАЗУ!**
      • Пароль показывается только один раз
      • Формат: `xxxx-xxxx-xxxx-xxxx` (16 символов в 4 группах)
      • Сохрани пароль в безопасном месте — он больше не будет показан

💡 **ВАЖНО:**
   • Используй **ТОЛЬКО** пароль приложения, **НЕ** обычный пароль Apple ID
   • Если потерял пароль — создай новый (старый нельзя увидеть снова)

✅ Когда всё готово, нажми кнопку "Я готов к подключению" ниже."""


async def settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик callback от кнопок настроек."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    if data == "settings_google":
        try:
            # Проверяем, не подключен ли уже
            connections = db.get_calendar_connections(user_id)
            google_connected = any(c['provider'] == 'google' for c in connections)
            
            if google_connected:
                # Предлагаем отключить
                keyboard = [
                    [InlineKeyboardButton("Отключить Google Calendar", callback_data="disconnect_google")],
                    [InlineKeyboardButton("⬅️ Назад", callback_data="settings_show")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(
                    "✅ Google Calendar уже подключен.\n\n"
                    "Твои события автоматически синхронизируются с Google Calendar.",
                    reply_markup=reply_markup
                )
            else:
                # Проверяем настройки Google OAuth ПЕРЕД созданием calendar
                if not config.GOOGLE_CLIENT_ID or not config.GOOGLE_CLIENT_SECRET or \
                   not config.GOOGLE_CLIENT_ID.strip() or not config.GOOGLE_CLIENT_SECRET.strip():
                    keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="settings_show")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await query.edit_message_text(
                        "❌ **Ошибка настройки Google Calendar**\n\n"
                        "Google OAuth не настроен.\n\n"
                        "📋 **Для настройки требуется:**\n\n"
                        "**1. Создать проект в Google Cloud Console:**\n"
                        "• Перейди на https://console.cloud.google.com/\n"
                        "• Создай новый проект или выбери существующий\n"
                        "• Включи Google Calendar API\n\n"
                        "**2. Создать OAuth 2.0 credentials:**\n"
                        "• Перейди в \"APIs & Services\" → \"Credentials\"\n"
                        "• Нажми \"Create Credentials\" → \"OAuth client ID\"\n"
                        "• Выбери тип \"Web application\"\n"
                        "• Добавь Redirect URI: `http://localhost:8080/callback`\n"
                        "• Скопируй Client ID и Client Secret\n\n"
                        "**3. Добавить в .env файл:**\n"
                        "```\n"
                        "GOOGLE_CLIENT_ID=твой_client_id\n"
                        "GOOGLE_CLIENT_SECRET=твой_client_secret\n"
                        "GOOGLE_REDIRECT_URI=http://localhost:8080/callback\n"
                        "```\n\n"
                        "**4. Перезапустить бота**\n\n"
                        "📖 Подробная инструкция: https://developers.google.com/calendar/api/quickstart/python",
                        reply_markup=reply_markup,
                        parse_mode="Markdown"
                    )
                    return
                
                # Инициируем OAuth flow для Google
                try:
                    calendar = GoogleCalendar(user_id)
                    auth_url = calendar.get_authorization_url()
                    
                    # Создаем кнопку для перехода по ссылке
                    keyboard = [
                        [InlineKeyboardButton(
                            "🔗 Открыть ссылку авторизации",
                            url=auth_url
                        )],
                        [InlineKeyboardButton("⬅️ Назад", callback_data="settings_show")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await query.edit_message_text(
                        "📅 **Подключение Google Calendar**\n\n"
                        "🔐 **Пошаговая инструкция:**\n\n"
                        "**ШАГ 1:** Нажми на кнопку **\"Открыть ссылку авторизации\"** ниже\n\n"
                        "**ШАГ 2:** Войди в свой Google аккаунт (если еще не вошел)\n\n"
                        "**ШАГ 3:** Разреши доступ к Google Calendar\n"
                        "• Нажми \"Разрешить\" или \"Allow\"\n"
                        "• Выбери аккаунт Google, если предложено\n\n"
                        "**ШАГ 4:** После авторизации\n"
                        "• Если видишь \"Access blocked\" или \"Эта страница не может быть открыта\" — это нормально!\n"
                        "• Не закрывай страницу, просто скопируй URL из адресной строки браузера\n"
                        "• URL должен содержать параметр `code=` или `error=`\n\n"
                        "**ШАГ 5:** Скопируй и отправь URL\n"
                        "• Скопируй **ВЕСЬ URL** из адресной строки (Ctrl+C или долгое нажатие)\n"
                        "• Отправь этот URL боту в ответ на это сообщение\n\n"
                        "⚠️ **Важно:**\n"
                        "• URL должен начинаться с `http://` или `https://`\n"
                        "• Скопируй URL целиком, включая `?code=` или `&code=`\n"
                        "• Если видишь ошибку в URL (`error=`), отправь URL боту — он покажет, что не так\n\n"
                        "Бот будет ожидать URL с кодом авторизации.",
                        reply_markup=reply_markup,
                        parse_mode="Markdown"
                    )
                    
                    # Сохраняем состояние ожидания URL
                    context.user_data['waiting_google_url'] = True
                except Exception as e:
                    logger.error(f"Ошибка инициализации Google Calendar OAuth: {e}", exc_info=True)
                    keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="settings_show")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    error_msg = str(e).lower()
                    if "google_client_id" in error_msg or "google_client_secret" in error_msg or "пустыми" in error_msg or "не установлены" in error_msg:
                        user_message = (
                            "❌ **Ошибка настройки Google Calendar**\n\n"
                            "Google OAuth не настроен.\n\n"
                            "📋 **Для настройки требуется:**\n\n"
                            "**1. Создать проект в Google Cloud Console:**\n"
                            "• Перейди на https://console.cloud.google.com/\n"
                            "• Создай новый проект или выбери существующий\n"
                            "• Включи Google Calendar API\n\n"
                            "**2. Создать OAuth 2.0 credentials:**\n"
                            "• Перейди в \"APIs & Services\" → \"Credentials\"\n"
                            "• Нажми \"Create Credentials\" → \"OAuth client ID\"\n"
                            "• Выбери тип \"Web application\"\n"
                            "• Добавь Redirect URI: `http://localhost:8080/callback`\n"
                            "• Скопируй Client ID и Client Secret\n\n"
                            "**3. Добавить в .env файл:**\n"
                            "```\n"
                            "GOOGLE_CLIENT_ID=твой_client_id\n"
                            "GOOGLE_CLIENT_SECRET=твой_client_secret\n"
                            "GOOGLE_REDIRECT_URI=http://localhost:8080/callback\n"
                            "```\n\n"
                            "**4. Перезапустить бота**\n\n"
                            "📖 Подробная инструкция: https://developers.google.com/calendar/api/quickstart/python"
                        )
                    else:
                        user_message = (
                            f"❌ Ошибка подключения Google Calendar.\n\n"
                            f"Детали ошибки: {str(e)[:300]}\n\n"
                            f"Проверь настройки GOOGLE_CLIENT_ID и GOOGLE_CLIENT_SECRET в файле .env"
                        )
                    
                    await query.edit_message_text(
                        user_message,
                        reply_markup=reply_markup,
                        parse_mode="Markdown"
                    )
        except Exception as e:
            logger.error(f"Ошибка в settings_google: {e}", exc_info=True)
            keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="settings_show")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ Произошла ошибка при обработке запроса.\n"
                "Попробуй снова через /settings",
                reply_markup=reply_markup
            )
    
    elif data == "menu_show":
        # Показываем главное меню с переключателем режимов
        is_meeting_mode = context.user_data.get('waiting_meeting_audio', False)
        
        keyboard = []
        
        # Переключатель режимов (одна кнопка, меняется в зависимости от режима)
        if is_meeting_mode:
            keyboard.append([InlineKeyboardButton("📅 Перейти в режим планировщика", callback_data="mode_planner")])
        else:
            keyboard.append([InlineKeyboardButton("🎤 Перейти в режим резюмирования встреч", callback_data="mode_meeting_transcribe")])
        
        # Кнопки настроек и помощи
        keyboard.append([InlineKeyboardButton("⚙️ Настройки", callback_data="settings_show")])
        keyboard.append([InlineKeyboardButton("❓ Как пользоваться", callback_data="help_show")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        mode_text = "🎤 **Режим резюмирования встреч**" if is_meeting_mode else "📅 **Режим планировщика**"
        
        await query.edit_message_text(
            f"📋 **Главное меню TRACY**\n\n"
            f"Текущий режим: {mode_text}\n\n"
            "Выбери действие:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return
    
    elif data == "settings_show":
        # Показываем меню настроек через callback
        user_id = query.from_user.id
        connections = db.get_calendar_connections(user_id)
        
        keyboard = []
        
        # Кнопка для Google Calendar
        google_connected = any(c['provider'] == 'google' for c in connections)
        keyboard.append([InlineKeyboardButton(
            f"Google Calendar {'✓' if google_connected else ''}",
            callback_data="settings_google"
        )])
        
        # Кнопка для iCloud Calendar
        icloud_connected = any(c['provider'] == 'icloud' for c in connections)
        keyboard.append([InlineKeyboardButton(
            f"iCloud Calendar {'✓' if icloud_connected else ''}",
            callback_data="settings_icloud"
        )])
        
        # Кнопка для настроек уведомлений
        keyboard.append([InlineKeyboardButton("Уведомления", callback_data="settings_notifications")])
        
        # Кнопка для открытия веб-приложения
        web_url = os.getenv("WEB_APP_URL", "http://localhost:3000")
        if "localhost" not in web_url.lower() and web_url.startswith("https://"):
            try:
                keyboard.append([InlineKeyboardButton(
                    "🌐 Открыть веб-приложение",
                    web_app=WebAppInfo(url=web_url)
                )])
            except:
                pass
        
        # Кнопка "Назад" в меню
        keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="menu_show")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "⚙️ **Настройки**\n\n"
            "Здесь ты можешь управлять подключенными календарями и другими параметрами:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return
    
    elif data == "help_show":
        # Показываем помощь (короткая версия без нумерации шагов)
        help_text = """📖 **Как пользоваться TRACY**

Просто напиши мне или отправь голосовое сообщение с событием, и я добавлю его в календарь.

**Примеры:**
• "Завтра в 15:00 стрижка"
• "Напомни про доклад в пятницу"
• "Уборка в среду утром"
• "Какие у меня планы на неделю?"
• "Удали все события на сегодня"

**Режимы работы:**
• **Режим планировщика** — создание и управление событиями
• **Режим резюмирования встреч** — расшифровка аудио встреч

💡 Бот работает без подключения календарей! Все события сохраняются, напоминания приходят."""
        
        keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="menu_show")]]
        inline_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(help_text, reply_markup=inline_markup, parse_mode="Markdown")
        
        # Устанавливаем постоянную клавиатуру отдельным сообщением
        reply_keyboard = get_reply_keyboard(context)
        await query.message.reply_text(
            "💡 Используй кнопки внизу экрана для переключения режима или возврата в меню.",
            reply_markup=reply_keyboard
        )
        return
    
    elif data == "settings_icloud":
        try:
            # Проверяем, не подключен ли уже
            connections = db.get_calendar_connections(user_id)
            icloud_connected = any(c['provider'] == 'icloud' for c in connections)
            
            if icloud_connected:
                keyboard = [
                    [InlineKeyboardButton("Отключить iCloud Calendar", callback_data="disconnect_icloud")],
                    [InlineKeyboardButton("⬅️ Назад", callback_data="settings_show")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(
                    "✅ iCloud Calendar уже подключен.\n\n"
                    "Твои события автоматически синхронизируются с iCloud Calendar.",
                    reply_markup=reply_markup
                )
            else:
                # Показываем инструкцию
                instructions = generate_icloud_instructions()
                keyboard = [
                    [InlineKeyboardButton("✅ Я готов к подключению", callback_data="icloud_ready")],
                    [InlineKeyboardButton("⬅️ Назад", callback_data="settings_show")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(instructions, reply_markup=reply_markup, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Ошибка в settings_icloud: {e}", exc_info=True)
            keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="settings_show")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ Произошла ошибка при обработке запроса.\n"
                "Попробуй снова через /settings",
                reply_markup=reply_markup
            )
    
    elif data == "icloud_ready":
        # Начинаем процесс подключения iCloud
        context.user_data['icloud_step'] = 'email'
        keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data="icloud_cancel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(
            "📧 **Шаг 1 из 2: Введи свой Apple ID**\n\n"
            "Отправь email адрес, который привязан к твоему Apple ID.\n\n"
            "Пример:\n"
            "`ivan@icloud.com`\n"
            "или\n"
            "`ivan@gmail.com` (если используется как Apple ID)\n\n"
            "Отправь email в ответ на это сообщение.",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return
    
    elif data == "icloud_cancel":
        # Отмена подключения iCloud
        context.user_data.pop('icloud_step', None)
        context.user_data.pop('icloud_email', None)
        await query.answer("Подключение отменено")
        
        # Возвращаемся к инструкции
        instructions = generate_icloud_instructions()
        keyboard = [
            [InlineKeyboardButton("✅ Я готов к подключению", callback_data="icloud_ready")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="settings_show")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(instructions, reply_markup=reply_markup, parse_mode="Markdown")
        return
    
    elif data == "disconnect_google":
        try:
            connections = db.get_calendar_connections(user_id)
            google_connection = next((c for c in connections if c['provider'] == 'google'), None)
            
            if google_connection:
                # Удаляем подключение
                db.deactivate_calendar_connection(user_id, 'google', google_connection.get('calendar_id', 'primary'))
                keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="settings_show")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text("✅ Google Calendar отключен.", reply_markup=reply_markup)
                
                # Отправляем обновленный статус календарей в веб-приложение
                await send_calendar_status_to_web_app(user_id, context)
            else:
                keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="settings_show")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text("Google Calendar не был подключен.", reply_markup=reply_markup)
        except Exception as e:
            logger.error(f"Ошибка отключения Google Calendar: {e}", exc_info=True)
            keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="settings_show")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("❌ Ошибка при отключении Google Calendar.", reply_markup=reply_markup)
    
    elif data == "disconnect_icloud":
        try:
            connections = db.get_calendar_connections(user_id)
            icloud_connection = next((c for c in connections if c['provider'] == 'icloud'), None)
            
            if icloud_connection:
                # Удаляем подключение
                db.deactivate_calendar_connection(user_id, 'icloud', icloud_connection.get('calendar_id', ''))
                keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="settings_show")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text("✅ iCloud Calendar отключен.", reply_markup=reply_markup)
                
                # Отправляем обновленный статус календарей в веб-приложение
                await send_calendar_status_to_web_app(user_id, context)
            else:
                keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="settings_show")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text("iCloud Calendar не был подключен.", reply_markup=reply_markup)
        except Exception as e:
            logger.error(f"Ошибка отключения iCloud Calendar: {e}", exc_info=True)
            keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="settings_show")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("❌ Ошибка при отключении iCloud Calendar.", reply_markup=reply_markup)
    
    elif data == "settings_notifications":
        # Настройки уведомлений
        user_settings = db.get_user_settings(user_id)
        notifications_enabled = user_settings.get('notifications_enabled', True)
        default_reminder_minutes = user_settings.get('default_reminder_minutes', 15)
        morning_digest_time = user_settings.get('morning_digest_time', '09:00')
        
        keyboard = []
        
        # Включение/выключение уведомлений
        if notifications_enabled:
            keyboard.append([InlineKeyboardButton("🔕 Отключить уведомления", callback_data="notifications_toggle")])
        else:
            keyboard.append([InlineKeyboardButton("🔔 Включить уведомления", callback_data="notifications_toggle")])
        
        # Настройка напоминаний по умолчанию
        keyboard.append([InlineKeyboardButton("⏰ Настроить напоминания", callback_data="notifications_reminders")])
        
        keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="settings_show")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        status_icon = "🔔" if notifications_enabled else "🔕"
        status_text = "включены" if notifications_enabled else "выключены"
        
        # Форматируем время напоминания для отображения
        if default_reminder_minutes < 60:
            reminder_text = f"{default_reminder_minutes} минут"
        elif default_reminder_minutes == 60:
            reminder_text = "1 час"
        elif default_reminder_minutes < 1440:
            hours = default_reminder_minutes // 60
            reminder_text = f"{hours} час{'а' if hours in [2, 3, 4] else '' if hours == 1 else 'ов'}"
        else:
            days = default_reminder_minutes // 1440
            reminder_text = f"{days} ден{'ь' if days == 1 else 'я' if days in [2, 3, 4] else 'ей'}"
        
        await query.edit_message_text(
            f"🔔 **Настройки уведомлений**\n\n"
            f"Статус: {status_icon} Уведомления {status_text}\n\n"
            f"Напоминание по умолчанию: за {reminder_text} до события\n"
            f"☀️ Утренний дайджест: {morning_digest_time}\n\n"
            "💡 Настройки утреннего дайджеста можно изменить в веб-приложении.\n\n"
            "Здесь ты можешь управлять уведомлениями о событиях и напоминаниями.",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return
    
    elif data == "notifications_toggle":
        # Переключение уведомлений
        user_settings = db.get_user_settings(user_id)
        notifications_enabled = user_settings.get('notifications_enabled', True)
        new_status = not notifications_enabled
        
        db.update_user_settings(user_id, settings_dict={'notifications_enabled': new_status})
        
        await query.answer(f"Уведомления {'включены' if new_status else 'выключены'}")
        
        # Возвращаемся к настройкам уведомлений
        keyboard = []
        if new_status:
            keyboard.append([InlineKeyboardButton("🔕 Отключить уведомления", callback_data="notifications_toggle")])
        else:
            keyboard.append([InlineKeyboardButton("🔔 Включить уведомления", callback_data="notifications_toggle")])
        keyboard.append([InlineKeyboardButton("⏰ Настроить напоминания", callback_data="notifications_reminders")])
        keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="settings_show")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        status_icon = "🔔" if new_status else "🔕"
        status_text = "включены" if new_status else "выключены"
        default_reminder_minutes = user_settings.get('default_reminder_minutes', 15)
        
        # Форматируем время напоминания для отображения
        if default_reminder_minutes < 60:
            reminder_text = f"{default_reminder_minutes} минут"
        elif default_reminder_minutes == 60:
            reminder_text = "1 час"
        elif default_reminder_minutes < 1440:
            hours = default_reminder_minutes // 60
            reminder_text = f"{hours} час{'а' if hours in [2, 3, 4] else '' if hours == 1 else 'ов'}"
        else:
            days = default_reminder_minutes // 1440
            reminder_text = f"{days} ден{'ь' if days == 1 else 'я' if days in [2, 3, 4] else 'ей'}"
        
        await query.edit_message_text(
            f"🔔 **Настройки уведомлений**\n\n"
            f"Статус: {status_icon} Уведомления {status_text}\n\n"
            f"Напоминание по умолчанию: за {reminder_text} до события\n\n"
            "Здесь ты можешь управлять уведомлениями о событиях и напоминаниями.",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return
    
    elif data == "notifications_reminders":
        # Настройка напоминаний
        user_settings = db.get_user_settings(user_id)
        default_reminder_minutes = user_settings.get('default_reminder_minutes', 15)
        
        keyboard = [
            [InlineKeyboardButton("⏰ За 5 минут", callback_data="reminder_set_5")],
            [InlineKeyboardButton("⏰ За 15 минут", callback_data="reminder_set_15")],
            [InlineKeyboardButton("⏰ За 30 минут", callback_data="reminder_set_30")],
            [InlineKeyboardButton("⏰ За 1 час", callback_data="reminder_set_60")],
            [InlineKeyboardButton("⏰ За 1 день", callback_data="reminder_set_1440")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="settings_notifications")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Форматируем текущее время напоминания
        if default_reminder_minutes < 60:
            current_reminder_text = f"{default_reminder_minutes} минут"
        elif default_reminder_minutes == 60:
            current_reminder_text = "1 час"
        elif default_reminder_minutes < 1440:
            hours = default_reminder_minutes // 60
            current_reminder_text = f"{hours} час{'а' if hours in [2, 3, 4] else '' if hours == 1 else 'ов'}"
        else:
            days = default_reminder_minutes // 1440
            current_reminder_text = f"{days} ден{'ь' if days == 1 else 'я' if days in [2, 3, 4] else 'ей'}"
        
        await query.edit_message_text(
            f"⏰ **Настройка напоминаний**\n\n"
            f"Текущее напоминание по умолчанию: за {current_reminder_text} до события\n\n"
            "Выбери время, за которое бот будет напоминать о событиях:\n\n"
            "Это время будет использоваться для всех новых событий, если ты не укажешь другое.",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return
    
    elif data.startswith("reminder_set_"):
        # Установка времени напоминания
        try:
            minutes = int(data.split("_")[-1])
            db.update_user_settings(user_id, settings_dict={'default_reminder_minutes': minutes})
            
            # Форматируем время для отображения
            if minutes < 60:
                time_text = f"{minutes} минут"
            elif minutes == 60:
                time_text = "1 час"
            elif minutes < 1440:
                hours = minutes // 60
                time_text = f"{hours} час{'а' if hours in [2, 3, 4] else '' if hours == 1 else 'ов'}"
            else:
                days = minutes // 1440
                time_text = f"{days} ден{'ь' if days == 1 else 'я' if days in [2, 3, 4] else 'ей'}"
            
            await query.answer(f"✅ Напоминание установлено: за {time_text}")
            
            # Возвращаемся к настройкам уведомлений
            user_settings = db.get_user_settings(user_id)
            notifications_enabled = user_settings.get('notifications_enabled', True)
            
            keyboard = []
            if notifications_enabled:
                keyboard.append([InlineKeyboardButton("🔕 Отключить уведомления", callback_data="notifications_toggle")])
            else:
                keyboard.append([InlineKeyboardButton("🔔 Включить уведомления", callback_data="notifications_toggle")])
            keyboard.append([InlineKeyboardButton("⏰ Настроить напоминания", callback_data="notifications_reminders")])
            keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="settings_show")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            status_icon = "🔔" if notifications_enabled else "🔕"
            status_text = "включены" if notifications_enabled else "выключены"
            
            # Форматируем для отображения в сообщении
            if minutes < 60:
                reminder_text = f"{minutes} минут"
            elif minutes == 60:
                reminder_text = "1 час"
            elif minutes < 1440:
                hours = minutes // 60
                reminder_text = f"{hours} час{'а' if hours in [2, 3, 4] else '' if hours == 1 else 'ов'}"
            else:
                days = minutes // 1440
                reminder_text = f"{days} ден{'ь' if days == 1 else 'я' if days in [2, 3, 4] else 'ей'}"
            
            await query.edit_message_text(
                f"🔔 **Настройки уведомлений**\n\n"
                f"Статус: {status_icon} Уведомления {status_text}\n\n"
                f"✅ Напоминание по умолчанию: за {reminder_text} до события\n\n"
                "Здесь ты можешь управлять уведомлениями о событиях и напоминаниями.",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            return
        except (ValueError, IndexError):
            await query.answer("Ошибка установки времени напоминания", show_alert=True)
            return
    
    elif data == "mode_planner":
        # Выход из режима расшифровки встреч в обычный режим планировщика
        context.user_data['waiting_meeting_audio'] = False
        await query.answer("✅ Переключено в режим планировщика")
        
        # Устанавливаем постоянную клавиатуру для режима планировщика
        reply_keyboard = get_reply_keyboard(context)
        
        # Дополнительные кнопки для меню (inline)
        keyboard = []
        keyboard.append([InlineKeyboardButton("⚙️ Настройки", callback_data="settings_show")])
        keyboard.append([InlineKeyboardButton("❓ Как пользоваться", callback_data="help_show")])
        inline_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📋 **Главное меню TRACY**\n\n"
            "✅ **Режим планировщика**\n\n"
            "Теперь ты в обычном режиме работы с календарем. Можешь:\n"
            "• Создавать события из текста, голоса или фото\n"
            "• Управлять напоминаниями\n"
            "• Просматривать и редактировать события\n\n"
            "Используй кнопки внизу экрана для переключения режима.",
            reply_markup=inline_markup,
            parse_mode="Markdown"
        )
        # Устанавливаем постоянную клавиатуру через новое сообщение
        await query.message.reply_text(
            "Постоянная клавиатура активирована. Используй кнопки внизу экрана.",
            reply_markup=reply_keyboard
        )
        return
    
    elif data == "mode_meeting_transcribe":
        # Переход в режим расшифровки встреч
        context.user_data['waiting_meeting_audio'] = True
        await query.answer("✅ Переключено в режим резюмирования встреч")
        
        # Устанавливаем постоянную клавиатуру для режима расшифровки
        reply_keyboard = get_reply_keyboard(context)
        
        # Дополнительные кнопки для меню (inline)
        keyboard = []
        keyboard.append([InlineKeyboardButton("⚙️ Настройки", callback_data="settings_show")])
        keyboard.append([InlineKeyboardButton("❓ Как пользоваться", callback_data="help_show")])
        inline_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📋 **Главное меню TRACY**\n\n"
            "✅ **Режим резюмирования встреч**\n\n"
            "Теперь ты в режиме расшифровки встреч. Отправь голосовое сообщение или аудиофайл с записью встречи для расшифровки.\n\n"
            "📎 Поддерживаемые аудиоформаты: MP3, M4A, WAV, OGG, OPUS, FLAC, AAC, WMA, AMR, 3GP, MKA и другие.\n\n"
            "Используй кнопки внизу экрана для переключения режима.",
            reply_markup=inline_markup,
            parse_mode="Markdown"
        )
        # Устанавливаем постоянную клавиатуру через новое сообщение
        await query.message.reply_text(
            "💡 Используй кнопки внизу экрана для переключения режима.",
            reply_markup=reply_keyboard
        )
        return
    
    elif data == "meeting_back_to_summary":
        # Возврат к резюме встречи
        meeting_data = context.user_data.get('last_meeting_data')
        if meeting_data:
            summary = meeting_data.get('summary', 'Резюме недоступно')
            keyboard = [
                [InlineKeyboardButton("📄 Показать полный текст встречи", callback_data="meeting_full_transcript")],
                [InlineKeyboardButton("📋 Сделать расширенное резюме", callback_data="meeting_extended_summary")],
                [InlineKeyboardButton("📅 Создать события из встречи", callback_data="meeting_create_events")]
            ]
            # Добавляем постоянные кнопки режима
            keyboard.extend(get_meeting_mode_footer_buttons(context))
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                f"📋 **Резюме встречи**\n\n{summary}\n\n"
                "💡 Режим расшифровки встреч активен. Отправь следующее аудио для расшифровки или выбери действие выше.",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        else:
            await query.answer("Нет данных о последней встрече.", show_alert=True)
        return
    
    elif data == "meetings_mode":
        # Вход в режим "Встречи и резюме"
        keyboard = [
            [InlineKeyboardButton("📝 Сделать резюме встречи", callback_data="meeting_create_summary")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="menu_show")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📝 **Встречи и резюме**\n\n"
            "Выбери действие:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    elif data == "meeting_create_summary":
        # Переходим в режим ожидания аудио
        context.user_data['waiting_meeting_audio'] = True
        
        keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="meetings_mode")]]
        # Добавляем постоянные кнопки режима
        keyboard.extend(get_meeting_mode_footer_buttons(context))
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🎤 **Создание резюме встречи**\n\n"
            "Отправь голосовое сообщение или аудиофайл с записью встречи.\n\n"
            "Бот обработает запись, создаст расшифровку с тайм-кодами и структурированное резюме.",
            reply_markup=reply_markup
        )
    
    elif data.startswith("meeting_") and data != "meeting_create_summary" and data != "meeting_back_to_summary":
        # Обработка дополнительных действий после создания резюме
        meeting_data = context.user_data.get('last_meeting_data')
        
        if not meeting_data:
            await query.answer("Нет данных о последней встрече. Сначала создай резюме.", show_alert=True)
            return
        
        if data == "meeting_full_transcript":
            # Показать полный текст
            transcript = meeting_data.get('transcript', 'Расшифровка недоступна')
            
            keyboard = [
                [InlineKeyboardButton("📋 Сделать расширенное резюме", callback_data="meeting_extended_summary")],
                [InlineKeyboardButton("📅 Создать события из встречи", callback_data="meeting_create_events")],
                [InlineKeyboardButton("⬅️ Назад к резюме", callback_data="meeting_back_to_summary")]
            ]
            # Добавляем постоянные кнопки режима
            keyboard.extend(get_meeting_mode_footer_buttons(context))
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Если текст слишком длинный, отправляем как отдельное сообщение
            if len(transcript) > 4000:
                # Разбиваем на части если слишком длинный
                parts = [transcript[i:i+4000] for i in range(0, len(transcript), 4000)]
                for i, part in enumerate(parts):
                    if i == 0:
                        await query.message.reply_text(
                            f"📄 **Полная расшифровка встречи** (часть {i+1}/{len(parts)})\n\n{part}",
                            parse_mode="Markdown"
                        )
                    else:
                        await query.message.reply_text(
                            f"**Продолжение** (часть {i+1}/{len(parts)})\n\n{part}",
                            parse_mode="Markdown"
                        )
                
                # Отправляем кнопки в последнем сообщении
                await query.message.reply_text(
                    "Выбери действие:",
                    reply_markup=reply_markup
                )
                await query.answer()
            else:
                await query.edit_message_text(
                    f"📄 **Полная расшифровка встречи**\n\n{transcript}",
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
        
        elif data == "meeting_extended_summary":
            # Расширенное резюме
            await query.answer("Генерирую расширенное резюме...")
            await context.bot.send_chat_action(
                chat_id=query.message.chat_id,
                action=ChatAction.TYPING
            )
            
            extended_summary = await meeting_processor.generate_extended_summary(
                meeting_data.get('transcript', ''),
                meeting_data.get('raw_text', ''),
                meeting_data.get('language', 'ru')
            )
            
            keyboard = [
                [InlineKeyboardButton("📄 Показать полный текст", callback_data="meeting_full_transcript")],
                [InlineKeyboardButton("📅 Создать события из встречи", callback_data="meeting_create_events")],
                [InlineKeyboardButton("⬅️ Назад к резюме", callback_data="meeting_back_to_summary")]
            ]
            # Добавляем постоянные кнопки режима
            keyboard.extend(get_meeting_mode_footer_buttons(context))
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if extended_summary:
                # Обновляем расширенное резюме в БД если есть ID встречи
                meeting_id = meeting_data.get('id')
                if meeting_id:
                    try:
                        # Обновляем встречу в БД через прямой SQL запрос, так как нет метода update_meeting
                        conn = db.get_connection()
                        cursor = conn.cursor()
                        try:
                            if db.use_postgresql:
                                cursor.execute(
                                    "UPDATE meetings SET summary_extended = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s AND user_id = %s",
                                    (extended_summary, meeting_id, user_id)
                                )
                            else:
                                cursor.execute(
                                    "UPDATE meetings SET summary_extended = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?",
                                    (extended_summary, meeting_id, user_id)
                                )
                            conn.commit()
                            logger.info(f"Расширенное резюме сохранено для встречи {meeting_id}")
                        except Exception as e:
                            logger.error(f"Ошибка сохранения расширенного резюме: {e}")
                            conn.rollback()
                        finally:
                            db.return_connection(conn)
                    except Exception as e:
                        logger.error(f"Ошибка обновления расширенного резюме: {e}")
                
                # Обновляем в контексте
                meeting_data['summary_extended'] = extended_summary
                context.user_data['last_meeting_data'] = meeting_data
                
                await query.message.reply_text(
                    f"📋 **Расширенное резюме**\n\n{extended_summary}",
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
            else:
                await query.message.reply_text(
                    "Не удалось создать расширенное резюме. Попробуй еще раз.",
                    reply_markup=reply_markup
                )
        
        elif data == "meeting_create_events":
            # Создать события из встречи
            await query.answer("Извлекаю события из встречи...")
            user = db.get_or_create_user(user_id)
            timezone = user.get('timezone', 'Europe/Moscow')
            
            await context.bot.send_chat_action(
                chat_id=query.message.chat_id,
                action=ChatAction.TYPING
            )
            
            events = await meeting_processor.extract_events_from_meeting(
                meeting_data.get('summary', ''),
                meeting_data.get('raw_text', ''),
                timezone
            )
            
            if events:
                if not decision_engine:
                    logger.error("decision_engine не инициализирован")
                    await query.message.reply_text("Ошибка инициализации. Попробуй перезапустить бота.")
                    return
                
                connections = db.get_calendar_connections(user_id)
                created_count = 0
                
                for event_data in events:
                    try:
                        # Капитализируем первую букву названия события
                        event_title = event_data.get('title', 'Событие из встречи')
                        if event_title:
                            event_title = event_title[0].upper() + event_title[1:] if len(event_title) > 1 else event_title.upper()
                        
                        # Получаем start_time и проверяем время
                        start_time = event_data.get('start_time')
                        has_explicit_time = event_data.get('has_explicit_time', True)
                        
                        # Если есть дата, но время 00:00:00, устанавливаем 12:00
                        if start_time and isinstance(start_time, datetime):
                            if start_time.hour == 0 and start_time.minute == 0 and start_time.second == 0:
                                import pytz
                                tz = pytz.timezone(timezone)
                                start_time = start_time.replace(hour=12, minute=0, second=0)
                                if start_time.tzinfo is None:
                                    start_time = tz.localize(start_time)
                                else:
                                    start_time = start_time.astimezone(tz)
                        
                        # Формируем extracted_data в правильном формате
                        extracted_data = {
                            'intent': 'event',
                            'title': event_title,
                            'description': event_data.get('description', ''),
                            'start_time': start_time,
                            'end_time': event_data.get('end_time'),
                            'location': event_data.get('location'),
                            'priority': event_data.get('priority', 0),
                            'has_explicit_time': has_explicit_time
                        }
                        
                        logger.info(f"Создаю событие: {extracted_data.get('title')} на {extracted_data.get('start_time')}")
                        
                        result = await decision_engine.process_intent(
                            user_id,
                            extracted_data,
                            last_event=None
                        )
                        
                        logger.info(f"Результат создания события: {result.get('action')}")
                        if result.get('action') == 'created':
                            created_count += 1
                    except Exception as e:
                        logger.error(f"Ошибка создания события из встречи: {e}", exc_info=True)
                
                keyboard = [
                    [InlineKeyboardButton("📄 Показать полный текст", callback_data="meeting_full_transcript")],
                    [InlineKeyboardButton("📋 Сделать расширенное резюме", callback_data="meeting_extended_summary")],
                    [InlineKeyboardButton("⬅️ Назад к резюме", callback_data="meeting_back_to_summary")]
                ]
                # Добавляем постоянные кнопки режима
                keyboard.extend(get_meeting_mode_footer_buttons(context))
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.message.reply_text(
                    f"✅ Создано событий из встречи: {created_count}\n\n"
                    f"События добавлены в твой календарь.\n\n"
                    f"🎤 **Режим расшифровки встреч всё ещё активен.** Отправь следующее голосовое сообщение или аудиофайл для расшифровки.",
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
            else:
                keyboard = [
                    [InlineKeyboardButton("📄 Показать полный текст", callback_data="meeting_full_transcript")],
                    [InlineKeyboardButton("📋 Сделать расширенное резюме", callback_data="meeting_extended_summary")],
                    [InlineKeyboardButton("⬅️ Назад к резюме", callback_data="meeting_back_to_summary")]
                ]
                # Добавляем постоянные кнопки режима
                keyboard.extend(get_meeting_mode_footer_buttons(context))
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.message.reply_text(
                    "Не найдено событий с конкретными датами в расшифровке встречи.",
                    reply_markup=reply_markup
                )


def get_meeting_mode_footer_buttons(context: ContextTypes.DEFAULT_TYPE) -> List[List[InlineKeyboardButton]]:
    """Создает постоянные кнопки для режима расшифровки встреч (переключение режима и меню)."""
    is_meeting_mode = context.user_data.get('waiting_meeting_audio', False)
    buttons = []
    
    # Кнопка переключения режима
    if is_meeting_mode:
        buttons.append([InlineKeyboardButton("📅 Перейти в режим планировщика", callback_data="mode_planner")])
    else:
        buttons.append([InlineKeyboardButton("🎤 Перейти в режим резюмирования встреч", callback_data="mode_meeting_transcribe")])
    
    # Кнопка меню
    buttons.append([InlineKeyboardButton("📋 Главное меню", callback_data="menu_show")])
    
    return buttons


def get_reply_keyboard(context: ContextTypes.DEFAULT_TYPE, remove: bool = False) -> Union[ReplyKeyboardMarkup, ReplyKeyboardRemove]:
    """
    Создает постоянную клавиатуру (ReplyKeyboardMarkup), которая всегда видна внизу экрана.
    
    Args:
        context: Контекст бота
        remove: Если True, возвращает ReplyKeyboardRemove для скрытия клавиатуры
    
    Returns:
        ReplyKeyboardMarkup или ReplyKeyboardRemove
    """
    if remove:
        return ReplyKeyboardRemove()
    
    is_meeting_mode = context.user_data.get('waiting_meeting_audio', False)
    keyboard = []
    
    # Кнопка переключения режима
    if is_meeting_mode:
        keyboard.append([KeyboardButton("📅 Режим планировщика")])
    else:
        keyboard.append([KeyboardButton("🎤 Режим расшифровки встреч")])
    
    # Кнопка меню
    keyboard.append([KeyboardButton("📋 Меню")])
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def is_audio_file(message) -> bool:
    """Проверяет, является ли сообщение аудиофайлом."""
    # Голосовое сообщение
    if message.voice:
        return True
    
    # Документ с аудио
    if message.document:
        doc = message.document
        # Проверяем расширение файла ПЕРВЫМ (более надежно для M4A из iPhone)
        if doc.file_name:
            audio_extensions = ['.mp3', '.m4a', '.wav', '.ogg', '.oga', '.opus', '.flac', '.aac', '.wma', '.amr', '.3gp', '.mka', '.mp4']
            file_ext = doc.file_name.lower()
            if any(file_ext.endswith(ext) for ext in audio_extensions):
                logger.info(f"Аудиофайл определен по расширению: {file_ext}")
                return True
        
        # Проверяем mime_type (M4A может быть audio/mp4 или audio/x-m4a)
        if doc.mime_type:
            mime_lower = doc.mime_type.lower()
            # Проверяем на audio/* типы
            if 'audio' in mime_lower:
                logger.info(f"Аудиофайл определен по MIME типу: {doc.mime_type}")
                return True
            # M4A может быть определен как audio/mp4 или video/mp4 (но с аудио контентом)
            if 'mp4' in mime_lower and doc.file_name and doc.file_name.lower().endswith('.m4a'):
                logger.info(f"M4A файл определен по комбинации MIME и расширения: {doc.mime_type}, {doc.file_name}")
                return True
        
        # Если нет имени файла, но есть document с audio mime_type, считаем аудио
        if doc.mime_type and 'audio' in doc.mime_type.lower():
            logger.info(f"Аудиофайл определен только по MIME типу: {doc.mime_type}")
            return True
        
        # Если нет имени файла и mime_type, но есть document, попробуем обработать
        # (Telegram иногда не передает mime_type)
        if not doc.mime_type and not doc.file_name:
            # Пробуем обработать как аудио, если нет других индикаторов
            return True
    
    return False


async def handle_meeting_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик аудио для режима встреч."""
    user_id = update.effective_user.id
    
    # Включаем typing action
    try:
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action=ChatAction.TYPING
        )
    except Exception as e:
        logger.warning(f"Ошибка отправки typing action: {e}")
    
    # Механизм для периодического обновления typing action
    stop_typing = False
    
    async def keep_typing():
        max_iterations = 60  # До 4 минут для обработки
        iteration = 0
        while not stop_typing and iteration < max_iterations:
            await asyncio.sleep(4)
            if stop_typing:
                break
            try:
                await context.bot.send_chat_action(
                    chat_id=update.effective_chat.id,
                    action=ChatAction.TYPING
                )
            except Exception:
                break
            iteration += 1
    
    typing_task = None
    try:
        typing_task = asyncio.create_task(keep_typing())
        
        # Получаем аудиофайл
        audio_file = None
        file_type = "unknown"
        file_name = "audio"
        
        if update.message.voice:
            voice = update.message.voice
            audio_file = await context.bot.get_file(voice.file_id)
            file_type = "voice"
            file_name = "voice.ogg"
            logger.info(f"Получено голосовое сообщение, длительность: {voice.duration} сек")
        elif update.message.document:
            doc = update.message.document
            logger.info(f"Получен документ: file_name={doc.file_name}, mime_type={doc.mime_type}, file_size={doc.file_size}")
            
            if is_audio_file(update.message):
                audio_file = await context.bot.get_file(doc.file_id)
                file_type = "document"
                file_name = doc.file_name or "audio_file"
                logger.info(f"✅ Аудиофайл определен: {file_name}, размер: {doc.file_size} bytes, mime_type: {doc.mime_type}")
            else:
                logger.warning(f"❌ Документ не определен как аудиофайл: file_name={doc.file_name}, mime_type={doc.mime_type}")
                # Устанавливаем постоянную клавиатуру
                reply_keyboard = get_reply_keyboard(context)
                await update.message.reply_text(
                    "❌ Это не аудиофайл. Пожалуйста, отправь голосовое сообщение или аудиофайл.\n\n"
                    "📎 Поддерживаемые форматы: MP3, M4A, WAV, OGG, OPUS, FLAC, AAC, WMA, AMR, 3GP, MKA и другие аудиоформаты.\n\n"
                    "💡 Для iPhone: отправь файл из диктофона (обычно формат M4A).\n\n"
                    "Используй кнопки внизу экрана для переключения режима.",
                    reply_markup=reply_keyboard
                )
                return
        
        if not audio_file:
            # Устанавливаем постоянную клавиатуру
            reply_keyboard = get_reply_keyboard(context)
            await update.message.reply_text(
                "❌ Не удалось получить аудиофайл. Убедись, что отправил голосовое сообщение или аудиофайл.\n\n"
                "📎 Поддерживаемые форматы: MP3, M4A, WAV, OGG, OPUS, FLAC, AAC, WMA, AMR, 3GP, MKA и другие аудиоформаты.\n\n"
                "Используй кнопки внизу экрана для переключения режима.",
                reply_markup=reply_keyboard
            )
            return
        
        # Проверяем, что meeting_processor инициализирован
        if not meeting_processor:
            logger.error("meeting_processor не инициализирован")
            # Добавляем постоянные кнопки режима
            keyboard = get_meeting_mode_footer_buttons(context)
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "❌ Ошибка инициализации. Попробуй перезапустить бота.",
                reply_markup=reply_markup
            )
            return
        
        # Получаем настройки пользователя
        user = db.get_or_create_user(user_id)
        language = user.get('locale', 'ru_RU').split('_')[0]  # Извлекаем язык
        logger.info(f"Язык для расшифровки: {language}")
        
        # Отправляем подтверждение о начале расшифровки с постоянной клавиатурой
        reply_keyboard = get_reply_keyboard(context)
        await update.message.reply_text(
            "🎤 Начинаю расшифровку. Это может занять некоторое время.",
            reply_markup=reply_keyboard
        )
        
        # Расшифровываем аудио
        logger.info(f"Начинаю расшифровку аудио для встречи (тип: {file_type}, имя: {file_name}, язык: {language})...")
        try:
            transcription_result = await meeting_processor.transcribe_meeting_audio(audio_file, language)
            if transcription_result:
                logger.info(f"✅ Расшифровка завершена успешно. Длина транскрипта: {len(transcription_result.get('transcript', ''))} символов")
            else:
                logger.warning("⚠️ Расшифровка вернула None (пустой результат)")
        except Exception as e:
            logger.error(f"Ошибка при расшифровке аудио: {e}", exc_info=True)
            import traceback
            logger.error(f"Traceback расшифровки: {traceback.format_exc()}")
            
            error_message = str(e)
            if "timeout" in error_message.lower() or "time" in error_message.lower():
                user_message = (
                    "⏱️ Таймаут при расшифровке аудио.\n\n"
                    "Аудиофайл слишком длинный или обработка заняла слишком много времени.\n\n"
                    "Попробуй отправить более короткий фрагмент или разделить встречу на части."
                )
            elif "format" in error_message.lower() or "неподдерживаемый" in error_message.lower():
                user_message = (
                    "📎 Проблема с форматом файла.\n\n"
                    "Попробуй конвертировать аудио в один из поддерживаемых форматов:\n"
                    "• MP3\n"
                    "• WAV\n"
                    "• OGG\n"
                    "• M4A\n\n"
                    "Или отправь аудио другим способом."
                )
            else:
                user_message = (
                    f"❌ Ошибка при расшифровке аудиозаписи.\n\n"
                    f"Детали: {error_message[:200]}\n\n"
                    "Попробуй:\n"
                    "• Отправить аудио в другом формате\n"
                    "• Проверить интернет-соединение\n"
                    "• Попробовать позже"
                )
            
            # Устанавливаем постоянную клавиатуру
            reply_keyboard = get_reply_keyboard(context)
            
            await update.message.reply_text(
                f"{user_message}\n\n"
                "💡 Режим расшифровки встреч всё ещё активен. Можешь отправить другое аудио.\n\n"
                "Используй кнопки внизу экрана для переключения режима.",
                reply_markup=reply_keyboard,
                parse_mode="Markdown"
            )
            return
        
        if not transcription_result:
            logger.warning("transcription_result пустой или None")
            # Устанавливаем постоянную клавиатуру
            reply_keyboard = get_reply_keyboard(context)
            await update.message.reply_text(
                "❌ Не удалось расшифровать аудиозапись.\n\n"
                "Возможные причины:\n"
                "• Неподдерживаемый формат файла\n"
                "• Проблемы с доступом к API распознавания речи\n"
                "• Аудио слишком длинное или пустое\n\n"
                "Попробуй:\n"
                "• Отправить аудио в формате MP3, WAV, OGG или M4A\n"
                "• Убедиться, что в записи есть речь\n"
                "• Проверить интернет-соединение\n\n"
                "💡 Режим расшифровки встреч всё ещё активен. Можешь отправить другое аудио.\n\n"
                "Используй кнопки внизу экрана для переключения режима.",
                reply_markup=reply_keyboard,
                parse_mode="Markdown"
            )
            return
        
        logger.info(f"Расшифровка успешна. Длина транскрипта: {len(transcription_result.get('transcript', ''))}")
        
        # Генерируем резюме
        logger.info("Генерирую резюме встречи...")
        try:
            summary = await meeting_processor.generate_meeting_summary(
                transcription_result.get('transcript', ''),
                transcription_result.get('raw_text', ''),
                language
            )
            logger.info(f"Резюме сгенерировано. Результат: {summary is not None}")
        except Exception as e:
            logger.error(f"Ошибка при генерации резюме: {e}", exc_info=True)
            # Устанавливаем постоянную клавиатуру
            reply_keyboard = get_reply_keyboard(context)
            await update.message.reply_text(
                f"❌ Ошибка при создании резюме: {str(e)}\n\n"
                "Попробуй еще раз.\n\n"
                "Используй кнопки внизу экрана для переключения режима.",
                reply_markup=reply_keyboard
            )
            return
        
        if not summary:
            logger.warning("summary пустой")
            # Устанавливаем постоянную клавиатуру
            reply_keyboard = get_reply_keyboard(context)
            await update.message.reply_text(
                "Не удалось создать резюме. Попробуй еще раз.\n\n"
                "Используй кнопки внизу экрана для переключения режима.",
                reply_markup=reply_keyboard
            )
            return
        
        # Извлекаем заголовок из резюме для названия встречи
        meeting_title = "Встреча"
        if summary:
            # Пытаемся извлечь название из резюме (первая строка до переноса строки или первые 50 символов)
            title_line = summary.split('\n')[0] if '\n' in summary else summary[:100]
            # Убираем markdown форматирование
            title_line = title_line.replace('**', '').replace('📋', '').strip()
            if title_line:
                meeting_title = title_line[:100]  # Ограничиваем длину
        
        # Сохраняем встречу в БД
        meeting_id = db.save_meeting(
            user_id=user_id,
            title=meeting_title,
            transcript=transcription_result.get('transcript', ''),
            raw_text=transcription_result.get('raw_text', ''),
            summary=summary,
            summary_extended=None,
            segments=transcription_result.get('segments', []),
            duration=int(transcription_result.get('duration', 0))
        )
        
        # Сохраняем данные встречи для дополнительных действий (включая ID из БД)
        context.user_data['last_meeting_data'] = {
            'id': meeting_id,
            'transcript': transcription_result.get('transcript', ''),
            'raw_text': transcription_result.get('raw_text', ''),
            'summary': summary,
            'language': language,
            'segments': transcription_result.get('segments', []),
            'duration': transcription_result.get('duration', 0)
        }
        
        # НЕ выходим из режима - остаемся в режиме расшифровки, чтобы принимать следующие аудио
        # Режим будет сброшен только при явном выходе через кнопку или команду
        
        # Останавливаем typing
        stop_typing = True
        
        # Формируем inline кнопки для дополнительных действий
        keyboard = [
            [InlineKeyboardButton("📄 Показать полный текст встречи", callback_data="meeting_full_transcript")],
            [InlineKeyboardButton("📋 Сделать расширенное резюме", callback_data="meeting_extended_summary")],
            [InlineKeyboardButton("📅 Создать события из встречи", callback_data="meeting_create_events")]
        ]
        inline_markup = InlineKeyboardMarkup(keyboard)
        
        # Устанавливаем постоянную клавиатуру (ReplyKeyboardMarkup)
        reply_keyboard = get_reply_keyboard(context)
        
        # Отправляем резюме с inline кнопками для дополнительных действий
        # Резюме уже содержит жирный заголовок и естественное описание
        await update.message.reply_text(
            f"{summary}\n\n"
            "💡 Режим расшифровки встреч активен. Отправь следующее аудио для расшифровки или выбери действие выше.",
            reply_markup=inline_markup,
            parse_mode="Markdown"
        )
        # Устанавливаем постоянную клавиатуру отдельным сообщением
        # (InlineKeyboardMarkup и ReplyKeyboardMarkup нельзя использовать одновременно в одном сообщении)
        # Постоянная клавиатура будет видна внизу экрана после этого сообщения
        await update.message.reply_text(
            "💡 Используй кнопки внизу экрана для переключения режима или возврата в меню.",
            reply_markup=reply_keyboard
        )
        
    except Exception as e:
        stop_typing = True
        logger.error(f"Ошибка обработки аудио для встречи: {e}", exc_info=True)
        # НЕ сбрасываем режим при ошибке - пользователь может попробовать еще раз
        # Устанавливаем постоянную клавиатуру
        reply_keyboard = get_reply_keyboard(context)
        await update.message.reply_text(
            "Что-то пошло не так при обработке встречи. Попробуй еще раз или отправь аудио в другом формате.\n\n"
            "Режим расшифровки встреч всё ещё активен.\n\n"
            "Используй кнопки внизу экрана для переключения режима.",
            reply_markup=reply_keyboard,
            parse_mode="Markdown"
        )
    
    finally:
        stop_typing = True
        if typing_task:
            typing_task.cancel()
            try:
                await typing_task
            except (asyncio.CancelledError, Exception):
                pass


async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /search."""
    user_id = update.effective_user.id
    
    # Получаем query из аргументов или из сообщения
    query_text = ' '.join(context.args) if context.args else ""
    
    if not query_text:
        await update.message.reply_text("Использование: /search <запрос>")
        return
    
    # Ищем события
    extracted_data = {
        'intent': 'search',
        'title': query_text,
        'description': query_text
    }
    
    if not decision_engine:
        logger.error("decision_engine не инициализирован")
        await update.message.reply_text("Ошибка инициализации. Попробуй перезапустить бота.")
        return
    
    connections = db.get_calendar_connections(user_id)
    result = await decision_engine.process_intent(user_id, extracted_data)
    
    await update.message.reply_text(result['message'])


async def share_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /share для шаринга события."""
    user_id = update.effective_user.id
    
    # Получаем query из аргументов
    query_text = ' '.join(context.args) if context.args else ""
    
    if not query_text:
        await update.message.reply_text("Использование: /share <название события>")
        return
    
    # Ищем событие
    events = db.find_similar_events(user_id, query_text)
    
    if not events:
        await update.message.reply_text(f"Событие '{query_text}' не найдено.")
        return
    
    event = events[0]
    external_id = event.get('external_id')
    provider = event.get('provider')
    
    # Формируем текстовую сводку
    summary = f"📅 {event['title']}\n\n"
    
    if event.get('start_time'):
        from datetime import datetime
        start_dt = datetime.fromisoformat(event['start_time'])
        summary += f"Время: {start_dt.strftime('%d.%m.%Y %H:%M')}\n"
    
    if event.get('location'):
        summary += f"Место: {event['location']}\n"
    
    if event.get('description'):
        summary += f"\n{event['description']}\n"
    
    # Пытаемся получить ICS файл для шаринга
    ics_content = None
    
    if external_id and provider == 'google':
        try:
            calendar = GoogleCalendar(user_id)
            ics_content = calendar.get_event_ics(external_id)
        except Exception as e:
            logger.error(f"Ошибка получения ICS от Google: {e}")
    elif external_id and provider == 'icloud':
        try:
            connections = db.get_calendar_connections(user_id)
            conn = next((c for c in connections if c['provider'] == 'icloud'), None)
            if conn:
                import json
                credentials = json.loads(conn['credentials'])
                from calendar_icloud import ICloudCalendar
                calendar = ICloudCalendar(
                    user_id=user_id,
                    caldav_url=credentials.get('caldav_url'),
                    username=credentials.get('username'),
                    password=credentials.get('password')
                )
                ics_content = calendar.get_event_ics(external_id)
        except Exception as e:
            logger.error(f"Ошибка получения ICS от iCloud: {e}")
    
    # Отправляем сводку
    await update.message.reply_text(summary)
    
    # Отправляем ICS файл если доступен
    if ics_content:
        from io import BytesIO
        ics_file = BytesIO(ics_content.encode('utf-8'))
        ics_file.name = f"{event['title']}.ics"
        await update.message.reply_document(document=ics_file, filename=ics_file.name)
    else:
        await update.message.reply_text("(ICS файл недоступен для этого события)")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Главный обработчик всех сообщений."""
    user_id = update.effective_user.id
    
    # Проверяем наличие web_app_data от веб-приложения (высший приоритет)
    if update.message and hasattr(update.message, 'web_app_data') and update.message.web_app_data:
        try:
            import json
            data_str = update.message.web_app_data.data
            data = json.loads(data_str)
            action = data.get('action')
            
            if action == 'get_events':
                # Веб-приложение запрашивает события
                web_events = await get_events_for_web_app(user_id)
                
                logger.info(f"Веб-приложение запросило события для пользователя {user_id}. Получено {len(web_events)} событий из БД")
                
                # Сохраняем события в user_data для последующего доступа
                context.user_data['last_web_app_events'] = web_events
                context.user_data['last_web_app_events_time'] = datetime.now().isoformat()
                
                import json
                response_data = json.dumps({
                    'action': 'sync_events',
                    'events': web_events,
                    'timestamp': datetime.now().isoformat(),
                    'count': len(web_events)
                }, ensure_ascii=False, default=str)
                context.user_data['last_web_app_events_json'] = response_data
                
                # КРИТИЧЕСКИ ВАЖНО: Telegram Web App не может читать ответы от бота напрямую через sendData
                # Решение: Отправляем данные через обычное сообщение, которое веб-приложение может прочитать
                # через механизм чтения последних сообщений или через копирование вручную
                # Но более правильное решение - использовать механизм через прямое сохранение в localStorage
                # через специальный механизм, который мы реализуем ниже
                
                # Отправляем сообщение с данными в специальном формате
                # Формат: TRACY_EVENTS_SYNC:{base64_encoded_json}
                # Веб-приложение может декодировать это и обновить localStorage
                try:
                    import base64
                    encoded_data = base64.b64encode(response_data.encode('utf-8')).decode('utf-8')
                    
                    # Отправляем сообщение (будет видно в чате, но веб-приложение может его использовать)
                    await update.message.reply_text(
                        f"TRACY_EVENTS_SYNC:{encoded_data}",
                        reply_markup=None,
                        parse_mode=None
                    )
                    logger.info(f"✅ Отправлены {len(web_events)} событий пользователю {user_id} (base64 encoded)")
                    
                    # ДОПОЛНИТЕЛЬНО: Сохраняем события в user_data для доступа через другой механизм
                    # Это позволит веб-приложению получить события при следующем запросе
                    
                except Exception as e:
                    logger.error(f"❌ Ошибка отправки событий через сообщение: {e}", exc_info=True)
                    # Fallback: отправляем короткое подтверждение
                    try:
                        await update.message.reply_text(
                            f"✅ События готовы ({len(web_events)} шт.)",
                            reply_markup=None
                        )
                    except Exception as e2:
                        logger.error(f"❌ Ошибка отправки подтверждения: {e2}")
                
                return
            
            elif action == 'update_notifications':
                # Обновление настроек уведомлений из веб-приложения
                enabled = data.get('enabled', True)
                db.update_user_settings(user_id, settings_dict={'web_notifications_enabled': enabled})
                logger.info(f"Обновлены настройки уведомлений для пользователя {user_id}: {enabled}")
                await update.message.reply_text("✅ Настройки уведомлений обновлены", reply_to_message_id=update.message.message_id)
                return
            
            elif action == 'update_morning_digest':
                # Обновление настроек утреннего дайджеста
                time_str = data.get('time', '09:00')
                default_reminder = data.get('default_reminder', '15')
                digest_enabled = data.get('enabled', True)
                
                settings_update = {
                    'default_reminder_minutes': int(default_reminder) if default_reminder.isdigit() else 15
                }
                
                # Используем morning_digest_time как флаг: если enabled = True, устанавливаем время, иначе NULL
                if digest_enabled:
                    settings_update['morning_digest_time'] = time_str
                    logger.info(f"Обновлены настройки утреннего дайджеста для пользователя {user_id}: включен, время={time_str}")
                else:
                    settings_update['morning_digest_time'] = None  # NULL означает выключен
                    logger.info(f"Обновлены настройки утреннего дайджеста для пользователя {user_id}: выключен")
                
                db.update_user_settings(user_id, settings_dict=settings_update)
                
                status_text = f"включен на {time_str}" if digest_enabled else "выключен"
                await update.message.reply_text(
                    f"✅ Утренний дайджест {status_text}", 
                    reply_to_message_id=update.message.message_id
                )
                return
            
            elif action == 'update_ai_settings':
                # Обновление настроек AI из веб-приложения
                model = data.get('model', 'gpt-4o-mini')
                mode = data.get('mode', 'soft')
                smart_reply = data.get('smart_reply', True)
                # Эти настройки пока сохраняем в user_data, так как они не критичны для БД
                context.user_data['ai_model'] = model
                context.user_data['ai_mode'] = mode
                context.user_data['smart_reply_enabled'] = smart_reply
                logger.info(f"Обновлены настройки AI для пользователя {user_id}: model={model}, mode={mode}, smart_reply={smart_reply}")
                await update.message.reply_text("✅ Настройки ИИ обновлены", reply_to_message_id=update.message.message_id)
                return
            
            elif action == 'get_calendar_status':
                # Получение статуса подключения календарей для веб-приложения
                connections = db.get_calendar_connections(user_id)
                google_connected = any(c['provider'] == 'google' for c in connections)
                icloud_connected = any(c['provider'] == 'icloud' for c in connections)
                
                import json
                import base64
                status_data = json.dumps({
                    'action': 'calendar_status',
                    'google': google_connected,
                    'icloud': icloud_connected,
                    'timestamp': datetime.now().isoformat()
                }, ensure_ascii=False)
                
                encoded_data = base64.b64encode(status_data.encode('utf-8')).decode('utf-8')
                await update.message.reply_text(
                    f"TRACY_CALENDAR_STATUS:{encoded_data}",
                    reply_markup=None,
                    parse_mode=None
                )
                logger.info(f"Отправлен статус календарей для пользователя {user_id}: Google={google_connected}, iCloud={icloud_connected}")
                return
            
            elif action == 'submit_google_oauth_url':
                # Веб-приложение отправляет URL из адресной строки после OAuth (кнопка "Перенести")
                auth_response = (data.get('url') or '').strip()
                if not auth_response:
                    await update.message.reply_text("❌ Не получил URL. Вставь URL и нажми «Перенести» ещё раз.")
                    return
                
                try:
                    # Проверяем, есть ли в URL параметр error (как и в текстовом сценарии)
                    if 'error=' in auth_response.lower():
                        error_params = auth_response.split('?')[-1] if '?' in auth_response else auth_response
                        if 'error=access_denied' in error_params.lower() or 'error=access_blocked' in error_params.lower():
                            await update.message.reply_text(
                                "❌ **Доступ запрещен**\n\n"
                                "Google заблокировал доступ к календарю.\n\n"
                                "**Возможные причины:**\n"
                                "• Google требует дополнительной проверки безопасности\n"
                                "• OAuth приложение не настроено правильно\n"
                                "• Redirect URI не добавлен в список разрешенных\n\n"
                                "**Что делать:**\n"
                                "1. Попробуй использовать другой браузер\n"
                                "2. Войди в Google аккаунт в обычном режиме (не инкогнито)\n"
                                "3. Убедись, что в Google Cloud Console правильно настроен redirect URI\n"
                                "4. Попробуй еще раз через несколько минут\n\n"
                                "Если проблема сохраняется, обратись к администратору бота.",
                                parse_mode="Markdown"
                            )
                            # Сбрасываем ожидание, если оно было включено из /settings
                            context.user_data['waiting_google_url'] = False
                            return
                    
                    calendar = GoogleCalendar(user_id)
                    if calendar.handle_callback(auth_response):
                        db.save_calendar_connection(
                            user_id=user_id,
                            provider='google',
                            calendar_id='primary',
                            credentials=''  # Credentials хранятся в файле
                        )
                        
                        keyboard = [[InlineKeyboardButton("⬅️ Назад в настройки", callback_data="settings_show")]]
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        
                        await update.message.reply_text(
                            "✅ **Google Calendar успешно подключен!**\n\n"
                            "События будут синхронизироваться с твоим Google Calendar.\n\n"
                            "Попробуй создать событие, например:\n"
                            "«Встреча завтра в 15:00»",
                            reply_markup=reply_markup,
                            parse_mode="Markdown"
                        )
                        
                        # Обновляем статус календарей для веб-приложения
                        await send_calendar_status_to_web_app(user_id, context)
                    else:
                        await update.message.reply_text(
                            "❌ **Ошибка подключения Google Calendar**\n\n"
                            "Не удалось обработать URL авторизации.\n\n"
                            "**Проверь:**\n"
                            "• Что скопировал полный URL из адресной строки\n"
                            "• Что URL содержит параметр `code=`\n"
                            "• Что URL начинается с `http://` или `https://`\n\n"
                            "Попробуй еще раз через /settings",
                            parse_mode="Markdown"
                        )
                except Exception as e:
                    logger.error(f"Ошибка обработки Google OAuth из веб-приложения: {e}", exc_info=True)
                    await update.message.reply_text(
                        f"❌ **Ошибка подключения**\n\n"
                        f"Произошла ошибка: {str(e)}\n\n"
                        "Попробуй еще раз через /settings",
                        parse_mode="Markdown"
                    )
                finally:
                    # Сбрасываем ожидание, если оно было включено из /settings
                    context.user_data['waiting_google_url'] = False
                return
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"Ошибка обработки web_app_data: {e}")
            # Продолжаем обычную обработку
    
    # Обработка текстовых команд от постоянной клавиатуры (ВЫСШИЙ ПРИОРИТЕТ)
    if update.message and update.message.text:
        text = update.message.text.strip()
        
        # Команды от постоянной клавиатуры
        if text == "📅 Режим планировщика" or text.lower() in ['режим планировщика', 'планировщик']:
            context.user_data['waiting_meeting_audio'] = False
            # Устанавливаем постоянную клавиатуру для режима планировщика
            reply_keyboard = get_reply_keyboard(context)
            await update.message.reply_text(
                "✅ **Режим планировщика**\n\n"
                "Теперь ты в обычном режиме работы с календарем.",
                reply_markup=reply_keyboard,
                parse_mode="Markdown"
            )
            return
        
        elif text == "🎤 Режим расшифровки встреч" or text.lower() in ['режим расшифровки встреч', 'расшифровка встреч']:
            context.user_data['waiting_meeting_audio'] = True
            # Устанавливаем постоянную клавиатуру для режима расшифровки
            reply_keyboard = get_reply_keyboard(context)
            await update.message.reply_text(
                "🎤 **Режим расшифровки встреч**\n\n"
                "Отправь голосовое сообщение или аудиофайл с записью встречи для расшифровки.\n\n"
                "📎 Поддерживаемые форматы: MP3, M4A, WAV, OGG, OPUS, FLAC, AAC, WMA, AMR, 3GP, MKA и другие аудиоформаты.",
                reply_markup=reply_keyboard,
                parse_mode="Markdown"
            )
            return
        
        elif text == "📋 Меню" or text.lower() == 'меню':
            # Открываем главное меню
            await menu_command(update, context)
            return
    
    # Проверяем, находимся ли мы в режиме ожидания аудио для встречи (ВЫСШИЙ ПРИОРИТЕТ)
    # В этом режиме ВСЕ голосовые сообщения идут на расшифровку встречи, а не на создание событий
    if context.user_data.get('waiting_meeting_audio'):
        # Обработка аудио для встречи - ВСЕ голосовые и аудиофайлы
        if is_audio_file(update.message):
            await handle_meeting_audio(update, context)
            return
        # Текстовые команды для выхода из режима (старые команды, для обратной совместимости)
        elif update.message.text and update.message.text.lower() in ['отмена', 'cancel', 'выход', 'отменить']:
            context.user_data['waiting_meeting_audio'] = False
            # Устанавливаем постоянную клавиатуру для режима планировщика
            reply_keyboard = get_reply_keyboard(context)
            await update.message.reply_text(
                "✅ **Режим планировщика**\n\n"
                "Теперь ты в обычном режиме работы с календарем.",
                reply_markup=reply_keyboard,
                parse_mode="Markdown"
            )
            return
        else:
            # Если не аудио и не команда выхода, напоминаем что нужно отправить аудио
            # НЕ обрабатываем текст как обычное сообщение в режиме расшифровки
            # Добавляем постоянные кнопки режима
            keyboard = get_meeting_mode_footer_buttons(context)
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Проверяем, что это не аудиофайл
            if update.message.document and not is_audio_file(update.message):
                await update.message.reply_text(
                    "❌ **Режим расшифровки встреч активен**\n\n"
                    "Этот файл не является аудиофайлом. Отправь голосовое сообщение или аудиофайл с записью встречи.\n\n"
                    "📎 Поддерживаемые форматы: MP3, M4A, WAV, OGG, OPUS, FLAC, AAC, WMA, AMR, 3GP, MKA и другие аудиоформаты.\n\n"
                    "Используй кнопки ниже для переключения режима или возврата в меню.",
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text(
                    "🎤 **Режим расшифровки встреч активен**\n\n"
                    "Отправь голосовое сообщение или аудиофайл с записью встречи для расшифровки.\n\n"
                    "📎 Поддерживаемые форматы: MP3, M4A, WAV, OGG, OPUS, FLAC, AAC, WMA, AMR, 3GP, MKA и другие аудиоформаты.\n\n"
                    "Используй кнопки ниже для переключения режима или возврата в меню.",
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
            return
    
    # Включаем индикатор "бот печатает"
    try:
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action=ChatAction.TYPING
        )
    except Exception as e:
        logger.warning(f"Ошибка отправки typing action: {e}")
    
    # Логируем тип полученного сообщения для отладки
    message_type = "текст"
    if update.message and update.message.voice:
        message_type = "голосовое"
        logger.info(f"Получено голосовое сообщение от пользователя {user_id}, длительность: {update.message.voice.duration} сек")
    elif update.message and update.message.photo:
        message_type = "изображение"
        logger.info(f"Получено изображение от пользователя {user_id}")
    elif update.message and update.message.document:
        doc = update.message.document
        if is_audio_file(update.message):
            message_type = "аудиофайл"
            logger.info(f"Получен аудиофайл от пользователя {user_id}: {doc.file_name or 'без имени'}, mime_type: {doc.mime_type}")
        elif doc.mime_type and doc.mime_type.startswith('image/'):
            message_type = "изображение (документ)"
            logger.info(f"Получен документ-изображение от пользователя {user_id}: {doc.file_name or 'без имени'}")
        else:
            message_type = "документ"
            logger.info(f"Получен документ от пользователя {user_id}: {doc.file_name or 'без имени'}, mime_type: {doc.mime_type}")
    elif update.message and update.message.text:
        message_type = "текст"
        logger.info(f"Получено текстовое сообщение от пользователя {user_id}")
    
    logger.info(f"Обработка сообщения типа: {message_type} от пользователя {user_id}")
    
    # Если это документ, но не аудио и не изображение, сообщаем об этом
    if update.message and update.message.document:
        doc = update.message.document
        # Если это не аудио и не изображение, не обрабатываем
        if not is_audio_file(update.message) and not (doc.mime_type and doc.mime_type.startswith('image/')):
            await update.message.reply_text(
                "📎 Я могу обрабатывать:\n"
                "• Голосовые сообщения\n"
                "• Аудиофайлы (MP3, M4A, WAV, OGG, OPUS, FLAC, AAC, WMA, AMR, 3GP, MKA и др.)\n"
                "• Изображения и скриншоты\n\n"
                "Этот тип файла пока не поддерживается. Отправь аудиофайл или изображение."
            )
            return
    
    # Проверяем процесс подключения iCloud (пошаговый)
    icloud_step = context.user_data.get('icloud_step')
    if icloud_step:
        if icloud_step == 'email':
            # Шаг 1: Получаем email
            email = update.message.text.strip()
            if '@' not in email:
                await update.message.reply_text(
                    "❌ Неверный формат email!\n\n"
                    "Отправь корректный email адрес, например:\n"
                    "`ivan@icloud.com`",
                    parse_mode="Markdown"
                )
                return
            
            # Сохраняем email и переходим к следующему шагу
            context.user_data['icloud_email'] = email
            context.user_data['icloud_step'] = 'password'
            
            keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data="icloud_cancel")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                f"🔑 **Шаг 2 из 2: Введи пароль приложения**\n\n"
                f"Apple ID: `{email}`\n\n"
                "Отправь пароль приложения (App-Specific Password), который ты создал на appleid.apple.com\n\n"
                "Формат: `xxxx-xxxx-xxxx-xxxx` (16 символов в 4 группах через дефис)\n\n"
                "⚠️ **Важно:** Используй пароль приложения, НЕ обычный пароль Apple ID!",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            return
        
        elif icloud_step == 'password':
            # Шаг 2: Получаем пароль и подключаемся
            password = update.message.text.strip()
            email = context.user_data.get('icloud_email')
            
            # Валидация формата пароля
            if '-' not in password or len(password.replace('-', '')) != 16:
                await update.message.reply_text(
                    "⚠️ Похоже, что это не пароль приложения!\n\n"
                    "Пароль приложения имеет формат:\n"
                    "`xxxx-xxxx-xxxx-xxxx` (16 символов в 4 группах)\n\n"
                    "Убедись, что:\n"
                    "• Используешь пароль из раздела 'Пароли приложений'\n"
                    "• НЕ используешь обычный пароль Apple ID\n"
                    "• Скопировал пароль полностью со всеми дефисами\n\n"
                    "Отправь пароль еще раз:",
                    parse_mode="Markdown"
                )
                return
            
            # Подключаемся к iCloud
            status_msg = await update.message.reply_text(
                f"🔌 Подключаюсь к iCloud Calendar...\n\n"
                f"⏳ Пожалуйста, подожди..."
            )
            
            try:
                from calendar_icloud import ICloudCalendar
                caldav_url = "https://caldav.icloud.com"
                calendar = ICloudCalendar(user_id, caldav_url, email, password)
                
                if calendar.connect():
                    # Сохраняем подключение
                    import json
                    credentials = json.dumps({
                        'caldav_url': caldav_url,
                        'username': email,
                        'password': password
                    })
                    
                    db.save_calendar_connection(
                        user_id=user_id,
                        provider='icloud',
                        calendar_id='primary',
                        credentials=credentials
                    )
                    
                    # Очищаем временные данные
                    context.user_data.pop('icloud_step', None)
                    context.user_data.pop('icloud_email', None)
                    
                    keyboard = [[InlineKeyboardButton("⬅️ Назад в настройки", callback_data="settings_show")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await status_msg.edit_text(
                        "✅ **iCloud Calendar успешно подключен!**\n\n"
                        f"События будут синхронизироваться с календарем `{email}`\n\n"
                        "Попробуй создать событие, например:\n"
                        "«Встреча завтра в 15:00»",
                        reply_markup=reply_markup,
                        parse_mode="Markdown"
                    )
                    
                    # Отправляем обновленный статус календарей в веб-приложение
                    await send_calendar_status_to_web_app(user_id, context)
                else:
                    await status_msg.edit_text(
                        "❌ **Ошибка подключения к iCloud Calendar**\n\n"
                        "Проверь:\n"
                        "✓ Правильность Apple ID (полный email)\n"
                        "✓ Что использован пароль приложения (не основной пароль!)\n"
                        "✓ Формат пароля: `xxxx-xxxx-xxxx-xxxx`\n"
                        "✓ Что включена двухфакторная аутентификация\n\n"
                        "Попробуй еще раз через /settings",
                        parse_mode="Markdown"
                    )
                    context.user_data.pop('icloud_step', None)
                    context.user_data.pop('icloud_email', None)
            
            except Exception as e:
                logger.error(f"Ошибка подключения iCloud: {e}", exc_info=True)
                error_msg = str(e).lower()
                
                if 'authentication' in error_msg or 'unauthorized' in error_msg or '401' in error_msg:
                    detailed_error = (
                        "❌ **Ошибка аутентификации**\n\n"
                        "Возможные причины:\n"
                        "• Неверный Apple ID или пароль\n"
                        "• Использован обычный пароль вместо пароля приложения\n"
                        "• Двухфакторная аутентификация не включена\n\n"
                        "Проверь настройки на appleid.apple.com и попробуй снова."
                    )
                else:
                    detailed_error = f"❌ Ошибка подключения: {str(e)}\n\nПопробуй еще раз через /settings"
                
                await status_msg.edit_text(detailed_error, parse_mode="Markdown")
                context.user_data.pop('icloud_step', None)
                context.user_data.pop('icloud_email', None)
            
            return
    
    # Проверяем, ожидаем ли мы URL подтверждения Google
    if context.user_data.get('waiting_google_url'):
        # Это URL с кодом подтверждения для Google OAuth
        auth_response = update.message.text
        
        try:
            # Проверяем, есть ли в URL параметр error
            if 'error=' in auth_response.lower():
                error_params = auth_response.split('?')[-1] if '?' in auth_response else auth_response
                if 'error=access_denied' in error_params.lower() or 'error=access_blocked' in error_params.lower():
                    await update.message.reply_text(
                        "❌ **Доступ запрещен**\n\n"
                        "Google заблокировал доступ к календарю.\n\n"
                        "**Возможные причины:**\n"
                        "• Google требует дополнительной проверки безопасности\n"
                        "• OAuth приложение не настроено правильно\n"
                        "• Redirect URI не добавлен в список разрешенных\n\n"
                        "**Что делать:**\n"
                        "1. Попробуй использовать другой браузер\n"
                        "2. Войди в Google аккаунт в обычном режиме (не инкогнито)\n"
                        "3. Убедись, что в Google Cloud Console правильно настроен redirect URI\n"
                        "4. Попробуй еще раз через несколько минут\n\n"
                        "Если проблема сохраняется, обратись к администратору бота."
                    )
                    context.user_data['waiting_google_url'] = False
                    return
            
            calendar = GoogleCalendar(user_id)
            
            if calendar.handle_callback(auth_response):
                db.save_calendar_connection(
                    user_id=user_id,
                    provider='google',
                    calendar_id='primary',
                    credentials=''  # Credentials хранятся в файле
                )
                
                keyboard = [[InlineKeyboardButton("⬅️ Назад в настройки", callback_data="settings_show")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    "✅ **Google Calendar успешно подключен!**\n\n"
                    "События будут синхронизироваться с твоим Google Calendar.\n\n"
                    "Попробуй создать событие, например:\n"
                    "«Встреча завтра в 15:00»",
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
                
                # Отправляем обновленный статус календарей в веб-приложение
                await send_calendar_status_to_web_app(user_id, context)
            else:
                await update.message.reply_text(
                    "❌ **Ошибка подключения Google Calendar**\n\n"
                    "Не удалось обработать URL авторизации.\n\n"
                    "**Проверь:**\n"
                    "• Что скопировал полный URL из адресной строки\n"
                    "• Что URL содержит параметр `code=`\n"
                    "• Что URL начинается с `http://` или `https://`\n\n"
                    "Попробуй еще раз через /settings"
                )
        except Exception as e:
            logger.error(f"Ошибка обработки Google OAuth: {e}", exc_info=True)
            error_msg = str(e).lower()
            
            if 'invalid_grant' in error_msg or 'expired' in error_msg:
                detailed_error = (
                    "❌ **Код авторизации истек или недействителен**\n\n"
                    "Код авторизации действителен только несколько минут.\n\n"
                    "**Что делать:**\n"
                    "1. Перейди снова по ссылке авторизации из настроек\n"
                    "2. Сразу скопируй URL из адресной строки\n"
                    "3. Отправь его боту\n\n"
                    "Попробуй еще раз через /settings"
                )
            elif 'redirect_uri_mismatch' in error_msg:
                detailed_error = (
                    "❌ **Ошибка настройки Redirect URI**\n\n"
                    "Redirect URI в настройках Google OAuth не совпадает с указанным.\n\n"
                    "**Это проблема настройки бота.**\n"
                    "Обратитесь к администратору для исправления настроек OAuth."
                )
            else:
                detailed_error = (
                    f"❌ **Ошибка подключения**\n\n"
                    f"Произошла ошибка: {str(e)}\n\n"
                    "Попробуй еще раз через /settings"
                )
            
            await update.message.reply_text(detailed_error, parse_mode="Markdown")
        
        context.user_data['waiting_google_url'] = False
        return
    
    # Извлекаем текст из сообщения (любого типа)
    text = None
    try:
        logger.info(f"Начинаю извлечение текста из сообщения типа: {message_type}")
        # Продолжаем показывать typing во время обработки
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action=ChatAction.TYPING
        )
        # Передаем bot из context
        text = await media_processor.extract_text_from_message(update, bot=context.bot)
        logger.info(f"Извлечен текст: {text[:50] if text else 'None'}...")
    except Exception as e:
        # Логируем ошибку тихо, без технических деталей
        logger.error(f"Ошибка при извлечении текста из сообщения: {e}", exc_info=True)
        # Возвращаем нейтральное сообщение пользователю
        await update.message.reply_text(
            "Не удалось обработать сообщение. Попробуй еще раз или отправь текстовое сообщение."
        )
        return
    
    if not text:
        logger.warning(f"Не удалось извлечь текст из сообщения типа {message_type}")
        # Нейтральный ответ без технических деталей
        await update.message.reply_text(
            "Не удалось распознать сообщение. Попробуй отправить его еще раз или использовать текстовое сообщение."
        )
        return
    
    # Проверяем, является ли это командой
    if not nlp_extractor:
        logger.error("nlp_extractor не инициализирован")
        await update.message.reply_text("Ошибка инициализации. Попробуй перезапустить бота.")
        return
    
    command = nlp_extractor.is_command(text)
    if command and command != "unknown":
        # Обрабатываем команды отдельно (если нужно)
        if command == "settings":
            await settings_command(update, context)
            return
        elif command == "search":
            await search_command(update, context)
            return
    
    # Механизм для периодического обновления typing action во время длительной обработки
    stop_typing = False
    
    async def keep_typing():
        """Периодически обновляет typing action, пока идет обработка."""
        max_iterations = 30  # Максимум 2 минуты (30 * 4 секунды)
        iteration = 0
        while not stop_typing and iteration < max_iterations:
            await asyncio.sleep(4)  # Telegram требует обновление каждые 4-5 секунд
            if stop_typing:
                break
            try:
                await context.bot.send_chat_action(
                    chat_id=update.effective_chat.id,
                    action=ChatAction.TYPING
                )
            except Exception as e:
                logger.debug(f"Ошибка отправки typing action: {e}")
                break
            iteration += 1
    
    # Получаем настройки пользователя ДО try блока (для использования в except)
    user = db.get_or_create_user(user_id)
    timezone = user.get('timezone', 'Europe/Moscow')
    locale = user.get('locale', 'ru_RU')
    
    # Запускаем задачу обновления typing в фоне
    typing_task = None
    try:
        typing_task = asyncio.create_task(keep_typing())
        
        # Получаем контекст последнего события для этого пользователя
        last_event = db.get_last_event(user_id)
        
        # Проверяем, является ли это reply к сообщению (для привязки заметок к событиям)
        reply_to_event = None
        if update.message.reply_to_message:
            # Если это reply, пытаемся найти событие из предыдущего сообщения
            # Можно расширить логику для поиска события по тексту reply_to_message
            reply_to_event = last_event  # Пока используем последнее событие
        
        # Проверяем, что компоненты инициализированы
        if not nlp_extractor:
            logger.error("nlp_extractor не инициализирован")
            await update.message.reply_text("Ошибка инициализации. Попробуй перезапустить бота.")
            return
        
        if not decision_engine:
            logger.error("decision_engine не инициализирован")
            await update.message.reply_text("Ошибка инициализации. Попробуй перезапустить бота.")
            return
        
        # Извлекаем intent и контекст (передаем информацию о последнем событии)
        extracted_data = await nlp_extractor.extract_intent_and_context(
            text, timezone, locale, last_event=last_event, is_reply=bool(update.message.reply_to_message)
        )
        
        # Принимаем решение и выполняем действие
        result = await decision_engine.process_intent(user_id, extracted_data, last_event=last_event, reply_to_event=reply_to_event)
        
        # Форматируем сообщение для лучшей читаемости
        formatted_message = format_message_for_user(result['message'])
        
        # Останавливаем typing перед отправкой ответа
        stop_typing = True
        
        # Устанавливаем постоянную клавиатуру для всех ответов
        reply_keyboard = get_reply_keyboard(context)
        
        # Отправляем результат пользователю с постоянной клавиатурой
        await update.message.reply_text(formatted_message, reply_markup=reply_keyboard)
        
        # Если событие было создано или обновлено, синхронизируем с веб-приложением
        # Отправляем обновленные события сразу после создания, чтобы веб-приложение могло их получить
        if result.get('action') in ['created', 'updated', 'created_draft']:
            # Сразу отправляем обновленные события для синхронизации с веб-приложением
            try:
                web_events = await get_events_for_web_app(user_id)
                import json
                import base64
                
                response_data = json.dumps({
                    'action': 'sync_events',
                    'events': web_events,
                    'timestamp': datetime.now().isoformat(),
                    'count': len(web_events)
                }, ensure_ascii=False, default=str)
                
                # Отправляем события в специальном формате для веб-приложения
                # Веб-приложение может прочитать это сообщение при следующем обновлении
                encoded_data = base64.b64encode(response_data.encode('utf-8')).decode('utf-8')
                
                # Отправляем как отдельное сообщение с данными для веб-приложения
                await update.message.reply_text(
                    f"TRACY_EVENTS_SYNC:{encoded_data}",
                    reply_markup=None,
                    parse_mode=None
                )
                
                logger.info(f"✅ События синхронизированы с веб-приложением: {len(web_events)} событий отправлено пользователю {user_id}")
            except Exception as e:
                logger.error(f"Ошибка синхронизации событий с веб-приложением: {e}", exc_info=True)
            
            # Также обновляем в user_data для последующего доступа
            await sync_events_to_web_app(user_id, context)
    
    except Exception as e:
        # Останавливаем typing при ошибке
        stop_typing = True
        
        # Логируем ошибку тихо с полным traceback
        logger.error(f"Ошибка обработки сообщения: {e}", exc_info=True)
        
        # Генерируем умное сообщение об ошибке через AI
        try:
            user_text = text if text else (update.message.text or update.message.caption or "сообщение")
            
            # Не вызываем NLP в блоке except - это может привести к новой ошибке
            # Используем простой fallback
            extracted_data = {'intent': 'unknown', '_original_text': user_text}
            
            # Генерируем умное сообщение об ошибке (если decision_engine доступен)
            if decision_engine:
                try:
                    error_message = decision_engine._generate_smart_error_message(
                        user_text=user_text,
                        extracted_data=extracted_data,
                        error_context=f"Произошла ошибка при обработке запроса"
                    )
                except Exception as ai_error:
                    logger.error(f"Ошибка генерации AI сообщения: {ai_error}")
                    error_message = "Что-то пошло не так. Попробуй еще раз или сформулируй запрос по-другому."
            else:
                error_message = "Что-то пошло не так. Попробуй еще раз или сформулируй запрос по-другому."
            
            # Устанавливаем постоянную клавиатуру при ошибке
            reply_keyboard = get_reply_keyboard(context)
            await update.message.reply_text(error_message, reply_markup=reply_keyboard)
        except Exception as reply_error:
            logger.error(f"Ошибка генерации/отправки сообщения об ошибке: {reply_error}", exc_info=True)
            # Fallback на простое сообщение
            try:
                reply_keyboard = get_reply_keyboard(context)
                await update.message.reply_text(
                    "Что-то пошло не так. Попробуй еще раз или сформулируй запрос по-другому.",
                    reply_markup=reply_keyboard
                )
            except:
                pass
    
    finally:
        # Останавливаем задачу обновления typing
        stop_typing = True
        if typing_task:
            typing_task.cancel()
            try:
                await typing_task
            except (asyncio.CancelledError, Exception):
                pass


async def sync_events_to_web_app(user_id: int, context: ContextTypes.DEFAULT_TYPE):
    """Синхронизирует события с веб-приложением (вызывается после создания/обновления события)."""
    try:
        # Обновляем события в user_data, чтобы веб-приложение могло их получить при следующем запросе
        web_events = await get_events_for_web_app(user_id)
        context.user_data['last_web_app_events'] = web_events
        context.user_data['last_web_app_events_time'] = datetime.now().isoformat()
        
        import json
        response_data = json.dumps({
            'action': 'sync_events',
            'events': web_events,
            'timestamp': datetime.now().isoformat(),
            'count': len(web_events)
        }, ensure_ascii=False)
        context.user_data['last_web_app_events_json'] = response_data
        
        logger.info(f"События синхронизированы для пользователя {user_id}: {len(web_events)} событий готовы для веб-приложения")
    except Exception as e:
        logger.error(f"Ошибка синхронизации событий: {e}", exc_info=True)


async def send_calendar_status_to_web_app(user_id: int, context: ContextTypes.DEFAULT_TYPE):
    """Отправляет статус подключения календарей в веб-приложение."""
    try:
        connections = db.get_calendar_connections(user_id)
        google_connected = any(c['provider'] == 'google' for c in connections)
        icloud_connected = any(c['provider'] == 'icloud' for c in connections)
        
        import json
        import base64
        status_data = json.dumps({
            'action': 'calendar_status',
            'google': google_connected,
            'icloud': icloud_connected,
            'timestamp': datetime.now().isoformat()
        }, ensure_ascii=False)
        
        # Сохраняем статус в user_data для доступа через веб-приложение
        context.user_data['last_calendar_status'] = status_data
        context.user_data['last_calendar_status_time'] = datetime.now().isoformat()
        
        logger.info(f"Статус календарей обновлен для пользователя {user_id}: Google={google_connected}, iCloud={icloud_connected}")
    except Exception as e:
        logger.error(f"Ошибка отправки статуса календарей: {e}", exc_info=True)


async def get_events_for_web_app(user_id: int) -> List[Dict]:
    """Получить события пользователя в формате для веб-приложения."""
    try:
        from datetime import timedelta
        import pytz
        
        user = db.get_or_create_user(user_id)
        timezone = user.get('timezone', 'Europe/Moscow')
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)
        
        # Получаем события за период (3 месяца назад - 1 год вперед)
        start_from = now - timedelta(days=90)
        start_to = now + timedelta(days=365)
        
        events = db.get_events(user_id, limit=200, start_from=start_from, start_to=start_to)
        logger.info(f"📊 Получено {len(events)} событий из БД для пользователя {user_id} (период: {start_from.date()} - {start_to.date()})")
        
        # Преобразуем события в формат для веб-приложения
        web_events = []
        for event in events:
            start_time = event.get('start_time')
            end_time = event.get('end_time')
            
            # Конвертируем datetime в ISO строку
            if isinstance(start_time, datetime):
                start_iso = start_time.isoformat()
            elif isinstance(start_time, str):
                start_iso = start_time
            else:
                continue
            
            if isinstance(end_time, datetime):
                end_iso = end_time.isoformat()
            elif isinstance(end_time, str):
                end_iso = end_time
            else:
                # Если нет end_time, добавляем час
                if isinstance(start_time, datetime):
                    end_iso = (start_time + timedelta(hours=1)).isoformat()
                else:
                    continue
            
            web_events.append({
                'id': str(event.get('id', '')),
                'title': event.get('title', 'Без названия'),
                'startAt': start_iso,
                'endAt': end_iso,
                'allDay': False,
                'description': event.get('description'),
                'location': event.get('location'),
                'calendarSource': {
                    'color': '#3b82f6',
                    'name': 'TRACY'
                }
            })
        
        logger.info(f"✅ Подготовлено {len(web_events)} событий для веб-приложения пользователя {user_id}")
        return web_events
    except Exception as e:
        logger.error(f"❌ Ошибка получения событий для веб-приложения: {e}", exc_info=True)
        return []




async def connect_icloud_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /connect_icloud."""
    user_id = update.effective_user.id
    
    if len(context.args) < 2:
        detailed_help = """❌ Недостаточно параметров!

📋 Формат команды:
/connect_icloud <apple_id> <app_password>

🔐 Как получить App-Specific Password:

ШАГ 1: Включи двухфакторную аутентификацию
   • Перейди на appleid.apple.com
   • Если не включена - включи в разделе "Безопасность"

ШАГ 2: Создай пароль приложения
   1. На appleid.apple.com → "Безопасность"
   2. Найди "Пароли приложений" (App-Specific Passwords)
   3. Нажми "Создать пароль..." (Generate Password...)
   4. Название: "TRACY Bot"
   5. ⚠️ Скопируй пароль (показывается только раз!)
      Формат: xxxx-xxxx-xxxx-xxxx

ШАГ 3: Используй в команде
   /connect_icloud твой_email@icloud.com xxxx-xxxx-xxxx-xxxx

💡 Важно: Используй App-Specific Password, НЕ обычный пароль!
   
❓ Нужна помощь? Напиши /help"""
        
        await update.message.reply_text(detailed_help)
        return
    
    apple_id = context.args[0].strip()
    app_password = ' '.join(context.args[1:]).strip()  # Пароль может содержать дефисы, берем все остальное
    
    # Валидация формата
    if '@' not in apple_id:
        await update.message.reply_text(
            "❌ Неверный формат Apple ID!\n\n"
            "Apple ID должен быть email адресом, например:\n"
            "ivan@icloud.com\n"
            "или\n"
            "ivan@gmail.com (если используется как Apple ID)"
        )
        return
    
    # Проверяем формат пароля (App-Specific Password: xxxx-xxxx-xxxx-xxxx)
    if '-' not in app_password or len(app_password.replace('-', '')) != 16:
        await update.message.reply_text(
            "⚠️ Похоже, что это не App-Specific Password!\n\n"
            "App-Specific Password имеет формат:\n"
            "xxxx-xxxx-xxxx-xxxx (16 символов в 4 группах)\n\n"
            "Убедись, что:\n"
            "1. Используешь пароль из раздела 'Пароли приложений'\n"
            "2. НЕ используешь обычный пароль Apple ID\n"
            "3. Скопировал пароль полностью со всеми дефисами\n\n"
            "Если не знаешь, как создать App-Specific Password, используй:\n"
            "/settings → iCloud Calendar (там подробная инструкция)"
        )
        return
    
    caldav_url = "https://caldav.icloud.com"
    
    status_msg = await update.message.reply_text(
        f"🔌 Подключаюсь к iCloud Calendar...\n\n"
        f"Apple ID: {apple_id}\n"
        f"⏳ Пожалуйста, подожди..."
    )
    
    try:
        from calendar_icloud import ICloudCalendar
        calendar = ICloudCalendar(user_id, caldav_url, apple_id, app_password)
        
        if calendar.connect():
            # Сохраняем подключение
            import json
            credentials = json.dumps({
                'caldav_url': caldav_url,
                'username': apple_id,
                'password': app_password
            })
            
            db.save_calendar_connection(
                user_id=user_id,
                provider='icloud',
                calendar_id='primary',
                credentials=credentials
            )
            
            await status_msg.edit_text(
                "✅ iCloud Calendar успешно подключен!\n\n"
                f"Теперь события будут синхронизироваться с календарем {apple_id}\n\n"
                "Попробуй создать событие, например:\n"
                "«Встреча завтра в 15:00»"
            )
            
            # Отправляем обновленный статус календарей в веб-приложение
            await send_calendar_status_to_web_app(user_id, context)
        else:
            await status_msg.edit_text(
                "❌ Ошибка подключения к iCloud Calendar\n\n"
                "Проверь:\n"
                "✓ Правильность Apple ID (полный email)\n"
                "✓ Что использован App-Specific Password (не основной пароль!)\n"
                "✓ Формат пароля: xxxx-xxxx-xxxx-xxxx\n"
                "✓ Что включена двухфакторная аутентификация\n"
                "✓ Что интернет соединение стабильно\n\n"
                "Если проблема сохраняется:\n"
                "• Создай новый App-Specific Password\n"
                "• Убедись, что используешь пароль из раздела 'Пароли приложений'"
            )
    
    except Exception as e:
        error_msg = str(e).lower()
        logger.error(f"Ошибка подключения iCloud: {e}", exc_info=True)
        
        if 'authentication' in error_msg or 'unauthorized' in error_msg or '401' in error_msg:
            detailed_error = (
                "❌ Ошибка аутентификации\n\n"
                "Возможные причины:\n"
                "• Неверный Apple ID или пароль\n"
                "• Использован обычный пароль вместо App-Specific Password\n"
                "• Пароль скопирован не полностью\n\n"
                "Решение:\n"
                "1. Перейди на appleid.apple.com\n"
                "2. Создай НОВЫЙ App-Specific Password\n"
                "3. Скопируй его полностью (включая дефисы)\n"
                "4. Попробуй снова: /connect_icloud <apple_id> <новый_пароль>"
            )
        elif 'connection' in error_msg or 'network' in error_msg:
            detailed_error = (
                "❌ Ошибка подключения\n\n"
                "Проверь интернет соединение и попробуй снова."
            )
        else:
            detailed_error = (
                f"❌ Ошибка подключения: {str(e)}\n\n"
                "Попробуй:\n"
                "1. Проверить правильность данных\n"
                "2. Создать новый App-Specific Password\n"
                "3. Убедиться, что двухфакторная аутентификация включена"
            )
        
        await status_msg.edit_text(detailed_error)


def main():
    """Запуск бота."""
    if not config.TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN не установлен в .env")
    
    # Создаем приложение
    application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
    
    # Инициализируем планировщик напоминаний и decision_engine
    global reminder_scheduler, decision_engine
    # Инициализируем AI клиент для reminder_scheduler
    from openai import OpenAI
    ai_client = OpenAI(
        api_key=config.OPENROUTER_API_KEY,
        base_url=config.OPENROUTER_BASE_URL
    )
    reminder_scheduler = ReminderScheduler(application.bot, db, ai_client=ai_client)
    # Передаем AI клиент из nlp_extractor для подбора эмодзи
    decision_engine = DecisionEngine(db, reminder_scheduler, ai_client=nlp_extractor.client)
    
    # Запускаем планировщик напоминаний через post_init хук
    async def post_init(app: Application) -> None:
        """Инициализация после запуска бота."""
        try:
            logger.info("🚀 Инициализация ReminderScheduler...")
            # Обновляем ссылку на bot перед запуском (на случай если application был пересоздан)
            if not reminder_scheduler:
                logger.error("reminder_scheduler не инициализирован")
                raise Exception("reminder_scheduler не инициализирован")
            
            reminder_scheduler.bot = app.bot
            await reminder_scheduler.start()
            logger.info("✅ ReminderScheduler запущен и работает")
            
            # Делаем первую проверку сразу после запуска
            if reminder_scheduler:
                logger.info("🔍 Выполняю первую проверку напоминаний...")
                await reminder_scheduler._check_and_send_reminders()
            else:
                logger.error("reminder_scheduler не инициализирован для проверки напоминаний")
            logger.info("✅ Первая проверка напоминаний завершена")
            
            # Устанавливаем Menu Button для веб-приложения (глобально для всех чатов)
            web_url = os.getenv("WEB_APP_URL")
            if web_url and "localhost" not in web_url.lower() and web_url.startswith("https://"):
                try:
                    menu_button = MenuButtonWebApp(text="TRACY", web_app=WebAppInfo(url=web_url))
                    # Устанавливаем глобально (chat_id=None означает глобальная настройка)
                    await app.bot.set_chat_menu_button(chat_id=None, menu_button=menu_button)
                    logger.info(f"✅ Menu Button установлен: {web_url}")
                except Exception as e:
                    logger.warning(f"⚠️ Не удалось установить Menu Button: {e}")
            else:
                logger.info("⚠️ WEB_APP_URL не настроен или не HTTPS, Menu Button не установлен")
            
            # Устанавливаем команды бота (для меню команд)
            try:
                commands = [
                    BotCommand("start", "Начать работу с ботом"),
                    BotCommand("menu", "Открыть меню"),
                    BotCommand("settings", "Настройки календарей"),
                    BotCommand("help", "Как пользоваться"),
                ]
                await app.bot.set_my_commands(commands)
                logger.info("✅ Команды бота установлены")
            except Exception as e:
                logger.warning(f"⚠️ Не удалось установить команды бота: {e}")
            
            # Устанавливаем описание и короткое описание бота для поиска
            try:
                bot_description = "🤖 TRACY — ваш AI-ассистент для управления календарем. Создавайте события, управляйте напоминаниями и расшифровывайте встречи."
                bot_short_description = "AI-ассистент для управления календарем и расшифровки встреч"
                await app.bot.set_my_description(description=bot_description)
                await app.bot.set_my_short_description(short_description=bot_short_description)
                logger.info("✅ Описание бота установлено")
            except Exception as e:
                logger.warning(f"⚠️ Не удалось установить описание бота: {e}")
        except Exception as e:
            logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА запуска ReminderScheduler: {e}", exc_info=True)
            import traceback
            logger.error(f"Трассировка ошибки запуска ReminderScheduler:\n{traceback.format_exc()}")
    
    # Используем post_init через builder (пересоздаем application)
    application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).post_init(post_init).build()
    
    # ОБЯЗАТЕЛЬНО обновляем ссылку на bot в scheduler после пересоздания
    # Это критически важно, иначе планировщик не сможет отправлять сообщения!
    if reminder_scheduler:
        reminder_scheduler.bot = application.bot
        logger.info(f"✅ Обновлена ссылка на bot в ReminderScheduler: {application.bot is not None}")
    else:
        logger.error("reminder_scheduler не инициализирован для обновления bot ссылки")
    
    # Добавляем обработчик ошибок
    async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик глобальных ошибок."""
        from telegram.error import Conflict, TimedOut, NetworkError
        
        error = context.error
        
        # Обрабатываем Conflict отдельно (другой экземпляр бота запущен)
        if isinstance(error, Conflict):
            logger.error("Обнаружен конфликт: запущен другой экземпляр бота. Остановите другие экземпляры и перезапустите.")
            # Не отправляем сообщение пользователю и не прерываем работу
            # Просто логируем и продолжаем попытки
            return
        
        # Обрабатываем таймауты и сетевые ошибки
        if isinstance(error, (TimedOut, NetworkError)):
            logger.warning(f"Сетевая ошибка: {error}. Продолжаю работу...")
            return
        
        # Для остальных ошибок логируем
        logger.error(f"Exception while handling an update: {error}", exc_info=error)
    
    application.add_error_handler(error_handler)
    
    # Регистрируем обработчики (команды имеют приоритет)
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("menu", menu_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("settings", settings_command))
    # Команды /web, /search, /share убраны из меню, но остаются доступными для использования
    application.add_handler(CommandHandler("web", web_command))
    application.add_handler(CommandHandler("search", search_command))
    application.add_handler(CommandHandler("share", share_command))
    application.add_handler(CommandHandler("connect_icloud", connect_icloud_command))
    application.add_handler(CallbackQueryHandler(settings_callback, pattern="^settings_"))
    application.add_handler(CallbackQueryHandler(settings_callback, pattern="^meeting_"))
    application.add_handler(CallbackQueryHandler(settings_callback, pattern="^help_"))
    application.add_handler(CallbackQueryHandler(settings_callback, pattern="^menu_"))
    application.add_handler(CallbackQueryHandler(settings_callback, pattern="^mode_"))
    application.add_handler(CallbackQueryHandler(settings_callback, pattern="^disconnect_"))
    application.add_handler(CallbackQueryHandler(settings_callback, pattern="^icloud_"))
    application.add_handler(CallbackQueryHandler(settings_callback, pattern="^notifications_"))
    application.add_handler(CallbackQueryHandler(settings_callback, pattern="^reminder_set_"))
    
    # Обработчик голосовых сообщений (отдельно для лучшей отладки)
    application.add_handler(MessageHandler(
        filters.VOICE,
        handle_message
    ))
    
    # Обработчик изображений (перед обработчиком документов, чтобы не перехватывать их)
    application.add_handler(MessageHandler(
        filters.PHOTO | filters.Document.IMAGE,
        handle_message
    ))
    
    # Обработчик документов (включая аудиофайлы)
    # Проверку на аудио делаем внутри handle_message
    application.add_handler(MessageHandler(
        filters.Document.ALL,  # Все документы, проверку делаем внутри
        handle_message
    ))
    
    # Обработчик текстовых сообщений (последним, чтобы не перехватывать команды)
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,  # Только текст, исключая команды
        handle_message
    ))
    
    # Запускаем бота
    logger.info("Запуск бота TRACY...")
    try:
        application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)


if __name__ == "__main__":
    main()
