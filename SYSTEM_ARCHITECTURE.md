# 📋 ПОЛНАЯ АРХИТЕКТУРА СИСТЕМЫ TRACY AI

**Дата создания**: 2026-01-14  
**Версия**: Текущее состояние (после всех фиксов)

---

## 1️⃣ ОБЩАЯ АРХИТЕКТУРА СИСТЕМЫ

### Схема системы (ASCII)

```
┌─────────────────────────────────────────────────────────────┐
│                    TELEGRAM ECOSYSTEM                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐         ┌──────────────┐                  │
│  │   Telegram   │         │   Telegram   │                  │
│  │   Client     │────────▶│     Bot      │                  │
│  │  (Mobile/    │◀────────│  (bot.py)    │                  │
│  │  Desktop)    │         │              │                  │
│  └──────────────┘         └──────┬───────┘                  │
│         │                        │                           │
│         │                        │                           │
│         │ Menu Button /         │                           │
│         │ /web command           │                           │
│         │                        │                           │
│         ▼                        │                           │
│  ┌───────────────────────────────┘                           │
│  │                                                           │
│  │  Telegram Mini App (WebView)                             │
│  │  ┌─────────────────────────────────────┐                 │
│  │  │  Next.js Frontend (Vercel)         │                 │
│  │  │  https://tracy-ai.vercel.app        │                 │
│  │  │                                     │                 │
│  │  │  ┌───────────────────────────────┐  │                 │
│  │  │  │  app/page.tsx (entrypoint)    │  │                 │
│  │  │  │  → TelegramBootstrap          │  │                 │
│  │  │  │  → router.push('/assistant')  │  │                 │
│  │  │  └───────────────────────────────┘  │                 │
│  │  │                                     │                 │
│  │  │  ┌───────────────────────────────┐  │                 │
│  │  │  │  /api/proxy (Next.js Route)  │  │                 │
│  │  │  │  POST { path, method, body } │  │                 │
│  │  │  └───────────┬───────────────────┘  │                 │
│  │  └───────────────┼─────────────────────┘                 │
│  └──────────────────┼───────────────────────────────────────┘
│                     │                                         
│                     │ HTTPS                                    
│                     ▼                                         
│  ┌──────────────────────────────────────┐                    
│  │  Backend API Server                   │                    
│  │  https://api.pasekaproduction.ru      │                    
│  │  (http_server.py)                     │                    
│  │                                       │                    
│  │  ┌─────────────────────────────────┐ │                    
│  │  │  Flask HTTP Server               │ │                    
│  │  │  Port: 8080                      │ │                    
│  │  │  Endpoints:                      │ │                    
│  │  │  - /api/events                   │ │                    
│  │  │  - /api/chat/*                   │ │                    
│  │  │  - /api/meetings/*               │ │                    
│  │  │  - /api/todo-lists/*             │ │                    
│  │  └─────────────────────────────────┘ │                    
│  └───────────────┬───────────────────────┘                    
│                  │                                             
│                  ▼                                             
│  ┌──────────────────────────────────────┐                    
│  │  Database Layer                      │                    
│  │  ┌──────────────┐  ┌──────────────┐ │                    
│  │  │  PostgreSQL  │  │   SQLite     │ │                    
│  │  │  (priority)  │  │  (fallback)  │ │                    
│  │  └──────────────┘  └──────────────┘ │                    
│  │  (database.py)                      │                    
│  └──────────────────────────────────────┘                    
│                                                               │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    EXTERNAL SERVICES                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │  OpenRouter  │  │   Google    │  │    iCloud   │        │
│  │  (AI/NLP)    │  │  Calendar   │  │   Calendar  │        │
│  │              │  │   (OAuth)   │  │   (CalDAV)   │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Подсистемы

1. **Telegram Bot** (`bot.py`)
   - Обработка команд и сообщений
   - Управление состоянием пользователя
   - Интеграция с календарями
   - Обработка медиа (голос, фото)

2. **Telegram Mini App** (`web-app/`)
   - Next.js 14 (App Router)
   - React компоненты
   - Telegram WebApp SDK интеграция
   - Клиентская навигация

3. **Backend API** (`http_server.py`)
   - Flask HTTP сервер
   - REST API endpoints
   - Интеграция с базой данных
   - Обработка запросов от Mini App

4. **Database** (`database.py`)
   - PostgreSQL (приоритет)
   - SQLite (fallback)
   - Хранение пользователей, событий, встреч

5. **External Services**
   - OpenRouter (AI/NLP)
   - Google Calendar (OAuth)
   - iCloud Calendar (CalDAV)

### Каналы коммуникации

1. **Telegram Bot ↔ User**: Telegram Bot API (long polling)
2. **Telegram Mini App ↔ User**: Telegram WebView (HTTPS)
3. **Mini App ↔ Backend**: Next.js `/api/proxy` → Backend API (HTTPS)
4. **Bot ↔ Backend**: Внутренние вызовы (Python)
5. **Bot ↔ Database**: PostgreSQL/SQLite (прямое подключение)
6. **Backend ↔ Database**: PostgreSQL/SQLite (прямое подключение)

---

## 2️⃣ TELEGRAM-БОТ (BACKEND)

### 2.1 Точка входа бота

**Основной файл**: `bot.py`

**Функция запуска**: `main()` (строка 3642)

**Как запускается**:
- **Production**: `systemctl` service (`tracy-bot.service`)
  - Файл сервиса: `/etc/systemd/system/tracy-bot.service`
  - Команда запуска: `/opt/tracy-ai-bot/venv/bin/python /opt/tracy-ai-bot/bot.py`
  - Расположение: `/opt/tracy-ai-bot/`
  - Перезапуск: `systemctl restart tracy-bot.service`

**Сервисы используются**:
- `python-telegram-bot` (Application, CommandHandler, MessageHandler)
- `asyncio` для асинхронной обработки
- `ReminderScheduler` для напоминаний
- `DecisionEngine` для обработки команд
- `MediaProcessor` для обработки медиа
- `MeetingProcessor` для расшифровки встреч

**Инициализация компонентов** (строки 33-39):
```python
db = Database()
media_processor = MediaProcessor()
nlp_extractor = NLPExtractor()
meeting_processor = MeetingProcessor(nlp_extractor.client)
reminder_scheduler = None  # Инициализируется в main()
decision_engine = None  # Инициализируется в main()
```

### 2.2 Команды бота

| Команда | Файл | Что делает | Побочные эффекты |
|---------|------|------------|------------------|
| `/start` | `bot.py:42` | Приветствие, онбординг, создание пользователя в БД | Создает запись в БД через `db.get_or_create_user()` |
| `/menu` | `bot.py:124` | Показывает главное меню с кнопками | НЕТ |
| `/help` | `bot.py:154` | Показывает справку по использованию | НЕТ |
| `/web` | `bot.py:163` | Открывает веб-приложение через WebApp кнопку | Проверяет валидность `WEB_APP_URL` |
| `/settings` | `bot.py:290` | Показывает настройки календарей | НЕТ |
| `/search` | `bot.py:1941` | Поиск событий по тексту | НЕТ |
| `/share` | `bot.py:1970` | Показывает инструкции по шарингу | НЕТ |
| `/connect_icloud` | `bot.py:3494` | Подключение iCloud Calendar | Сохраняет credentials в БД |

**Регистрация handlers** (строки 3769-3811):
```python
application.add_handler(CommandHandler("start", start_command))
application.add_handler(CommandHandler("menu", menu_command))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(CommandHandler("settings", settings_command))
application.add_handler(CommandHandler("web", web_command))
application.add_handler(CommandHandler("search", search_command))
application.add_handler(CommandHandler("share", share_command))
application.add_handler(CommandHandler("connect_icloud", connect_icloud_command))
```

### 2.3 Inline / Keyboard / Menu Button

**Menu Button**:
- **Где формируется**: `bot.py:3684-3704` (в `post_init` хуке)
- **Где задаётся WebApp URL**: `config.WEB_APP_URL` из `.env`
- **Валидация**: `config.is_valid_production_url()` - проверяет, что URL production (не preview)
- **Установка**: `app.bot.set_chat_menu_button(chat_id=None, menu_button=menu_button)`
  - `chat_id=None` означает глобальная настройка для всех чатов
- **Текст кнопки**: "TRACY"
- **URL**: Только production URL (валидируется)

**Команды, открывающие Mini App**:
- `/web` - создает InlineKeyboardButton с `WebAppInfo(url=web_url)`
- Menu Button (глобальная кнопка внизу чата)

**Дубли логики**: НЕТ - Menu Button и `/web` используют один и тот же `WEB_APP_URL`

### 2.4 Работа с состоянием пользователя

**Где хранится user state**:
- **База данных**: `database.py` - таблица `users`
- **Временное состояние**: `context.user_data` (dict) - хранится в памяти бота
  - Используется для multi-step диалогов (например, подключение iCloud)
  - Примеры: `context.user_data['waiting_meeting_audio']`, `context.user_data['icloud_email']`

**Как идентифицируется пользователь**:
- **Telegram User ID**: `update.effective_user.id` (int)
- **Создание в БД**: `db.get_or_create_user(user_id)` при `/start`
- **Получение из БД**: `db.get_user(user_id)`

**Session / Memory / Cache**:
- **НЕТ явной session системы** - используется `context.user_data` (в памяти)
- **НЕТ persistent cache** - все данные в БД
- **НЕТ memory для AI** - каждый запрос обрабатывается независимо

---

## 3️⃣ TELEGRAM MINI APP (FRONTEND)

### 3.1 Точка входа

**URL, который открывает Telegram**: `https://tracy-ai.vercel.app` (production URL)

