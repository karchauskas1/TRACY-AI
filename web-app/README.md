# TRACY Web Application

Веб-приложение для управления календарем TRACY - минималистичный интерфейс в стиле Apple.

## Технологии

- **Next.js 14** (App Router) + TypeScript
- **TailwindCSS** + **shadcn/ui** компоненты
- **Prisma** + PostgreSQL
- **Telegram Login** для авторизации
- **Google Calendar OAuth** интеграция
- **iCloud Calendar CalDAV** интеграция
- **OpenAI** для обработки встреч

## Установка

1. Установите зависимости:

```bash
npm install
```

2. Настройте переменные окружения:

Скопируйте `.env.example` в `.env` и заполните необходимые значения:

```bash
cp .env.example .env
```

3. Настройте базу данных:

```bash
# Создайте миграцию
npm run db:migrate

# Или используйте push для разработки
npm run db:push
```

4. Запустите приложение:

```bash
npm run dev
```

Приложение будет доступно по адресу [http://localhost:3000](http://localhost:3000)

## Структура проекта

```
web-app/
├── app/                    # Next.js App Router страницы
│   ├── api/               # API endpoints
│   ├── calendar/          # Страница календаря
│   ├── event/             # Детали события
│   ├── settings/          # Настройки
│   └── meetings/          # Встречи и резюме
├── components/            # React компоненты
│   ├── ui/               # shadcn/ui компоненты
│   ├── calendar/         # Компоненты календаря
│   └── event/            # Компоненты событий
├── lib/                   # Утилиты и хелперы
│   ├── auth.ts           # Авторизация
│   ├── prisma.ts         # Prisma client
│   └── utils.ts          # Утилиты
└── prisma/               # Prisma схема и миграции
    └── schema.prisma
```

## API Endpoints

### Авторизация
- `POST /api/auth/telegram` - Вход через Telegram
- `POST /api/auth/logout` - Выход

### Пользователь
- `GET /api/me` - Получить текущего пользователя
- `PATCH /api/me` - Обновить настройки пользователя

### События
- `GET /api/events?from=YYYY-MM-DD&to=YYYY-MM-DD` - Получить события за период
- `GET /api/events/day?date=YYYY-MM-DD` - Получить события за день
- `GET /api/events/:id` - Получить событие
- `POST /api/events` - Создать событие
- `PATCH /api/events/:id` - Обновить событие
- `DELETE /api/events/:id` - Удалить событие

### Календари
- `GET /api/calendars` - Список подключенных календарей
- `POST /api/calendars/google/connect` - Подключить Google Calendar
- `POST /api/calendars/icloud/connect` - Подключить iCloud Calendar

### Встречи
- `POST /api/meetings` - Загрузить аудио встречи
- `GET /api/meetings` - Список встреч
- `GET /api/meetings/:id` - Детали встречи

## Переменные окружения

См. `.env.example` для полного списка переменных.

## Разработка

### Запуск в режиме разработки

```bash
npm run dev
```

### Сборка для продакшена

```bash
npm run build
npm start
```

### Работа с базой данных

```bash
# Генерация Prisma Client
npm run db:generate

# Создание миграции
npm run db:migrate

# Открыть Prisma Studio
npm run db:studio
```

## Лицензия

MIT



