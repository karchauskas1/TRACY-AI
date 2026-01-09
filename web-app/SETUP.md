# Установка и запуск TRACY Web App

## Быстрый старт

1. **Установите зависимости:**
```bash
npm install
```

2. **Настройте переменные окружения:**
```bash
cp .env.local.example .env.local
# Отредактируйте .env.local и заполните необходимые значения
```

3. **Настройте базу данных:**
```bash
# Создайте PostgreSQL базу данных
createdb tracy

# Примените миграции
npm run db:push
# или
npm run db:migrate
```

4. **Запустите приложение:**
```bash
npm run dev
```

Приложение будет доступно по адресу http://localhost:3000

## Важные переменные окружения

- `DATABASE_URL` - строка подключения к PostgreSQL
- `TELEGRAM_BOT_TOKEN` - токен Telegram бота
- `NEXT_PUBLIC_TELEGRAM_BOT_USERNAME` - username бота (без @)
- `NEXTAUTH_SECRET` - секретный ключ для сессий
- `OPENAI_API_KEY` - для обработки аудио встреч
- `OPENROUTER_API_KEY` - для AI функций

## Структура проекта

- `app/` - Next.js App Router страницы и API routes
- `components/` - React компоненты
- `lib/` - утилиты и хелперы
- `prisma/` - схема базы данных

## Дополнительная информация

См. README.md для полной документации.