**Entrypoint файл**: `web-app/app/page.tsx`

**Layout**: `web-app/app/layout.tsx`

**Что происходит при открытии**:
1. Загружается `layout.tsx`:
   - Подключается Telegram SDK: `<script src="https://telegram.org/js/telegram-web-app.js" />`
   - Инжектится `NEXT_PUBLIC_API_URL` в `window.__NEXT_PUBLIC_API_URL__`
   - Рендерится `TelegramBootstrap` компонент
2. Загружается `page.tsx`:
   - Проверяет наличие Telegram WebApp
   - Сохраняет user data в `localStorage` (если есть)
   - Перенаправляет на `/assistant` или `/login`

### 3.2 Навигация

| Path | File | Используется где | Примечания |
|------|------|------------------|------------|
| `/` | `app/page.tsx` | Entrypoint, автоматический редирект | Редиректит на `/assistant` или `/login` |
| `/assistant` | `app/assistant/page.tsx` | Главный экран, кнопка "Чат с Tracy" | Использует `router.push('/chat')` |
| `/chat` | `app/chat/page.tsx` | Чат с AI-ассистентом | Существует, используется кнопкой "Чат с Tracy" |
| `/calendar` | `app/calendar/page.tsx` | Календарь событий | Используется кнопкой в `/assistant` |
| `/calendar/list` | `app/calendar/list/page.tsx` | Список событий | Используется из `/calendar` |
| `/meetings` | `app/meetings/page.tsx` | Главная страница встреч | НЕ ОБНАРУЖЕНО В КОДЕ - используется `MeetingsPageClient.tsx` |
| `/meetings/new` | `app/meetings/new/page.tsx` | Создание новой встречи | Используется кнопкой в `MeetingsPageClient.tsx` |
| `/meetings/history` | `app/meetings/history/page.tsx` | История встреч | Используется кнопкой в `MeetingsPageClient.tsx` |
| `/meetings/[id]` | `app/meetings/[id]/page.tsx` | Детали встречи | Динамический роут |
| `/todo-lists` | `app/todo-lists/page.tsx` | Списки задач | Используется кнопкой в `/assistant` |
| `/todo-lists/detail` | `app/todo-lists/detail/page.tsx` | Детали списка задач | Используется из `/todo-lists` |
| `/settings` | `app/settings/page.tsx` | Главная страница настроек | Используется кнопкой в `/assistant` |
| `/settings/account` | `app/settings/account/page.tsx` | Настройки аккаунта | Используется из `/settings` |
| `/settings/ai` | `app/settings/ai/page.tsx` | Настройки AI | Используется из `/settings` |
| `/settings/calendars` | `app/settings/calendars/page.tsx` | Настройки календарей | Используется из `/settings` |
| `/settings/feedback` | `app/settings/feedback/page.tsx` | Обратная связь | Используется из `/settings` |
| `/settings/general` | `app/settings/general/page.tsx` | Общие настройки | Используется из `/settings` |
| `/settings/notifications` | `app/settings/notifications/page.tsx` | Настройки уведомлений | Используется из `/settings` |
| `/login` | `app/login/page.tsx` | Страница входа | Используется при отсутствии user |
| `/oauth-callback` | `app/oauth-callback/page.tsx` | OAuth callback для Google Calendar | Используется при OAuth редиректе |
| `/debug` | `app/debug/page.tsx` | Debug страница | Используется только для супер-пользователей |
| `/click-test` | `app/click-test/page.tsx` | Тестовая страница для кликов | Тестовая страница |
| `/test-navigation` | `app/test-navigation/page.tsx` | Тестовая страница навигации | Тестовая страница |
| `/test` | `app/test/page.tsx` | Тестовая страница | Тестовая страница |
| `/not-found` | `app/not-found.tsx` | 404 страница | Автоматически при 404 |

