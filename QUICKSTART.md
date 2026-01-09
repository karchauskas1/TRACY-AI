# Быстрый старт TRACY AI Bot

## Шаг 1: Установка зависимостей

```bash
pip install -r requirements.txt
```

**Опционально:** Установите Tesseract OCR (только если нужна обработка изображений, ~120-230 МБ):
- macOS: `brew install tesseract tesseract-lang`
- Ubuntu: `sudo apt-get install tesseract-ocr tesseract-ocr-rus`

⚠️ **Важно:** Бот работает и без Tesseract! Он нужен только для OCR изображений/скриншотов. Текст и голос обрабатываются без него.

## Шаг 2: Настройка переменных окружения

1. Скопируйте `env.example` в `.env`:
```bash
cp env.example .env
```

2. Заполните обязательные переменные:
- `TELEGRAM_BOT_TOKEN` - получите у [@BotFather](https://t.me/BotFather)
- `OPENROUTER_API_KEY` - получите на [OpenRouter.ai](https://openrouter.ai)

3. Опционально (для календарей):
- Google Calendar: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` из Google Cloud Console
- iCloud: настраивается через команду `/connect_icloud` в боте

## Шаг 3: Запуск

```bash
python bot.py
```

## Шаг 4: Использование

1. Найдите бота в Telegram и отправьте `/start`
2. Подключите календари через `/settings`
3. Отправляйте события естественным языком:
   - "Встреча завтра в 15:00"
   - "Напомни про доклад в пятницу"
   - Голосовое сообщение или изображение с текстом

## Подключение Google Calendar

1. Создайте проект в [Google Cloud Console](https://console.cloud.google.com/)
2. Включите Google Calendar API
3. Создайте OAuth 2.0 credentials (Web application)
4. Добавьте `http://localhost:8080/callback` в redirect URIs
5. Вставьте Client ID и Secret в `.env`
6. В боте: `/settings` → Google Calendar → следуйте инструкциям

## Подключение iCloud Calendar

1. Перейдите на [appleid.apple.com](https://appleid.apple.com)
2. Создайте App-Specific Password
3. В боте выполните: `/connect_icloud <your_apple_id> <app_password>`

## Примеры использования

```
Встреча с командой завтра в 15:00 в офис
```
→ Создаст событие на завтра в 15:00

```
Удали встречу завтра
```
→ Удалит найденное событие

```
/search встреча
```
→ Найдет все события с "встреча" в названии

```
/share встреча с командой
```
→ Отправит сводку и ICS файл события

