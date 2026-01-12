# Аудит репозитория TRACY AI BOT

## 0. Ключевые директории и файлы

### Settings → Notifications UI
- **Файл**: `web-app/app/settings/notifications/page.tsx`
- **Компонент**: `NotificationsPage` (client component)
- **Текущее состояние**: 
  - Все настройки в одной карточке
  - Time picker не центрирован
  - Default reminder находится в той же карточке, что и утренний дайджест

### Calendar UI (веб)
- **Файлы**:
  - `web-app/app/calendar/page.tsx` - страница календаря
  - `web-app/app/calendar/CalendarPageClient.tsx` - клиентский компонент
  - `web-app/components/calendar/CalendarGrid.tsx` - сетка календаря
- **Текущее состояние**: 
  - Загрузка событий через Telegram Web App API
  - Есть floating button (нужно убрать)
  - Нужно проверить наличие дублирующей шестерёнки

### History / Transcripts UI
- **Файлы**:
  - `web-app/app/meetings/history/page.tsx` - список истории
  - `web-app/app/meetings/MeetingsPageClient.tsx` - клиентский компонент встреч
  - `web-app/app/meetings/new/page.tsx` - новая встреча
- **Текущее состояние**: 
  - Использует localStorage (моковые данные)
  - Нет реального API для загрузки встреч
  - Кнопки действий не работают

### Backend API
- **Файлы**:
  - `http_server.py` - HTTP API сервер (endpoints: `/api/events`)
  - `api_server.py` - обёртка для запуска API сервера
  - `bot.py` - основной бот (обработка команд, сообщений)
  - `decision_engine.py` - логика создания/обновления событий
  - `database.py` - работа с БД
- **Endpoints**:
  - `GET /api/events?user_id=XXX` - получение событий
  - Нет endpoint для встреч/транскриптов
  - Нет endpoint для создания события из встречи

### Scheduler/Jobs
- **Файлы**:
  - `reminder_scheduler.py` - планировщик напоминаний и утреннего дайджеста
  - `check_reminders.py` - скрипт проверки напоминаний
- **Текущее состояние**:
  - Утренний дайджест проверяется каждые 5 минут (iteration % 10)
  - Не учитывает timezone пользователя точно
  - Не перепланируется при изменении времени

### Интеграции календарей
- **Файлы**:
  - `calendar_google.py` - Google Calendar интеграция
  - `calendar_icloud.py` - iCloud Calendar интеграция (CalDAV)
- **Текущее состояние**:
  - Google Calendar: OAuth flow реализован
  - iCloud: CalDAV подключение работает
  - Нет выбора календаря при создании события

### Telegram bot handlers
- **Файл**: `bot.py`
- **Обработчики**:
  - `handle_message` - обработка сообщений
  - `settings_callback` - обработка настроек
  - `handle_meeting_audio` - обработка аудио встреч
  - Web App data обработка

## Структура проекта

```
TRACY AI BOT/
├── bot.py                    # Основной бот
├── decision_engine.py         # Логика создания событий
├── database.py                # Работа с БД
├── reminder_scheduler.py      # Планировщик напоминаний
├── calendar_google.py         # Google Calendar
├── calendar_icloud.py         # iCloud Calendar
├── meeting_processor.py       # Обработка встреч
├── nlp_extractor.py           # NLP извлечение интентов
├── media_processor.py         # STT/OCR
├── http_server.py             # HTTP API
├── api_server.py              # Обёртка API сервера
└── web-app/
    ├── app/
    │   ├── settings/
    │   │   └── notifications/ # Настройки уведомлений
    │   ├── calendar/          # Календарь
    │   ├── meetings/          # Встречи/транскрипты
    │   └── layout.tsx         # Главный layout
    └── components/
        └── calendar/          # Компоненты календаря
```

## Проблемы и задачи

### A. Settings → Notifications
1. UI: все в одной карточке, нужно разделить на 2
2. Time picker не центрирован
3. Утренний дайджест не учитывает timezone точно

### B. Default Reminder
1. Не применяется автоматически при создании события
2. Не отображается в подтверждении

### C. Calendars
1. Google Calendar: нужно проверить работоспособность
2. Веб-календарь: "Список всех событий" не работает
3. Дублирующая шестерёнка
4. Floating кнопка Tracy

### D. History/Transcripts
1. Нет реального API
2. Кнопки действий не работают
3. Нет детального просмотра

### E. Режим расшифровки встреч
1. Нужно проверить поддержку форматов
2. Добавить тесты

### F. Темы
1. Нет переключателя тем
2. Нет сохранения выбора