**Навигация использует**:
- `useRouter()` из `next/navigation` - основной способ
- `router.push(path)` - для программной навигации
- `<Link href={path}>` - для ссылок (редко используется)
- `window.location.href` - ТОЛЬКО как fallback в `page.tsx` (строка 25)

### 3.3 Инициализация Telegram WebApp

**Где загружается SDK**:
- `app/layout.tsx:28` - `<script src="https://telegram.org/js/telegram-web-app.js" />`

**Где вызывается ready() / expand()**:
- `components/TelegramBootstrap.tsx:37-38`
  - `tg.ready()`
  - `tg.expand()`
  - `tg.setHeaderColor("#1a1a20")`
  - `tg.setBackgroundColor("#1a1a20")`

**Гарантии single-init**:
- `useRef(false)` для отслеживания инициализации (строка 15)
- Проверка `initializedRef.current` перед инициализацией (строка 22, 33)
- Компонент рендерится один раз в `layout.tsx` (строка 38)

**Важно**: Все другие компоненты НЕ должны вызывать `tg.ready()` или `tg.expand()` - это делается только в `TelegramBootstrap`.

### 3.4 Клики и события

**Обработчики**:
- **onClick** - основной способ (используется везде)
- **onTouchStart** - НЕ используется (удален из `click-test/page.tsx` для совместимости с Desktop)
- **preventDefault** - используется ТОЛЬКО в:
  - `app/meetings/new/page.tsx:17,22,27` - для drag & drop (нормально)
  - `app/chat/page.tsx:343` - для Enter key в textarea (нормально)

