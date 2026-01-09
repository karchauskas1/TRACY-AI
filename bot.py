"""Основной модуль Telegram бота TRACY."""
import logging
import asyncio
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, MenuButtonWebApp, BotCommand
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
        
        keyboard = [[InlineKeyboardButton("📅 Режим планировщика", callback_data="mode_planner")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🎤 **Режим работы с записями встреч**\n\n"
            "Вы вошли в режим расшифровки встреч. Чтобы продолжить и расшифровать встречу, отправьте голосовое сообщение или аудиофайл с записью встречи.\n\n"
            "Бот обработает запись, создаст расшифровку с тайм-кодами и структурированное резюме.\n\n"
            "📎 Поддерживаемые форматы: MP3, M4A, WAV, OGG",
            reply_markup=reply_markup,
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
    
    # Кнопка для веб-приложения
    web_url = os.getenv("WEB_APP_URL", "http://localhost:3000")
    if "localhost" not in web_url.lower() and web_url.startswith("https://"):
        try:
            keyboard.append([InlineKeyboardButton(
                "🌐 Открыть веб-приложение",
                web_app=WebAppInfo(url=web_url)
            )])
        except:
            pass
    
    # Кнопка меню
    keyboard.append([InlineKeyboardButton("📋 Меню", callback_data="menu_show")])
    # Кнопка помощи
    keyboard.append([InlineKeyboardButton("❓ Как пользоваться", callback_data="help_show")])
    
    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
    
    await update.message.reply_text(
        welcome_message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /menu."""
    keyboard = [
        [InlineKeyboardButton("🎤 Режим резюмирования встреч", callback_data="mode_meeting_transcribe")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "📋 **Меню TRACY**\n\n"
        "Выберите действие:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help."""
    # Генерируем структурированный ответ через AI
    help_text = await generate_structured_help_response()
    await update.message.reply_text(help_text)


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
4. Команды

Формат ответа должен быть таким, как в примере:
"Когда ты мне пишешь, я делаю так:

1. Сначала читаю твоё сообщение — текст, голос, картинку или скриншот.
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

1. Сначала читаю твоё сообщение — текст, голос, картинку или скриншот.
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


async def generate_icloud_instructions(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Генерирует подробную инструкцию для подключения iCloud через AI."""
    try:
        # Используем AI для генерации понятной инструкции на русском
        prompt = """Создай подробную пошаговую инструкцию на русском языке для подключения iCloud Calendar к боту через CalDAV.

Требования:
1. Нужно создать App-Specific Password (пароль приложения)
2. Должна быть включена двухфакторная аутентификация
3. Инструкция должна быть максимально понятной для обычного пользователя
4. Включи конкретные примеры и предупреждения
5. Объясни, где именно найти нужные настройки на appleid.apple.com
6. Используй эмодзи для визуального разделения разделов
7. Объясни разницу между обычным паролем и App-Specific Password

Формат вывода: структурированный текст с шагами, примерами и важными замечаниями."""
        
        response = nlp_extractor.client.chat.completions.create(
            model=config.OPENROUTER_MODEL,
            messages=[
                {"role": "system", "content": "Ты помощник, который создает понятные инструкции для пользователей. Отвечай только текстом инструкции, без дополнительных пояснений."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800
        )
        
        ai_instructions = response.choices[0].message.content.strip()
        
        # Добавляем стандартную информацию о команде
        return f"{ai_instructions}\n\n" \
               f"📝 После создания пароля используй команду:\n" \
               f"/connect_icloud <твой_apple_id@example.com> <app-specific-пароль>\n\n" \
               f"💡 Пример:\n" \
               f"/connect_icloud ivan@icloud.com abcd-efgh-ijkl-mnop"
    
    except Exception as e:
        logger.error(f"Ошибка генерации AI инструкции: {e}")
        # Fallback на статическую инструкцию
        return """📋 ПОДРОБНАЯ ИНСТРУКЦИЯ: Подключение iCloud Calendar

🔐 ШАГ 1: Включи двухфакторную аутентификацию
   1. Открой appleid.apple.com в браузере
   2. Войди в свой Apple ID
   3. Перейди в раздел "Безопасность"
   4. Если видишь "Двухфакторная аутентификация: Выкл" - включи её
   5. Следуй инструкциям для активации

🔑 ШАГ 2: Создай App-Specific Password
   1. На appleid.apple.com перейди в "Безопасность"
   2. Прокрути вниз до раздела "Пароли приложений"
   3. Нажми кнопку "Создать пароль..." или "Generate Password..."
   4. В появившемся окне введи название: "TRACY Bot"
   5. Нажми "Создать" или "Create"
   6. ⚠️ КРИТИЧЕСКИ ВАЖНО: Скопируй пароль СРАЗУ!
      Пароль показывается только один раз и имеет вид:
      xxxx-xxxx-xxxx-xxxx
      (16 символов, разделенных на 4 группы дефисами)
   7. Сохрани пароль в безопасном месте

📝 ШАГ 3: Подключи в боте
   Отправь команду:
   /connect_icloud твой_email@icloud.com xxxx-xxxx-xxxx-xxxx
   
   Пример:
   /connect_icloud ivan@icloud.com abcd-efgh-ijkl-mnop

⚠️ ВАЖНЫЕ ЗАМЕЧАНИЯ:
   • Используй ТОЛЬКО App-Specific Password, НЕ обычный пароль!
   • Пароль должен содержать дефисы между группами
   • Если забыл пароль - создай новый (старый нельзя увидеть снова)
   • Один App-Specific Password можно использовать для нескольких приложений

❓ Частые проблемы:
   • "Неверный пароль" → Убедись, что используешь App-Specific Password
   • "Двухфакторная аутентификация не включена" → Включи её на appleid.apple.com
   • "Неверный формат" → Проверь, что скопировал пароль полностью со всеми дефисами"""


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
                        "1. Нажми на кнопку ниже для авторизации\n"
                        "2. Разреши доступ к календарю\n"
                        "3. После редиректа скопируй ПОЛНЫЙ URL из адресной строки\n"
                        "4. Отправь этот URL боту в ответ на это сообщение\n\n"
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
                    await query.edit_message_text(
                        f"❌ Ошибка подключения Google Calendar.\n\n"
                        f"Проверь настройки GOOGLE_CLIENT_ID и GOOGLE_CLIENT_SECRET.\n"
                        f"Ошибка: {str(e)}",
                        reply_markup=reply_markup
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
        # Показываем меню с опциями
        keyboard = [
            [InlineKeyboardButton("🎤 Режим резюмирования встреч", callback_data="mode_meeting_transcribe")],
            [InlineKeyboardButton("📅 Режим планировщика", callback_data="mode_planner")],
            [InlineKeyboardButton("⚙️ Настройки", callback_data="settings_show")],
            [InlineKeyboardButton("❓ Как пользоваться", callback_data="help_show")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📋 **Меню TRACY**\n\n"
            "Выберите режим работы или действие:",
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
        # Показываем помощь (быстрый статический ответ)
        help_text = """📖 **Как пользоваться TRACY**

Когда ты мне пишешь, я делаю так:

1. Сначала читаю твоё сообщение — текст, голос, картинку или скриншот.
2. Извлекаю из него ключевую информацию о событии или напоминании (что, когда, где).
3. Создаю или обновляю событие в твоём календаре.
4. Если нужно, устанавливаю напоминание, чтобы вовремя тебя уведомить.
5. Отвечаю тебе, подтверждая, что событие добавлено или изменено.
6. Если ты хочешь, могу искать события, удалять их или делиться ими с друзьями.
7. Если ты отправляешь "/settings", показываю меню настроек для управления календарями, уведомлениями и прочим.

📝 **Примеры использования:**
• "Встреча с командой завтра в 15:00"
• "Напомни про доклад в пятницу"
• "Уборка в среду утром"
• "Какие у меня планы на ближайшую неделю?"
• "Удали все события на сегодня"

🔧 **Команды:**
• /settings — подключить Google/iCloud календарь, настроить параметры
• /search <текст> — найти события
• /share <событие> — поделиться событием (ICS файл)

💡 **Подсказка:** Бот работает без подключения календарей! Все события сохраняются, напоминания приходят. Подключение календарей — это дополнительная функция для синхронизации с твоим привычным календарем.

Короче, ты просто говоришь, что нужно, а я организую твой график и напомню! 😉"""
        
        keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="menu_show")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(help_text, reply_markup=reply_markup, parse_mode="Markdown")
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
                # Показываем сообщение о загрузке, затем генерируем инструкцию
                await query.edit_message_text("⏳ Генерирую подробную инструкцию...")
                # Генерируем подробную инструкцию через AI для лучшего понимания
                instructions = await generate_icloud_instructions(user_id, context)
                keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="settings_show")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(instructions, reply_markup=reply_markup)
        except Exception as e:
            logger.error(f"Ошибка в settings_icloud: {e}", exc_info=True)
            keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="settings_show")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ Произошла ошибка при обработке запроса.\n"
                "Попробуй снова через /settings",
                reply_markup=reply_markup
            )
    
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
        keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="settings_show")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "Настройки уведомлений:\n\n"
            "В разработке. Сейчас все подтверждения отправляются в Telegram.",
            reply_markup=reply_markup
        )
    
    elif data == "mode_planner":
        # Выход из режима расшифровки встреч в обычный режим планировщика
        context.user_data['waiting_meeting_audio'] = False
        await query.answer("Переключено в режим планировщика")
        
        keyboard = [
            [InlineKeyboardButton("🎤 Режим расшифровки встреч", callback_data="mode_meeting_transcribe")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="menu_show")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📅 **Режим планировщика**\n\n"
            "Теперь вы в обычном режиме работы с календарем.\n\n"
            "Можете:\n"
            "• Создавать события из текста, голоса или фото\n"
            "• Управлять напоминаниями\n"
            "• Просматривать и редактировать события",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return
    
    elif data == "mode_meeting_transcribe":
        # Переход в режим расшифровки встреч
        context.user_data['waiting_meeting_audio'] = True
        await query.answer("Переключено в режим расшифровки встреч")
        
        keyboard = [
            [InlineKeyboardButton("📅 Режим планировщика", callback_data="mode_planner")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="menu_show")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🎤 **Режим работы с записями встреч**\n\n"
            "Вы вошли в режим расшифровки встреч. Чтобы продолжить и расшифровать встречу, отправьте голосовое сообщение или аудиофайл с записью встречи.\n\n"
            "Бот обработает запись, создаст расшифровку с тайм-кодами и структурированное резюме.\n\n"
            "📎 Поддерживаемые форматы: MP3, M4A, WAV, OGG",
            reply_markup=reply_markup,
            parse_mode="Markdown"
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
                [InlineKeyboardButton("📅 Создать события из встречи", callback_data="meeting_create_events")],
                [InlineKeyboardButton("📅 Режим планировщика", callback_data="mode_planner")]
            ]
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
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🎤 **Создание резюме встречи**\n\n"
            "Отправь голосовое сообщение или аудиофайл с записью встречи.\n\n"
            "Бот обработает запись, создаст расшифровку с тайм-кодами и структурированное резюме.",
            reply_markup=reply_markup
        )
    
    elif data.startswith("meeting_") and data != "meeting_create_summary":
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
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Если текст слишком длинный, отправляем как отдельное сообщение
            if len(transcript) > 4000:
                await query.message.reply_text(
                    f"📄 **Полная расшифровка встречи**\n\n{transcript}",
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
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
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if extended_summary:
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
                        result = await decision_engine.process_intent(
                            user_id,
                            {**event_data, 'intent': 'event'},
                            last_event=None
                        )
                        if result.get('action') == 'created':
                            created_count += 1
                    except Exception as e:
                        logger.error(f"Ошибка создания события из встречи: {e}")
                
                keyboard = [
                    [InlineKeyboardButton("📄 Показать полный текст", callback_data="meeting_full_transcript")],
                    [InlineKeyboardButton("📋 Сделать расширенное резюме", callback_data="meeting_extended_summary")],
                    [InlineKeyboardButton("⬅️ Назад к резюме", callback_data="meeting_back_to_summary")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.message.reply_text(
                    f"✅ Создано событий из встречи: {created_count}\n\n"
                    f"События добавлены в твой календарь.",
                    reply_markup=reply_markup
                )
            else:
                keyboard = [
                    [InlineKeyboardButton("📄 Показать полный текст", callback_data="meeting_full_transcript")],
                    [InlineKeyboardButton("📋 Сделать расширенное резюме", callback_data="meeting_extended_summary")],
                    [InlineKeyboardButton("⬅️ Назад к резюме", callback_data="meeting_back_to_summary")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.message.reply_text(
                    "Не найдено событий с конкретными датами в расшифровке встречи.",
                    reply_markup=reply_markup
                )


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
        if update.message.voice:
            voice = update.message.voice
            audio_file = await context.bot.get_file(voice.file_id)
        elif update.message.document:
            doc = update.message.document
            audio_file = await context.bot.get_file(doc.file_id)
        
        if not audio_file:
            await update.message.reply_text("Не удалось получить аудиофайл. Попробуй еще раз.")
            return
        
        # Получаем настройки пользователя
        user = db.get_or_create_user(user_id)
        language = user.get('locale', 'ru_RU').split('_')[0]  # Извлекаем язык
        
        # Расшифровываем аудио
        logger.info("Начинаю расшифровку аудио для встречи...")
        transcription_result = await meeting_processor.transcribe_meeting_audio(audio_file, language)
        
        if not transcription_result:
            await update.message.reply_text(
                "Не удалось расшифровать аудиозапись. Проверь формат файла и попробуй еще раз."
            )
            return
        
        # Генерируем резюме
        logger.info("Генерирую резюме встречи...")
        summary = await meeting_processor.generate_meeting_summary(
            transcription_result.get('transcript', ''),
            transcription_result.get('raw_text', ''),
            language
        )
        
        if not summary:
            await update.message.reply_text(
                "Не удалось создать резюме. Попробуй еще раз."
            )
            return
        
        # Сохраняем данные встречи для дополнительных действий
        context.user_data['last_meeting_data'] = {
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
        
        # Формируем кнопки для дополнительных действий
        keyboard = [
            [InlineKeyboardButton("📄 Показать полный текст встречи", callback_data="meeting_full_transcript")],
            [InlineKeyboardButton("📋 Сделать расширенное резюме", callback_data="meeting_extended_summary")],
            [InlineKeyboardButton("📅 Создать события из встречи", callback_data="meeting_create_events")],
            [InlineKeyboardButton("📅 Режим планировщика", callback_data="mode_planner")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Отправляем резюме с кнопками и напоминанием о режиме
        await update.message.reply_text(
            f"📋 **Резюме встречи**\n\n{summary}\n\n"
            "💡 Режим расшифровки встреч активен. Отправь следующее аудио для расшифровки или выбери действие выше.",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        stop_typing = True
        logger.error(f"Ошибка обработки аудио для встречи: {e}", exc_info=True)
        # НЕ сбрасываем режим при ошибке - пользователь может попробовать еще раз
        keyboard = [[InlineKeyboardButton("📅 Режим планировщика", callback_data="mode_planner")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "Что-то пошло не так при обработке встречи. Попробуй еще раз или отправь аудио в другом формате.\n\n"
            "Режим расшифровки встреч всё ещё активен.",
            reply_markup=reply_markup,
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
    
    # Проверяем, находимся ли мы в режиме ожидания аудио для встречи (ВЫСШИЙ ПРИОРИТЕТ)
    # В этом режиме ВСЕ голосовые сообщения идут на расшифровку встречи, а не на создание событий
    if context.user_data.get('waiting_meeting_audio'):
        # Обработка аудио для встречи - ВСЕ голосовые и аудиофайлы
        if update.message.voice or (update.message.document and update.message.document.mime_type and 'audio' in update.message.document.mime_type):
            await handle_meeting_audio(update, context)
            return
        # Текстовые команды для выхода из режима
        elif update.message.text and update.message.text.lower() in ['отмена', 'cancel', 'выход', 'отменить', 'режим планировщика']:
            context.user_data['waiting_meeting_audio'] = False
            keyboard = [[InlineKeyboardButton("🎤 Режим расшифровки встреч", callback_data="mode_meeting_transcribe")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "📅 **Режим планировщика**\n\n"
                "Теперь вы в обычном режиме работы с календарем.\n\n"
                "Можете:\n"
                "• Создавать события из текста, голоса или фото\n"
                "• Управлять напоминаниями\n"
                "• Просматривать и редактировать события",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            return
        else:
            # Если не аудио и не команда выхода, напоминаем что нужно отправить аудио
            # НЕ обрабатываем текст как обычное сообщение в режиме расшифровки
            keyboard = [[InlineKeyboardButton("📅 Режим планировщика", callback_data="mode_planner")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "🎤 **Режим расшифровки встреч активен**\n\n"
                "Отправь голосовое сообщение или аудиофайл с записью встречи для расшифровки.\n\n"
                "Чтобы выйти из режима расшифровки, напиши 'отмена' или 'режим планировщика', или нажми кнопку ниже.",
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
    elif update.message and update.message.text:
        message_type = "текст"
        logger.info(f"Получено текстовое сообщение от пользователя {user_id}")
    
    logger.info(f"Обработка сообщения типа: {message_type} от пользователя {user_id}")
    
    # Проверяем, ожидаем ли мы URL подтверждения Google
    if context.user_data.get('waiting_google_url'):
        # Это URL с кодом подтверждения для Google OAuth
        auth_response = update.message.text
        
        try:
            calendar = GoogleCalendar(user_id)
            
            if calendar.handle_callback(auth_response):
                db.save_calendar_connection(
                    user_id=user_id,
                    provider='google',
                    calendar_id='primary',
                    credentials=''  # Credentials хранятся в файле
                )
                await update.message.reply_text("✓ Google Calendar успешно подключен!")
            else:
                await update.message.reply_text(
                    "Ошибка подключения. Проверь URL и попробуй снова.\n"
                    "Или используй /settings для новой попытки."
                )
        except Exception as e:
            logger.error(f"Ошибка обработки Google OAuth: {e}")
            await update.message.reply_text(f"Ошибка: {str(e)}\nПопробуй снова через /settings")
        
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
        
        # Отправляем результат пользователю (одно финальное сообщение)
        await update.message.reply_text(formatted_message)
    
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
            
            await update.message.reply_text(error_message)
        except Exception as reply_error:
            logger.error(f"Ошибка генерации/отправки сообщения об ошибке: {reply_error}", exc_info=True)
            # Fallback на простое сообщение
            try:
                await update.message.reply_text(
                    "Что-то пошло не так. Попробуй еще раз или сформулируй запрос по-другому."
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
    reminder_scheduler = ReminderScheduler(application.bot, db)
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
    
    # Обработчик голосовых сообщений (отдельно для лучшей отладки)
    application.add_handler(MessageHandler(
        filters.VOICE,
        handle_message
    ))
    
    # Обработчик изображений
    application.add_handler(MessageHandler(
        filters.PHOTO | filters.Document.IMAGE,
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
