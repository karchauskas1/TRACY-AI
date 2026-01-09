# TRACY AI Bot

Производственный MVP AI-ассистента для управления календарем через Telegram.

## Возможности

TRACY принимает пользовательские входы в четырех форматах:
- **Текст** - обычные текстовые сообщения
- **Голосовые сообщения** - распознавание речи (STT)
- **Изображения** - OCR для извлечения текста
- **Скриншоты** - обработка как изображений

### Основные функции

1. **Автоматическое извлечение информации**:
   - Intent (событие/напоминание/заметка)
   - Что (название)
   - Когда (дата/время, явное или выведенное)
   - Где (место)
   - Приоритет

2. **Умное принятие решений**:
   - Автоматическое создание событий в календаре
   - Обновление существующих событий (дедупликация)
   - Создание черновиков при неопределенности
   - Сохранение заметок

3. **Интеграция с календарями**:
   - Google Calendar (OAuth 2.0)
   - Apple iCloud Calendar (CalDAV)
   - Поддержка нескольких календарей одновременно

4. **Команды**:
   - `/search <запрос>` - поиск событий
   - `/settings` - настройки календарей
   - `/help` - справка

## Установка

### Требования

- Python 3.9+
- Tesseract OCR (опционально, только для обработки изображений/скриншотов)
- Google OAuth credentials (опционально, для Google Calendar)
- Apple App-Specific Password (опционально, для iCloud Calendar)

**Примечание:** Бот полностью работает без Tesseract. Он нужен только для извлечения текста из изображений. Для текстовых и голосовых сообщений Tesseract не требуется.

### Установка зависимостей

```bash
pip install -r requirements.txt
```

### Установка Tesseract (опционально, только для OCR изображений)

Tesseract OCR весит ~120-230 МБ (включая языковые данные). Если не планируете обрабатывать изображения, можно пропустить этот шаг.

**macOS:**
```bash
brew install tesseract
brew install tesseract-lang  # для русского языка (~100-200 МБ)
```

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr
sudo apt-get install tesseract-ocr-rus
```

**Windows:**
Скачать с [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)

Если Tesseract не установлен, бот просто сообщит об этом при попытке обработать изображение и продолжит работу с текстом/голосом.

### Настройка

1. Скопируйте `.env.example` в `.env`:
```bash
cp .env.example .env
```

2. Заполните переменные окружения:
- `TELEGRAM_BOT_TOKEN` - токен от @BotFather
- `OPENROUTER_API_KEY` - ключ API от OpenRouter
- `GOOGLE_CLIENT_ID` и `GOOGLE_CLIENT_SECRET` - для Google Calendar OAuth
- `GOOGLE_REDIRECT_URI` - URI для OAuth callback (для MVP можно использовать http://localhost:8080/callback)

### Настройка Google Calendar OAuth

1. Перейдите в [Google Cloud Console](https://console.cloud.google.com/)
2. Создайте проект
3. Включите Google Calendar API
4. Создайте OAuth 2.0 credentials (Web application)
5. Добавьте `http://localhost:8080/callback` в authorized redirect URIs
6. Скопируйте Client ID и Client Secret в `.env`

### Настройка iCloud Calendar

1. Войдите на [appleid.apple.com](https://appleid.apple.com)
2. Создайте App-Specific Password для TRACY
3. Используйте команду `/connect_icloud <apple_id> <app_password>` в боте

## Запуск

```bash
python bot.py
```

## Использование

### Создание событий

Просто напишите боту естественным языком:
```
Встреча с командой завтра в 15:00
```

```
Напомни про доклад в пятницу утром
```

```
Дело на офис в среду
```

### Обновление и удаление

```
Измени встречу на завтра, время 16:00
```

```
Удали встречу с командой
```

### Поиск

```
/search встреча
```

## Архитектура

```
bot.py                    # Основной модуль Telegram бота
├── database.py           # Управление SQLite БД
├── media_processor.py    # Обработка мультимедиа (STT, OCR)
├── nlp_extractor.py     # Извлечение intent через OpenRouter
├── decision_engine.py   # Логика принятия решений
├── calendar_google.py   # Интеграция с Google Calendar
└── calendar_icloud.py   # Интеграция с iCloud Calendar (CalDAV)
```

## Принципы дизайна

- **Нет жесткого синтаксиса команд** - обработка неформальных, естественных входов
- **Предпочитаем предположения вопросам** - делаем лучшее предположение вместо уточнений
- **Минимальные ответы** - короткие, фактологические сообщения

## Нецелевые функции

- Нет общего чата
- Нет менеджера задач
- Нет редактирования изображений/текста (только OCR)

## Лицензия

MIT