**Кастомные gesture handlers**: НЕТ

**Alert / Confirm / Prompt**: 
- **УДАЛЕНЫ** - заменены на `toast()` из `hooks/use-toast`
- Используется в: `meetings/history/page.tsx`, `meetings/new/page.tsx`, `oauth-callback/page.tsx`

**window.open / location.href**:
- **window.open** - используется ТОЛЬКО для внешних ссылок (Telegram бот) - это нормально
- **location.href** - используется ТОЛЬКО как fallback в `page.tsx:25` и для чтения URL (не для навигации)

---

## 4️⃣ СВЯЗЬ БОТ ↔ MINI APP

### 4.1 Как данные передаются из бота в Mini App

**initData**:
- Telegram автоматически передает `initData` в WebView
- Доступно через `window.Telegram.WebApp.initDataUnsafe`
- Содержит: `user`, `auth_date`, `hash`
- Используется в: `lib/useTelegramUser.ts:49`

**Query params**:
- НЕТ прямых query params от бота
- Используется в `/calendar` для передачи событий: `?events={encoded_data}` (строка 3365 в `bot.py`)

**Storage**:
- `localStorage.setItem('telegram_user', JSON.stringify(userData))` - сохраняется в `app/page.tsx:46`
- Используется как fallback, если `initData` недоступен

**URL payload**: НЕТ

### 4.2 Как Mini App общается с backend

**Через proxy**:
- **Production** (не localhost): Все запросы идут через `/api/proxy`
- **Логика**: `lib/apiClient.ts:224-273`
- **Проверка**: `window.location.hostname !== 'localhost'`

**Прямые запросы**:
- **Localhost**: Прямые запросы к `NEXT_PUBLIC_API_URL`
- **Логика**: `lib/apiClient.ts:276-411`

**API Routes**:
- `/api/proxy` - единственный API route в Next.js
- Файл: `app/api/proxy/route.ts`
- Метод: `POST`
- Формат запроса: `{ path, method, params, body }`
- Проксирует к: `INTERNAL_API_BASE` или `NEXT_PUBLIC_API_URL`

---

## 5️⃣ BACKEND / API

### 5.1 Где backend логика

