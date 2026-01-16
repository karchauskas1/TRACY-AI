# TRACY AI BOT — Техническая документация

> Исчерпывающее руководство по архитектуре, модулям и логике работы Telegram-бота TRACY для управления календарём и событиями.

---

## Оглавление

1. [Общая архитектура системы](#1-общая-архитектура-системы)
2. [Главные файлы и их назначение](#2-главные-файлы-и-их-назначение)
3. [Flow обработки сообщений](#3-flow-обработки-сообщений)
4. [Структура данных событий](#4-структура-данных-событий)
5. [Intent-система и NLP](#5-intent-система-и-nlp)
6. [Система напоминаний](#6-система-напоминаний)
7. [Интеграция с внешними календарями](#7-интеграция-с-внешними-календарями)
8. [HTTP API для веб-приложения](#8-http-api-для-веб-приложения)
9. [База данных](#9-база-данных)
10. [Конфигурация](#10-конфигурация)
11. [Типичные баги и их исправление](#11-типичные-баги-и-их-исправление)
12. [Чеклист для внесения изменений](#12-чеклист-для-внесения-изменений)

---

## 1. Общая архитектура системы

### Диаграмма компонентов

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              TELEGRAM LAYER                                  │
│  ┌──────────────┐     ┌─────────────────────────────────────────────────┐  │
│  │ Telegram User│────▶│          python-telegram-bot (bot.py)           │  │
│  └──────────────┘     └─────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
        ┌───────────────────┐ ┌─────────────┐ ┌─────────────────┐
        │  media_processor  │ │nlp_extractor│ │meeting_processor│
        │  (STT, OCR)       │ │ (AI/OpenAI) │ │ (Whisper, AI)   │
        └───────────────────┘ └──────┬──────┘ └─────────────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    ▼                ▼                ▼
        ┌───────────────────┐ ┌─────────────┐ ┌─────────────────┐
        │conversation_handler│ │decision_    │ │conversation_    │
        │ (multi-turn)      │ │engine       │ │memory           │
        └───────────────────┘ └──────┬──────┘ └─────────────────┘
                                     │
            ┌────────────────────────┼────────────────────────┐
            ▼                        ▼                        ▼
    ┌───────────────┐       ┌───────────────┐       ┌───────────────┐
    │   database    │       │reminder_      │       │calendar_google│
    │ (PostgreSQL/  │       │scheduler      │       │calendar_icloud│
    │  SQLite)      │       └───────────────┘       └───────────────┘
    └───────────────┘
            │
            ▼
    ┌───────────────┐       ┌───────────────────────────────────────┐
    │  http_server  │◀─────▶│        Next.js Web App (web-app/)    │
    │   (aiohttp)   │       │         Telegram Mini App             │
    └───────────────┘       └───────────────────────────────────────┘
```

### Зависимости между модулями

| Модуль | Зависит от | Используется в |
|--------|------------|----------------|
| `bot.py` | Все модули | Точка входа |
| `nlp_extractor.py` | config, OpenAI | bot.py, http_server.py |
| `decision_engine.py` | database, calendar_*, reminder_scheduler | bot.py, http_server.py |
| `database.py` | config | Все модули |
| `conversation_handler.py` | database, nlp_extractor, decision_engine, conversation_memory | bot.py |
| `reminder_scheduler.py` | database, telegram | bot.py |
| `media_processor.py` | config, OpenAI, speech_recognition | bot.py |
| `meeting_processor.py` | config, OpenAI | bot.py |
| `calendar_google.py` | config, google-api | decision_engine.py |
| `calendar_icloud.py` | config, caldav | decision_engine.py |
| `http_server.py` | database, nlp_extractor, decision_engine | api_server.py |

---

## 2. Главные файлы и их назначение

### 2.1 `bot.py` — Точка входа (3842 строки)

**Назначение:** Главный модуль Telegram бота. Обрабатывает все входящие сообщения, команды и callback-кнопки.

**Глобальные объекты (инициализируются при старте):**

```python
# Сразу при импорте:
db = Database()                    # Инстанс базы данных
media_processor = MediaProcessor() # Обработка медиа (голос, фото)
nlp_extractor = NLPExtractor()     # NLP модуль для извлечения intent

# Инициализируются в main():
decision_engine = None             # Логика действий с событиями
reminder_scheduler = None          # Планировщик напоминаний
conversation_memory = None         # Память диалога (история)
conversation_handler = None        # Обработчик multi-turn диалогов
```

**Ключевые функции:**

| Функция | Строки | Описание |
|---------|--------|----------|
| `start_command()` | 68-147 | Обработка /start с онбордингом |
| `menu_command()` | 149-177 | Главное меню /menu |
| `help_command()` | 179-186 | Помощь /help |
| `settings_command()` | 320-354 | Настройки /settings |
| `handle_message()` | ~1200+ | **Основной обработчик всех сообщений** |
| `settings_callback()` | 385-1100+ | Обработка inline-кнопок |
| `get_reply_keyboard()` | ~1150 | Создание клавиатуры режимов |
| `main()` | ~3700+ | Инициализация и запуск бота |

**Режимы работы:**

1. **Режим планировщика** (по умолчанию):
   - Создание событий из текста/голоса/фото
   - Редактирование и удаление событий
   - Просмотр расписания

2. **Режим резюмирования встреч** (`context.user_data['waiting_meeting_audio'] = True`):
   - Расшифровка аудиозаписей встреч
   - Создание резюме
   - Извлечение событий из записи

---

### 2.2 `nlp_extractor.py` — NLP обработка (760 строк)

**Назначение:** Извлечение intent (намерения) и структурированных данных из текста пользователя через OpenRouter/OpenAI API.

**Главный метод:**

```python
async def extract_intent_and_context(
    text: str,                          # Текст пользователя
    user_timezone: str = "Europe/Moscow",
    user_locale: str = "ru_RU",
    last_event: Optional[Dict] = None,  # Последнее событие (для контекста)
    is_reply: bool = False,             # Это reply к сообщению бота?
    interpretation_mode: str = "soft",  # 'soft' или 'strict'
    chat_history: Optional[List] = None # История чата
) -> Dict
```

**Возвращаемые поля:**

```python
{
    # Основные поля
    'intent': str,           # Тип действия (см. таблицу ниже)
    'title': str,            # Название события
    'description': str,      # Описание
    'start_time': datetime,  # Время начала
    'end_time': datetime,    # Время окончания
    'location': str,         # Место
    'priority': int,         # Приоритет (0-5)
    
    # Флаги
    'has_explicit_time': bool,      # Время указано явно?
    'refers_to_last_event': bool,   # Ссылка на предыдущее событие?
    'confidence': float,            # Уверенность (0.0-1.0)
    
    # Для напоминаний
    'reminder_intervals': List[str], # ["1 hour", "30 minutes"]
    
    # Для повторяющихся событий
    'is_recurring': bool,
    'recurrence_type': str,  # 'daily', 'weekly', 'monthly'
    'interval': int,         # Каждые N дней/недель
    'days_of_week': List[str], # ['MO', 'WE', 'FR']
    'day_of_month': int,     # 1-31
    
    # Для операций
    'operation_verb': str,   # 'удали', 'перенеси', 'измени'
    'new_time': str,         # Новое время (для update)
    'new_date': str,         # Новая дата (для update)
    'relative_time_modification': str, # "+1 hour", "-30 minutes"
    
    # Служебные
    '_original_text': str    # Оригинальный текст (для fallback)
}
```

**Вспомогательные методы:**

| Метод | Описание |
|-------|----------|
| `_detect_missing_fields(extracted_data)` | Определяет какие поля отсутствуют |
| `generate_clarification_question(field, context)` | Генерирует уточняющий вопрос |
| `extract_from_answer(text, awaiting_field, partial_data)` | Извлекает ответ на уточняющий вопрос |
| `_parse_time_answer(text, partial_data, timezone)` | Парсит время из ответа |
| `_parse_yes_no(text)` | Распознаёт да/нет |
| `_fallback_extraction(text, timezone)` | Резервное извлечение при ошибке LLM |
| `is_command(text)` | Проверяет, является ли текст командой |

---

### 2.3 `decision_engine.py` — Логика действий (3231 строка)

**Назначение:** Принятие решений и выполнение действий с событиями на основе извлечённых данных.

**Главный метод:**

```python
async def process_intent(
    user_id: int,
    extracted_data: Dict,               # Данные от NLP
    last_event: Optional[Dict] = None,  # Последнее событие
    reply_to_event: Optional[Dict] = None # Событие из reply
) -> Dict
```

**Возвращает:**

```python
{
    'action': str,           # 'created', 'updated', 'deleted', 'error', 'awaiting_input'
    'message': str,          # Сообщение для пользователя
    'event_id': int,         # ID созданного/изменённого события
    'needs_confirmation': bool,
    'confirmation_type': str # Тип подтверждения (если нужно)
}
```

**Обработчики по intent:**

| Intent | Метод | Описание |
|--------|-------|----------|
| `event` | `_handle_event()` | Создание события |
| `reminder` | `_handle_reminder()` | Создание напоминания (как событие) |
| `note` | `_handle_note()` | Сохранение заметки |
| `update` | `_handle_update()` | Изменение существующего события |
| `update_many` | `_handle_update_many()` | Массовое изменение событий |
| `delete` | `_handle_delete()` | Удаление события |
| `delete_all` | `_handle_delete_all()` | Удаление всех событий |
| `delete_by_period` | `_handle_delete_by_period()` | Удаление за период |
| `delete_many` | `_handle_delete_many()` | Удаление нескольких событий |
| `delete_by_pattern` | `_handle_delete_by_pattern()` | Удаление по паттерну |
| `list_events` | `_handle_list_events()` | Показ списка событий |
| `search` | `_handle_search()` | Поиск событий |
| `add_reminder` | `_handle_add_reminder()` | Добавление напоминания к событию |
| `add_note` | `_handle_add_note()` | Добавление заметки к событию |
| `create_many` | `_handle_create_many()` | Создание нескольких событий |
| `small_talk` | `_handle_small_talk()` | Обработка приветствий и болтовни |
| `list_notes` | `_handle_list_notes()` | Показ заметок |
| `delete_note` | `_handle_delete_note()` | Удаление заметки |

**КРИТИЧЕСКИ ВАЖНО — Fallback-механизм (строки 137-368):**

Если NLP неправильно распознал intent, decision_engine переопределяет его:

```python
# Пример fallback логики:

# 1. "удали все планы/события" → delete_all
if has_delete_word and any(phrase in text for phrase in delete_all_patterns):
    intent = 'delete_all'

# 2. "покажи все события" → list_events
if any(phrase in text for phrase in ['покажи все события', 'покажи планы']):
    intent = 'list_events'

# 3. Время + действие → event (даже если NLP вернул 'note')
if has_any_time and has_action and intent == 'note':
    intent = 'event'

# 4. Reply + "удали" → delete
if reply_to_event and 'удали' in text_lower:
    intent = 'delete'
    extracted_data['refers_to_last_event'] = True
```

---

### 2.4 `database.py` — Работа с БД (2355 строк)

**Назначение:** Unified API для работы с PostgreSQL и SQLite.

**Определение типа БД:**

```python
USE_POSTGRESQL = bool(config.DATABASE_URL)
# Если DATABASE_URL указан → PostgreSQL (psycopg2 с connection pool)
# Иначе → SQLite (sqlite3)
```

**Ключевые методы:**

| Категория | Метод | Описание |
|-----------|-------|----------|
| **Пользователи** | `get_or_create_user(user_id)` | Получить/создать пользователя |
| | `get_user_settings(user_id)` | Получить настройки |
| | `update_user_settings(user_id, ...)` | Обновить настройки |
| **События** | `save_event(user_id, title, ...)` | Создать событие |
| | `get_events(user_id, limit, start_from, start_to)` | Получить события |
| | `get_event_by_id(event_id, user_id)` | Получить по ID |
| | `update_event(event_id, **kwargs)` | Обновить событие |
| | `delete_event(event_id, user_id)` | Удалить событие |
| | `find_similar_events(user_id, title, start_time)` | Найти похожие |
| **Напоминания** | `save_reminder(user_id, event_id, ...)` | Создать напоминание |
| | `get_pending_reminders(threshold_time)` | Получить неотправленные |
| | `mark_reminder_sent(reminder_id)` | Пометить отправленным |
| | `delete_reminders_for_event(event_id)` | Удалить напоминания события |
| **Календари** | `save_calendar_connection(...)` | Сохранить подключение |
| | `get_calendar_connections(user_id)` | Получить подключения |
| | `deactivate_calendar_connection(...)` | Деактивировать |
| **Контекст** | `get_last_event(user_id)` | Получить последнее событие |
| | `update_last_event_context(user_id, event_id)` | Обновить контекст |
| **Встречи** | `save_meeting(...)` | Сохранить встречу |
| | `get_meetings(user_id)` | Получить встречи |
| | `get_meeting(meeting_id, user_id)` | Получить по ID |
| **Чат** | `save_chat_message(user_id, role, content)` | Сохранить сообщение |
| | `get_chat_messages(user_id, limit)` | История чата |

---

### 2.5 `conversation_handler.py` — Multi-turn диалоги (267 строк)

**Назначение:** Управление многошаговыми диалогами для сбора недостающей информации.

**Главный метод:**

```python
async def process_message(
    user_id: int,
    text: str,
    extracted_data: Dict,
    last_event: Optional[Dict] = None
) -> Dict
```

**Логика работы:**

```
1. Проверяем есть ли активное состояние (ожидание ответа)
   │
   ├─▶ ДА → _handle_answer() — обрабатываем ответ на вопрос
   │   │
   │   └─▶ Проверяем остались ли недостающие поля
   │       │
   │       ├─▶ ДА → Задаём следующий вопрос
   │       └─▶ НЕТ → Выполняем через DecisionEngine
   │
   └─▶ НЕТ → _handle_new_action() — новое действие
       │
       └─▶ Проверяем полноту данных
           │
           ├─▶ Недостающие поля → Задаём уточняющий вопрос
           └─▶ Все данные есть → Выполняем через DecisionEngine
```

**Состояние диалога (таблица `conversation_state`):**

```python
{
    'pending_action': str,      # 'event', 'delete', 'update'
    'partial_data': Dict,       # Собранные данные
    'awaiting_field': str,      # 'time', 'title', 'location', 'confirmation'
    'context_event_id': int,    # ID события в контексте
    'updated_at': datetime      # Время обновления (для timeout)
}
```

**Timeout:** Состояние автоматически очищается через 10 минут.

---

### 2.6 `conversation_memory.py` — Память диалога (300 строк)

**Назначение:** Хранение и управление историей диалога (скользящее окно).

**Методы:**

| Метод | Описание |
|-------|----------|
| `add_message(user_id, role, content, intent)` | Добавить сообщение в историю |
| `get_history(user_id, limit=20)` | Получить последние N сообщений |
| `get_state(user_id)` | Получить состояние диалога |
| `set_state(user_id, pending_action, partial_data, awaiting_field, context_event_id)` | Установить состояние |
| `clear_state(user_id)` | Очистить состояние |
| `update_partial_data(user_id, field, value)` | Обновить одно поле |
| `cleanup_old_messages(days=30)` | Очистить старые сообщения |

---

### 2.7 `reminder_scheduler.py` — Планировщик напоминаний (603 строки)

**Назначение:** Фоновая отправка напоминаний о событиях и утренних дайджестов.

**Основной цикл:**

```python
async def _check_reminders_loop():
    while self.running:
        await self._check_and_send_reminders()    # Проверка напоминаний
        await self._check_and_send_morning_digests() # Утренние дайджесты
        await asyncio.sleep(60)  # Интервал: 1 минута
```

**Типы напоминаний:**

| Тип | reminder_type | Описание |
|-----|---------------|----------|
| До события | `before` | За N минут до начала |
| В момент начала | `start` | В момент начала события |
| Интервальные | `interval` | В заданном окне времени |

**Создание напоминаний:**

```python
def create_reminders_for_event(
    user_id: int,
    event_id: int,
    event_start_time: datetime,
    reminder_minutes: list = [15]  # По умолчанию за 15 минут
) -> list
```

**Утренний дайджест:**

- Время отправки: `morning_digest_time` (по умолчанию 09:00)
- Содержит: список событий на день + мотивационную цитату
- Генерация цитаты через AI на основе событий дня

---

### 2.8 `media_processor.py` — Обработка медиа (377 строк)

**Назначение:** Конвертация голосовых сообщений и изображений в текст.

**Методы:**

| Метод | Описание |
|-------|----------|
| `process_voice(voice_file, language="ru")` | STT через Google Speech Recognition |
| `process_image(photo_file, language="rus")` | OCR через Vision API или Tesseract |
| `extract_text_from_message(update, bot)` | Универсальный метод для любого типа |

**Поддерживаемые форматы:**

- **Голос:** mp3, m4a, wav, ogg, opus, flac, aac, wma, amr, 3gp, mka
- **Изображения:** jpeg, png, webp

**Приоритет обработки изображений:**
1. Vision API (OpenRouter/gpt-4o-mini)
2. Tesseract OCR (fallback)

---

### 2.9 `meeting_processor.py` — Обработка встреч (651 строка)

**Назначение:** Расшифровка аудиозаписей встреч и создание структурированных резюме.

**Методы:**

| Метод | Описание |
|-------|----------|
| `transcribe_meeting_audio(audio_file, language)` | Расшифровка через Whisper API |
| `generate_meeting_summary(transcript, raw_text)` | Краткое резюме |
| `generate_extended_summary(transcript, raw_text)` | Расширенное резюме |
| `extract_events_from_meeting(summary, transcript, timezone)` | Извлечение событий |

**Формат результата расшифровки:**

```python
{
    'transcript': str,      # Расшифровка с тайм-кодами
    'raw_text': str,        # Чистый текст без тайм-кодов
    'segments': List[Dict], # Сегменты с временными метками
    'duration': int,        # Длительность в секундах
    'language': str
}
```

---

### 2.10 `calendar_google.py` — Google Calendar (402 строки)

**Назначение:** Интеграция с Google Calendar через OAuth 2.0.

**OAuth Flow:**

```
1. get_authorization_url()
   └─▶ Генерирует URL для авторизации Google
   
2. Пользователь переходит по URL, авторизуется
   └─▶ Google возвращает code в redirect URI
   
3. handle_callback(authorization_response)
   └─▶ Обмен code на access_token + refresh_token
   
4. Токен сохраняется: tokens/google_token_{user_id}.json
```

**CRUD операции:**

| Метод | Описание |
|-------|----------|
| `create_event(title, description, start_time, end_time, location, timezone)` | Создать |
| `update_event(event_id, **kwargs)` | Обновить |
| `delete_event(event_id)` | Удалить |
| `search_events(query, time_min, time_max, max_results)` | Поиск |
| `get_event_ics(event_id)` | Получить в формате ICS |

---

### 2.11 `calendar_icloud.py` — iCloud Calendar (355 строк)

**Назначение:** Интеграция с iCloud через CalDAV.

**Требования:**
- App-Specific Password (не основной пароль Apple ID!)
- URL: `https://caldav.icloud.com`

**Credentials хранятся в БД (JSON):**

```python
{
    'caldav_url': 'https://caldav.icloud.com',
    'username': 'apple_id@icloud.com',
    'password': 'xxxx-xxxx-xxxx-xxxx'  # App-Specific Password
}
```

**CRUD операции:** аналогичны Google Calendar.

---

### 2.12 `http_server.py` — HTTP API (1346 строк)

**Назначение:** REST API для веб-приложения (aiohttp).

**Основные endpoints:**

| Endpoint | Метод | Описание |
|----------|-------|----------|
| `/api/events` | GET | Список событий `?user_id=&from=&to=` |
| `/api/meetings` | GET | Список встреч |
| `/api/meetings/{id}` | GET | Конкретная встреча |
| `/api/settings` | POST | Обновление настроек |
| `/api/feedback` | GET | Получить feedback (только super_user) |
| `/api/feedback/submit` | POST | Отправить feedback |
| `/api/todo-lists` | GET/POST | Списки задач |
| `/api/todo-lists/{id}` | GET/PUT/DELETE | Конкретный список |
| `/api/todo-lists/{id}/items` | POST | Добавить задачу |
| `/api/todo-items/{id}` | PUT/DELETE | Изменить/удалить задачу |
| `/api/chat/messages` | GET | История чата |
| `/api/chat/greeting` | GET | Приветственное сообщение |
| `/api/chat/send` | POST | Отправить сообщение |
| `/api/telegram-proxy` | POST | Прокси для Mini App |
| `/health` | GET | Health check |

---

### 2.13 `recurring_events.py` — Повторяющиеся события (199 строк)

**Назначение:** Движок для повторяющихся событий (частично реализован).

**Типы повторений:**
- `daily` — ежедневно
- `weekly` — еженедельно (с указанием дней недели)
- `monthly` — ежемесячно (с указанием числа)

**Статус:** Таблицы созданы, базовая логика есть, полная реализация в TODO.

---

## 3. Flow обработки сообщений

### Текстовое сообщение

```
Пользователь отправляет: "Встреча с Настей завтра в 15:00"
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ bot.py: handle_message()                                        │
│   1. Проверка режима (планировщик или встречи)                  │
│   2. Для планировщика:                                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ nlp_extractor.py: extract_intent_and_context()                  │
│   Input: "Встреча с Настей завтра в 15:00"                      │
│   Output: {                                                      │
│     intent: 'event',                                             │
│     title: 'Встреча с Настей',                                   │
│     start_time: datetime(2026, 1, 17, 15, 0),                   │
│     has_explicit_time: True                                      │
│   }                                                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ conversation_handler.py: process_message()                      │
│   1. Проверка активного состояния → НЕТ                         │
│   2. _handle_new_action()                                        │
│   3. _detect_missing_fields() → [] (все поля есть)              │
│   4. → decision_engine.process_intent()                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ decision_engine.py: process_intent()                            │
│   1. Fallback проверки intent → OK                               │
│   2. _handle_event():                                            │
│      a) db.save_event() → event_id=123                           │
│      b) calendar_google.create_event() (если подключён)         │
│      c) reminder_scheduler.create_reminders_for_event()          │
│   3. Return: { action: 'created', message: '...', event_id: 123 }│
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Пользователю:                                                    │
│ "✅ Создано событие                                              │
│  📅 Встреча с Настей                                             │
│  🗓 Суббота, 17 января                                           │
│  🕐 15:00 — 16:00                                                 │
│  ⏰ Напомню за 15 минут"                                         │
└─────────────────────────────────────────────────────────────────┘
```

### Голосовое сообщение

```
Пользователь отправляет: [Голосовое сообщение]
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ bot.py: handle_message()                                        │
│   1. Определяет тип: voice                                       │
│   2. media_processor.extract_text_from_message()                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ media_processor.py: process_voice()                              │
│   1. Скачивание файла                                            │
│   2. Конвертация в WAV (через pydub)                             │
│   3. Google Speech Recognition → "Встреча завтра в три"          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
              [Далее как текстовое сообщение]
```

### Reply к сообщению бота

```
Бот отправил: "✅ Создано: Встреча завтра в 15:00"
Пользователь отвечает reply: "удали"
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ bot.py: handle_message()                                        │
│   1. Определяет: это reply к сообщению бота                      │
│   2. Парсит event_id из оригинального сообщения                  │
│   3. Передаёт reply_to_event в decision_engine                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ decision_engine.py: process_intent()                            │
│   1. Fallback: reply + "удали" → intent='delete'                 │
│   2. extracted_data['refers_to_last_event'] = True               │
│   3. _handle_delete() → удаляет событие                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Структура данных событий

### Создание события

**Входной текст:** `"Встреча с Настей завтра в 15:00"`

**extracted_data от NLP:**

```python
{
    'intent': 'event',
    'title': 'Встреча с Настей',
    'start_time': datetime(2026, 1, 17, 15, 0, tzinfo=<Moscow>),
    'end_time': datetime(2026, 1, 17, 16, 0, tzinfo=<Moscow>),  # +1 час
    'has_explicit_time': True,
    'location': None,
    'description': None,
    'priority': 0,
    '_original_text': 'Встреча с Настей завтра в 15:00'
}
```

**Результат в БД (таблица events):**

```python
{
    'id': 123,
    'user_id': 308477378,
    'title': 'Встреча с Настей',
    'description': None,
    'start_time': '2026-01-17T15:00:00+03:00',
    'end_time': '2026-01-17T16:00:00+03:00',
    'location': None,
    'status': 'confirmed',
    'priority': 0,
    'external_id': 'abc123xyz',  # ID в Google Calendar (если подключён)
    'provider': 'google',        # 'google' или 'icloud'
    'created_at': '2026-01-16T12:00:00+03:00',
    'updated_at': '2026-01-16T12:00:00+03:00'
}
```

**Созданные напоминания (таблица reminders):**

```python
[
    {
        'id': 456,
        'user_id': 308477378,
        'event_id': 123,
        'reminder_time': '2026-01-17T14:45:00+00:00',  # UTC
        'event_start_time': '2026-01-17T12:00:00+00:00',  # UTC
        'reminder_type': 'before',
        'minutes_before': 15,
        'sent': False
    },
    {
        'id': 457,
        'user_id': 308477378,
        'event_id': 123,
        'reminder_time': '2026-01-17T12:00:00+00:00',  # UTC
        'event_start_time': '2026-01-17T12:00:00+00:00',  # UTC
        'reminder_type': 'start',
        'minutes_before': None,
        'sent': False
    }
]
```

### Обновление события

**Текст:** `"Перенеси встречу на 16:00"` или reply + `"перенеси на 16:00"`

```python
extracted_data = {
    'intent': 'update',
    'refers_to_last_event': True,  # или title для поиска
    'new_time': '16:00',
    'operation_verb': 'перенеси'
}
```

### Удаление события

**Текст:** `"Удали встречу с Настей"` или reply + `"удали"`

```python
extracted_data = {
    'intent': 'delete',
    'title': 'Встреча с Настей',  # ИЛИ
    'refers_to_last_event': True   # если reply или местоимение
}
```

---

## 5. Intent-система и NLP

### Полный список intent

| Intent | Описание | Пример текста |
|--------|----------|---------------|
| `event` | Создание события | "Встреча завтра в 15:00" |
| `reminder` | Создание напоминания | "Напомни проветрить в 19:30" |
| `note` | Сохранение заметки | "Запиши: купить молоко" |
| `update` | Изменение события | "Перенеси на 16:00" |
| `update_many` | Массовое изменение | "Перенеси все встречи на час" |
| `delete` | Удаление события | "Удали встречу" |
| `delete_all` | Удаление всех | "Удали все планы" |
| `delete_by_period` | Удаление за период | "Удали все за сегодня" |
| `delete_many` | Удаление нескольких | "Удали встречу и обед" |
| `delete_by_pattern` | Удаление по паттерну | "Удали все встречи" |
| `list_events` | Показ событий | "Покажи события на завтра" |
| `search` | Поиск | "Найди встречу с Настей" |
| `add_reminder` | Добавить напоминание | Reply + "напомни за час" |
| `add_note` | Добавить заметку | Reply + "важная встреча" |
| `create_many` | Создать несколько | "Добавь встречу и обед" |
| `small_talk` | Болтовня | "Привет", "Как дела" |
| `list_notes` | Показ заметок | "Покажи заметки" |
| `delete_note` | Удаление заметки | "Удали заметку" |
| `unknown` | Неизвестно | Fallback |

### Приоритет определения intent

1. **Высший приоритет:** Явные команды (`delete_all`, `list_events`)
2. **Высокий:** Операционные глаголы (`удали`, `перенеси`, `покажи`)
3. **Средний:** Время + действие → `event`
4. **Низкий:** Заметка без времени → `note`

### Режимы интерпретации

| Режим | Описание |
|-------|----------|
| `soft` (default) | Гибкая интерпретация, разумные предположения |
| `strict` | Точное следование, без предположений |

---

## 6. Система напоминаний

### Создание напоминаний

При создании события автоматически создаются напоминания:

```python
# default_reminder_minutes из настроек пользователя (по умолчанию 15)
reminder_minutes = [15]  # За 15 минут до события

# Если указаны в тексте:
# "за час, за полтора, за два часа напомни"
reminder_minutes = [60, 90, 120]
```

### Типы напоминаний

| Тип | reminder_type | Когда отправляется |
|-----|---------------|-------------------|
| До события | `before` | За N минут до `event_start_time` |
| В момент начала | `start` | В момент `event_start_time` |
| Интервальные | `interval` | Каждые N минут в заданном окне |

### Логика отправки

```python
# reminder_scheduler._check_and_send_reminders()

1. Получить все неотправленные напоминания (sent=False)
2. Для каждого:
   - Если reminder_time <= now + 30сек И reminder_time >= now - 30мин:
     - Отправить сообщение пользователю
     - mark_reminder_sent(reminder_id)
```

### Формат сообщения напоминания

```
🔔 Напоминание

Через 15 минут у тебя событие:

📅 Встреча с Настей
🕐 Суббота, 17 января 15:00

[⏰ Перенести]  ← inline кнопка
```

---

## 7. Интеграция с внешними календарями

### Google Calendar

**Требования:**
1. GOOGLE_CLIENT_ID и GOOGLE_CLIENT_SECRET в .env
2. Redirect URI настроен в Google Cloud Console

**Процесс подключения:**
1. Пользователь: /settings → Google Calendar
2. Бот: отправляет ссылку авторизации
3. Пользователь: авторизуется, копирует URL с code
4. Пользователь: отправляет URL боту
5. Бот: обменивает code на токен, сохраняет в БД

**Токен:** `tokens/google_token_{user_id}.json`

### iCloud Calendar

**Требования:**
1. Apple ID с двухфакторной аутентификацией
2. App-Specific Password (создаётся на appleid.apple.com)

**Процесс подключения:**
1. Пользователь: /settings → iCloud Calendar
2. Бот: показывает инструкцию по созданию App Password
3. Пользователь: отправляет Apple ID и App Password
4. Бот: проверяет подключение, сохраняет credentials в БД

**Credentials:** хранятся в `calendar_connections.credentials` (JSON)

---

## 8. HTTP API для веб-приложения

### Аутентификация

API использует `user_id` из параметров запроса. В production рекомендуется добавить токен аутентификации.

### Примеры запросов

**Получить события:**
```bash
GET /api/events?user_id=308477378&from=2026-01-01&to=2026-12-31

Response:
{
  "success": true,
  "events": [
    {
      "id": "123",
      "title": "Встреча с Настей",
      "startAt": "2026-01-17T15:00:00+03:00",
      "endAt": "2026-01-17T16:00:00+03:00",
      "allDay": false,
      "description": null,
      "location": null,
      "calendarSource": { "color": "#3b82f6", "name": "TRACY" }
    }
  ],
  "count": 1
}
```

**Отправить сообщение в чат:**
```bash
POST /api/chat/send
Content-Type: application/json

{
  "user_id": 308477378,
  "message": "Создай встречу завтра в 15:00"
}

Response:
{
  "success": true,
  "message": "✅ Создано событие...",
  "action": "created",
  "event_id": 124
}
```

**Обновить настройки:**
```bash
POST /api/settings
Content-Type: application/json

{
  "user_id": 308477378,
  "timezone": "Europe/Moscow",
  "morning_digest_time": "08:00",
  "default_reminder_minutes": 30
}

Response: { "success": true }
```

---

## 9. База данных

### Таблицы

```sql
-- Пользователи
users (
    user_id BIGINT PRIMARY KEY,
    timezone TEXT DEFAULT 'Europe/Moscow',
    locale TEXT DEFAULT 'ru_RU',
    notifications_enabled BOOLEAN DEFAULT TRUE,
    default_reminder_minutes INTEGER DEFAULT 15,
    morning_digest_time TEXT DEFAULT '09:00',
    web_notifications_enabled BOOLEAN DEFAULT TRUE,
    interpretation_mode TEXT DEFAULT 'soft',
    created_at TIMESTAMP
)

-- События
events (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    external_id TEXT,           -- ID во внешнем календаре
    provider TEXT,              -- 'google' или 'icloud'
    title TEXT NOT NULL,
    description TEXT,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    location TEXT,
    status TEXT DEFAULT 'confirmed',  -- 'confirmed', 'needs_confirmation'
    priority INTEGER DEFAULT 0,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)

-- Напоминания
reminders (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    event_id INTEGER NOT NULL,
    reminder_time TIMESTAMP NOT NULL,
    event_start_time TIMESTAMP NOT NULL,
    reminder_type TEXT DEFAULT 'before',  -- 'before', 'start', 'interval'
    minutes_before INTEGER,
    sent BOOLEAN DEFAULT FALSE,
    sent_at TIMESTAMP,
    created_at TIMESTAMP
)

-- Подключения календарей
calendar_connections (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    provider TEXT NOT NULL,     -- 'google' или 'icloud'
    calendar_id TEXT NOT NULL,
    credentials TEXT,           -- JSON для iCloud
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP
)

-- Заметки
notes (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    content TEXT NOT NULL,
    context TEXT,               -- Контекст (например, event_id)
    created_at TIMESTAMP
)

-- Встречи (расшифровки)
meetings (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    title TEXT,
    transcript TEXT,            -- С тайм-кодами
    raw_text TEXT,              -- Без тайм-кодов
    summary TEXT,               -- Краткое резюме
    summary_extended TEXT,      -- Расширенное резюме
    segments JSONB,             -- Сегменты расшифровки
    duration INTEGER DEFAULT 0,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)

-- Списки задач
todo_lists (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    title TEXT NOT NULL,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)

-- Элементы списков
todo_items (
    id SERIAL PRIMARY KEY,
    list_id INTEGER NOT NULL,
    text TEXT NOT NULL,
    completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)

-- История чата
chat_messages (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    role TEXT NOT NULL,         -- 'user' или 'assistant'
    content TEXT NOT NULL,
    created_at TIMESTAMP
)

-- История диалога (для контекста NLP)
conversation_sessions (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    message_role TEXT NOT NULL,
    message_content TEXT NOT NULL,
    intent TEXT,
    created_at TIMESTAMP
)

-- Состояние диалога (multi-turn)
conversation_state (
    user_id BIGINT PRIMARY KEY,
    pending_action TEXT,
    partial_data JSONB,
    awaiting_field TEXT,
    context_event_id INTEGER,
    updated_at TIMESTAMP
)

-- Последнее событие (для контекста)
user_last_event (
    user_id BIGINT PRIMARY KEY,
    event_id INTEGER NOT NULL,
    updated_at TIMESTAMP
)

-- Обратная связь
feedback (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    feedback_type TEXT NOT NULL,
    comment TEXT NOT NULL,
    screenshot_url TEXT,
    created_at TIMESTAMP
)

-- Повторяющиеся события (паттерны)
recurring_patterns (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    event_template_id INTEGER,
    recurrence_type TEXT NOT NULL,  -- 'daily', 'weekly', 'monthly'
    interval INTEGER DEFAULT 1,
    days_of_week TEXT,              -- 'MO,WE,FR'
    day_of_month INTEGER,
    start_date DATE NOT NULL,
    end_date DATE,
    exceptions TEXT,                -- Даты-исключения
    created_at TIMESTAMP
)

-- Экземпляры повторяющихся событий
recurring_instances (
    id SERIAL PRIMARY KEY,
    pattern_id INTEGER NOT NULL,
    event_id INTEGER NOT NULL,
    occurrence_date DATE NOT NULL
)
```

### Индексы

```sql
CREATE INDEX idx_events_user_id ON events(user_id);
CREATE INDEX idx_events_start_time ON events(start_time);
CREATE INDEX idx_events_external_id ON events(external_id, provider);
CREATE INDEX idx_reminders_user_id ON reminders(user_id);
CREATE INDEX idx_reminders_reminder_time ON reminders(reminder_time);
CREATE INDEX idx_reminders_sent ON reminders(sent);
CREATE INDEX idx_meetings_user_id ON meetings(user_id);
CREATE INDEX idx_conv_sessions_user_time ON conversation_sessions(user_id, created_at DESC);
CREATE INDEX idx_chat_messages_user_id ON chat_messages(user_id);
```

---

## 10. Конфигурация

### Переменные окружения (.env)

```bash
# ============ ОБЯЗАТЕЛЬНЫЕ ============

# Telegram Bot
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# OpenRouter (AI)
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxx
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=gpt-4o-mini

# ============ БАЗА ДАННЫХ ============

# PostgreSQL (приоритет) - для production
DATABASE_URL=postgresql://user:password@host:5432/tracy_db

# SQLite (fallback) - для разработки
DATABASE_PATH=./data/tracy.db

# ============ GOOGLE CALENDAR (опционально) ============

GOOGLE_CLIENT_ID=123456789-xxxxxxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxxxxxxxxxxx
GOOGLE_REDIRECT_URI=https://your-domain.com/callback
# Или для разработки:
# GOOGLE_REDIRECT_URI=http://localhost:8080/callback

# ============ СЕРВЕР ============

HOST=0.0.0.0
PORT=8080
TRACY_API_BASE_URL=https://api.your-domain.com

# ============ WEB APP ============

WEB_APP_URL=https://tracy-ai.vercel.app

# ============ НАСТРОЙКИ ============

DEFAULT_TIMEZONE=Europe/Moscow
SUPER_USER_ID=308477378  # ID админа для просмотра feedback
```

### config.py — Ключевые переменные

```python
TELEGRAM_BOT_TOKEN       # Токен бота
OPENROUTER_API_KEY       # API ключ OpenRouter
OPENROUTER_BASE_URL      # URL API (по умолчанию OpenRouter)
OPENROUTER_MODEL         # Модель (gpt-4o-mini)
GOOGLE_CLIENT_ID         # OAuth Client ID
GOOGLE_CLIENT_SECRET     # OAuth Client Secret
GOOGLE_REDIRECT_URI      # Redirect URI для OAuth
DATABASE_URL             # PostgreSQL connection string
DATABASE_PATH            # Путь к SQLite файлу
HOST                     # Хост сервера
PORT                     # Порт сервера
TRACY_API_BASE_URL       # Базовый URL API
WEB_APP_URL              # URL веб-приложения
DEFAULT_TIMEZONE         # Часовой пояс по умолчанию
TOKENS_DIR               # Директория для OAuth токенов
SUPER_USER_ID            # ID супер-пользователя
ALLOWED_PRODUCTION_DOMAINS # Разрешённые домены для Mini App
```

---

## 11. Типичные баги и их исправление

### 11.1 Неправильное распознавание intent

**Проблема:** NLP возвращает `note` вместо `event` для текста с датой/временем.

**Причина:** LLM иногда ошибается в определении intent.

**Решение:** Fallback в `decision_engine.py` (строки 211-306):

```python
# Если есть время + действие → переопределяем на event
if has_any_time and has_action and intent not in ['list_events', 'delete', ...]:
    intent = 'event'
    extracted_data['intent'] = 'event'
    logger.warning(f"Fallback: переопределил intent '{original_intent}' → 'event'")
```

**Где исправлять:** `decision_engine.py`, метод `process_intent()`, строки 211-306.

---

### 11.2 Время создаётся в прошлом

**Проблема:** Пользователь пишет "в 14:00", а сейчас 15:00 → событие создаётся на сегодня в прошлом.

**Причина:** NLP парсит время без учёта текущего времени.

**Решение:** В `nlp_extractor.py` (строки 391-420):

```python
# Если НЕТ явной даты И время уже прошло → добавляем 1 день
if not has_explicit_date and parsed_date < now:
    parsed_date = parsed_date + timedelta(days=1)
    logger.info(f"Время уже прошло, переносим на завтра")
```

**Где исправлять:** `nlp_extractor.py`, метод `extract_intent_and_context()`, строки 391-420.

---

### 11.3 Reply не определяется как операция над событием

**Проблема:** Reply к сообщению бота + "удали" не удаляет событие.

**Причина:** NLP не всегда понимает контекст reply.

**Решение:** В `decision_engine.py` (строки 315-348):

```python
# Определение типа операции для reply НЕЗАВИСИМО от текущего intent
if reply_to_event and original_text:
    text_lower = original_text.lower()
    
    # "удали" в reply → это delete
    if any(word in text_lower for word in ['удали', 'удалить', 'стереть', 'убрать']):
        intent = 'delete'
        extracted_data['intent'] = 'delete'
        extracted_data['refers_to_last_event'] = True
```

**Где исправлять:** `decision_engine.py`, метод `process_intent()`, строки 315-348.

---

### 11.4 Местоимения не распознаются

**Проблема:** "Перенеси это на завтра" не понимается как операция над последним событием.

**Причина:** NLP не всегда определяет `refers_to_last_event`.

**Решение:** Fallback в `decision_engine.py` (строки 350-368):

```python
# Определение refers_to_last_event по местоимениям
pronouns = ['это', 'его', 'её', 'эту', 'этот', 'тот', 'то', 'тому']

if any(pronoun in original_text.lower().split() for pronoun in pronouns):
    extracted_data['refers_to_last_event'] = True
    logger.info(f"Fallback: обнаружено местоимение → refers_to_last_event=True")
```

**Где исправлять:** `decision_engine.py`, метод `process_intent()`, строки 350-368.

---

### 11.5 Напоминания не отправляются

**Проблема:** Напоминания создаются, но не приходят.

**Возможные причины:**
1. `reminder_scheduler` не запущен
2. Время напоминания в неправильном часовом поясе
3. Напоминание уже помечено как отправленное

**Диагностика:**
```python
# В логах должно быть:
# "✓ ReminderScheduler задача запущена"
# "✓ Найдено напоминание {id}"
# "✅ Напоминание {id} успешно отправлено"
```

**Где исправлять:** `reminder_scheduler.py`, метод `_check_and_send_reminders()`.

---

### 11.6 Дубликаты событий

**Проблема:** При повторной отправке того же текста создаётся дубликат.

**Решение:** В `decision_engine.py` есть дедупликация (строки 665-706):

```python
# Проверяем похожие события в пределах 1 дня
similar_events = self.db.find_similar_events(user_id, title, start_time, days_window=1)

# Обновляем только если:
# 1. Название совпадает почти точно
# 2. Время отличается менее чем на 1 час
if similar_events and time_diff < 3600:
    return await self._update_existing_event(...)
```

**Где исправлять:** `decision_engine.py`, метод `_handle_event()`, строки 665-706.

---

## 12. Чеклист для внесения изменений

### Добавление нового intent

1. **`nlp_extractor.py`** (строки 132-280):
   - Добавить описание intent в system_prompt
   - Добавить примеры использования
   - Добавить в список возможных значений intent в JSON schema

2. **`decision_engine.py`**:
   - Создать метод `_handle_new_intent()`
   - Добавить routing в `process_intent()` (строки 425-465)
   - При необходимости добавить fallback логику (строки 154-209)

3. **Тестирование**:
   - Проверить на разных формулировках
   - Проверить с reply
   - Проверить с местоимениями

---

### Изменение формата сообщений

1. **Для подтверждений создания/изменения:**
   - `decision_engine.py`: метод `_format_event_confirmation()`

2. **Для списков событий:**
   - `decision_engine.py`: метод `_format_event_list()`

3. **Для напоминаний:**
   - `reminder_scheduler.py`: метод `_send_reminder()`

---

### Добавление новой таблицы в БД

1. **`database.py`**:
   - Добавить CREATE TABLE в `init_db()`:
     - PostgreSQL: строки 107-393
     - SQLite: строки 396-628
   - Добавить индексы если нужно
   - Создать CRUD методы

2. **Миграция** (для production):
   - Добавить ALTER TABLE в `init_db()` для существующих БД
   - Или использовать отдельный скрипт миграции

---

### Изменение обработки голоса/изображений

1. **`media_processor.py`**:
   - Голос: метод `process_voice()`
   - Изображения: метод `process_image()`
   - Универсальный: метод `extract_text_from_message()`

2. **Зависимости**:
   - Голос: `speech_recognition`, `pydub`, `ffmpeg`
   - Изображения: `PIL`, `pytesseract`, OpenAI Vision API

---

### Изменение расписания напоминаний

1. **Дефолтные значения:**
   - `database.py`: `default_reminder_minutes` в настройках пользователя

2. **Создание напоминаний:**
   - `reminder_scheduler.py`: метод `create_reminders_for_event()`

3. **Интервал проверки:**
   - `reminder_scheduler.py`: `self.check_interval = 60` (в секундах)

---

### Добавление нового endpoint в HTTP API

1. **`http_server.py`**:
   - Создать async handler функцию
   - Зарегистрировать route в `create_app()` (строки 1292-1320)

2. **CORS**:
   - При необходимости добавить origin в `allowed_origins` (строки 1240-1245)

---

## Быстрый старт для разработчика

```bash
# 1. Клонировать репозиторий
git clone <repo_url>
cd "TRACY AI BOT"

# 2. Создать виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или: venv\Scripts\activate  # Windows

# 3. Установить зависимости
pip install -r requirements.txt

# 4. Создать .env файл
cp env.example .env
# Заполнить TELEGRAM_BOT_TOKEN и OPENROUTER_API_KEY

# 5. Запустить бота
python api_server.py

# Или для разработки только бота:
python bot.py
```

---

## Контакты и поддержка

- **Супер-пользователь ID:** 308477378
- **Feedback:** через /settings → Обратная связь
- **Логи:** stdout с уровнем INFO

---

*Документация актуальна на январь 2026 года.*