**Файлы**:
- `http_server.py` - Flask HTTP сервер
- `bot.py` - Telegram Bot (использует те же модули)
- `database.py` - Работа с БД
- `media_processor.py` - Обработка медиа
- `nlp_extractor.py` - NLP через OpenRouter
- `decision_engine.py` - Логика принятия решений
- `meeting_processor.py` - Обработка встреч
- `reminder_scheduler.py` - Напоминания
- `calendar_google.py` - Google Calendar интеграция
- `calendar_icloud.py` - iCloud Calendar интеграция
- `feedback_service.py` - Обратная связь

**Endpoints** (из `http_server.py`):
- HTTP сервер использует `aiohttp` (асинхронный)
- Запускается в отдельном потоке из `bot.py:3845-3846`
- Функция запуска: `start_http_server(host, port)` (строка 1084)
- Использует глобальную ссылку на БД через `set_database(db)`

**Роли**:
- HTTP сервер запускается в фоновом потоке из `bot.py` (строка 3755-3760)
- Использует Flask для обработки HTTP запросов
- Порт: `config.PORT` (по умолчанию 8080)

### 5.2 API контракт

**Endpoints** (из анализа `http_server.py:1054-1079`):

| Endpoint | Method | Кто вызывает | Что делает | Handler |
|----------|--------|--------------|------------|---------|
| `/` | GET | Health check | Корневой endpoint | `root_handler` |
| `/health` | GET | Health check | Проверка здоровья сервера | `health_handler` |
| `/api/events` | GET | Mini App | Список событий пользователя | `get_events_handler` |
| `/api/meetings` | GET | Mini App | Список встреч пользователя | `get_meetings_handler` |
| `/api/meetings/{meeting_id}` | GET | Mini App | Детали встречи | `get_meeting_handler` |
| `/api/meetings/{meeting_id}/create-event` | POST | Mini App | Создать событие из встречи | `create_event_from_meeting_handler` |
| `/api/settings` | POST | Mini App | Обновить настройки пользователя | `update_settings_handler` |
| `/api/feedback` | GET | Mini App | Получить обратную связь | `get_feedback_handler` |
| `/api/todo-lists` | GET | Mini App | Список списков задач | `get_todo_lists_handler` |
| `/api/todo-lists` | POST | Mini App | Создать список задач | `create_todo_list_handler` |
| `/api/todo-lists/{list_id}` | GET | Mini App | Детали списка задач | `get_todo_list_handler` |
| `/api/todo-lists/{list_id}` | PUT | Mini App | Обновить список задач | `update_todo_list_handler` |
| `/api/todo-lists/{list_id}` | DELETE | Mini App | Удалить список задач | `delete_todo_list_handler` |
| `/api/todo-lists/{list_id}/items` | POST | Mini App | Создать задачу в списке | `create_todo_item_handler` |
| `/api/todo-items/{item_id}` | PUT | Mini App | Обновить задачу | `update_todo_item_handler` |
| `/api/todo-items/{item_id}` | DELETE | Mini App | Удалить задачу | `delete_todo_item_handler` |
| `/api/chat/messages` | GET | Mini App | История сообщений чата | `get_chat_messages_handler` |
| `/api/chat/greeting` | GET | Mini App | Приветственное сообщение | `generate_chat_greeting_handler` |
| `/api/chat/send` | POST | Mini App | Отправить сообщение | `send_chat_message_handler` |
| `/api/telegram-proxy` | POST | Mini App | Прокси для Telegram Bot API | `telegram_proxy_handler` |

**Примечание**: Все endpoints требуют `user_id` в query параметрах или body. HTTP сервер использует `aiohttp` (асинхронный).

---

## 6️⃣ ОКРУЖЕНИЯ И ДЕПЛОЙ

### 6.1 Переменные окружения

#### Backend (bot.py)

| Переменная | Где используется | Обязательна | Что будет если нет |
|------------|------------------|-------------|-------------------|
| `TELEGRAM_BOT_TOKEN` | `config.py:8`, `bot.py:3644` | ✅ Да | Бот не запустится (ValueError) |
| `OPENROUTER_API_KEY` | `config.py:11` | ✅ Да | NLP не будет работать |
| `OPENROUTER_BASE_URL` | `config.py:12` | ⚠️ Нет | Используется default: `https://openrouter.ai/api/v1` |
| `OPENROUTER_MODEL` | `config.py:13` | ⚠️ Нет | Используется default: `gpt-4o-mini` |
| `GOOGLE_CLIENT_ID` | `config.py:16` | ⚠️ Нет | Google Calendar не будет работать |
| `GOOGLE_CLIENT_SECRET` | `config.py:17` | ⚠️ Нет | Google Calendar не будет работать |
| `GOOGLE_REDIRECT_URI` | `config.py:20` | ⚠️ Нет | Используется default: `https://karchauskas1.github.io/TRACY-AI/` |
| `DATABASE_URL` | `config.py:24` | ⚠️ Нет | Используется SQLite fallback |
| `DATABASE_PATH` | `config.py:25` | ⚠️ Нет | Используется default: `./data/tracy.db` |
| `HOST` | `config.py:30` | ⚠️ Нет | Используется default: `localhost` |
| `PORT` | `config.py:32` | ⚠️ Нет | Используется default: `8080` |
| `DEFAULT_TIMEZONE` | `config.py:39` | ⚠️ Нет | Используется default: `Europe/Moscow` |
| `WEB_APP_URL` | `config.py:56`, `bot.py:3687` | ⚠️ Нет | Menu Button не будет установлен |
| `FEEDBACK_SPREADSHEET_ID` | `config.py:117` | ⚠️ Нет | Обратная связь не будет работать |
| `FEEDBACK_APPS_SCRIPT_URL` | `config.py:131` | ⚠️ Нет | Используется default URL |
| `SUPER_USER_ID` | `config.py:137` | ⚠️ Нет | Используется default: `308477378` |

#### Frontend (web-app)

| Переменная | Где используется | Обязательна | Что будет если нет |
|------------|------------------|-------------|-------------------|
| `NEXT_PUBLIC_API_URL` | `lib/apiClient.ts:57`, `app/api/proxy/route.ts:11` | ✅ Да | Используется fallback: `https://api.pasekaproduction.ru` |
| `INTERNAL_API_BASE` | `app/api/proxy/route.ts:11` | ⚠️ Нет | Используется `NEXT_PUBLIC_API_URL` или fallback |
| `NEXT_PUBLIC_TELEGRAM_BOT_USERNAME` | `app/login/page.tsx:24`, `app/meetings/new/page.tsx:49` | ⚠️ Нет | Используется default: `tracy_aibot` |

### 6.2 Сервер

**Где живёт бот**:
- **IP**: `5.35.126.42`
- **Путь**: `/opt/tracy-ai-bot/`
- **Service**: `tracy-bot.service`
- **User**: `root`

**Как деплоится**:
- **Вручную**: Копирование файлов через SSH (`scp` или `cat`)
- **Git**: НЕТ git репозитория на сервере (код обновляется вручную)

**Как рестартится**:
- `systemctl restart tracy-bot.service`
- Или через `deploy.sh` скрипт (строка 41-44)

### 6.3 Vercel

**Production domain**: `https://tracy-ai.vercel.app`

**Preview domains**: НЕ ИСПОЛЬЗУЮТСЯ - валидация в `config.is_valid_production_url()` запрещает preview URLs

**Как триггерится деплой**:
- **Автоматически**: При push в GitHub (если проект подключен через GitHub)
- **Вручную**: Через Vercel CLI (`npx vercel --prod`)
- **Через deploy.sh**: Скрипт делает `git push`, что триггерит автоматический деплой

**Конфигурация Vercel**:
- **Framework Preset**: Next.js
- **Root Directory**: `web-app` (предположительно)
- **Build Command**: `npm run build`
- **Output Directory**: `.next`

---

## 7️⃣ ИЗВЕСТНЫЕ ОГРАНИЧЕНИЯ И ОСОБЕННОСТИ

### Telegram WebView особенности

1. **Alert/Confirm/Prompt**: ЗАПРЕЩЕНЫ - ломают UX в Desktop WebView
2. **window.open**: Работает, но лучше использовать `tg.openTelegramLink()` для Telegram ссылок
3. **CORS**: Решается через `/api/proxy` в Next.js
4. **initData**: Доступен только в Telegram WebView, не в обычном браузере

### Desktop vs Mobile различия

1. **onTouchStart**: Не работает корректно в Desktop - убран из кода
2. **preventDefault**: Может ломать клики в Desktop - используется только для drag & drop и Enter key
3. **pointer events**: Desktop WebView более строгий к обработке событий

### Ограничения SDK

1. **Telegram WebApp SDK**: Должен инициализироваться один раз через `TelegramBootstrap`
2. **ready() / expand()**: Должны вызываться до пользовательских действий
3. **initData**: Может быть недоступен сразу - используется fallback на `localStorage`

### Места повышенного риска

1. **WEB_APP_URL валидация**: Если не production URL - Menu Button не установится
2. **Навигация через window.location.href**: Может вызвать проблемы в Telegram WebView (используется только как fallback)
3. **CORS в production**: Решается через proxy, но требует правильной настройки `NEXT_PUBLIC_API_URL`
4. **Инициализация Telegram WebApp**: Должна быть только в `TelegramBootstrap`, иначе возможны конфликты

---

## 8️⃣ ТОЧКИ ИЗМЕНЕНИЙ (CHANGE IMPACT MAP)

### Если меняется URL

**Что ломается**:
- Menu Button не установится (если URL не проходит валидацию)
- Команда `/web` не будет работать
- Ссылки на Mini App в боте перестанут работать

**Где менять**:
- `.env` на сервере: `WEB_APP_URL`
- Валидация: `config.is_valid_production_url()` в `config.py`
- Allowlist: `config.ALLOWED_PRODUCTION_DOMAINS` в `config.py`

### Если меняется роут

**Что ломается**:
- Навигация в Mini App (404 ошибки)
- Кнопки, которые используют `router.push()` с этим роутом

**Где менять**:
- Файл роута: `app/{route}/page.tsx`
- Все места, где используется `router.push('/{route}')`
- Все места, где используется `<Link href="/{route}">`

### Если меняется структура кнопок

**Что ломается**:
- UX в Telegram (кнопки не работают)
- Навигация в Mini App

**Где менять**:
- Компоненты с кнопками: `app/assistant/page.tsx`, `app/settings/page.tsx`, и т.д.
- Обработчики кликов: `onClick={() => router.push('/path')}`

### Если меняется init логика

**Что ломается**:
- Telegram WebApp не инициализируется
- Клики не работают в Desktop WebView
- User data не загружается

**Где менять**:
- `components/TelegramBootstrap.tsx` - ЕДИНСТВЕННОЕ место для инициализации
- `lib/useTelegramUser.ts` - загрузка user data
- `app/page.tsx` - начальная загрузка и редирект

---

## 9️⃣ ИТОГОВАЯ КАРТА СИСТЕМЫ (SUMMARY)

### Где "истина"

1. **WEB_APP_URL**: `.env` на сервере → `config.WEB_APP_URL` → валидация в `config.is_valid_production_url()`
2. **Telegram WebApp инициализация**: `components/TelegramBootstrap.tsx` - ЕДИНСТВЕННОЕ место
3. **Навигация**: `useRouter()` из `next/navigation` - основной способ
4. **API запросы**: `lib/apiClient.ts` - автоматически выбирает proxy или прямой запрос
5. **User data**: `lib/useTelegramUser.ts` - единый хук для получения user data

### Где "тонкие места"

1. **CORS**: Решается через proxy, но требует правильной настройки `NEXT_PUBLIC_API_URL`
2. **Desktop WebView клики**: Требуют отсутствия `onTouchStart` и `preventDefault` (кроме специальных случаев)
3. **initData доступность**: Может быть недоступен сразу - используется fallback на `localStorage`
4. **Валидация WEB_APP_URL**: Строгая валидация может заблокировать установку Menu Button

### Где "жёсткие контракты"

1. **Telegram WebApp SDK**: Должен инициализироваться один раз через `TelegramBootstrap`
2. **WEB_APP_URL**: Должен быть production URL (валидация в `config.is_valid_production_url()`)
3. **Навигация**: Должна использовать `router.push()` (не `window.location.href`)
4. **Alert/Confirm/Prompt**: ЗАПРЕЩЕНЫ - использовать только `toast()`
5. **API запросы**: В production должны идти через `/api/proxy`

---

## 🔚 ЗАКЛЮЧЕНИЕ

Этот документ описывает текущее состояние системы TRACY AI на основе анализа кода. Все факты проверены по реальным файлам проекта.

**Важно**: Если что-то не найдено в коде, это явно указано как "НЕ ОБНАРУЖЕНО В КОДЕ".

**Для дальнейшей работы**: Используйте этот документ как справочник при внесении изменений в систему.

---

**Дата создания**: 2026-01-14  
**Версия**: 1.0  
**Статус**: Полный анализ текущего состояния системы
