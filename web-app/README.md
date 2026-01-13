# TRACY Web Application

Веб-приложение для управления календарем TRACY - минималистичный интерфейс в стиле Apple.

**🚀 Деплой:** [Vercel](https://vercel.com) | **📱 Telegram Mini App** поддерживается

## Технологии

- **Next.js 14** (App Router) + TypeScript
- **TailwindCSS** + **shadcn/ui** компоненты
- **Vercel** для хостинга и API Proxy
- **Telegram Mini App** нативная поддержка
- **Google Calendar OAuth** интеграция
- **iCloud Calendar CalDAV** интеграция  
- **OpenAI** для обработки встреч

## ⚡ Быстрый старт

### Деплой на Vercel (Production)

См. **[VERCEL_DEPLOY.md](./VERCEL_DEPLOY.md)** для подробных инструкций по деплою.

## Локальная разработка

1. **Установите зависимости:**

```bash
npm install
```

2. **Настройте переменные окружения:**

```bash
cp .env.example .env.local
```

Отредактируйте `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8080
INTERNAL_API_BASE=http://localhost:8080
NEXT_PUBLIC_TELEGRAM_BOT_USERNAME=your_bot_dev
```

3. **Запустите приложение:**

```bash
npm run dev
```

Приложение будет доступно по адресу [http://localhost:3000](http://localhost:3000)

## Production Deploy (Vercel)

Полная инструкция: **[VERCEL_DEPLOY.md](./VERCEL_DEPLOY.md)**

**Кратко:**
1. Подключите репозиторий к Vercel
2. Установите Environment Variables
3. Обновите `WEB_APP_URL` в боте
4. Готово! 🎉

## Архитектура

### Telegram Mini App + Proxy

```
Telegram Mini App 
    ↓
Next.js /api/proxy (Vercel Edge Function)
    ↓
Backend API (api.pasekaproduction.ru)
```

**Преимущества:**
- ✅ Нет CORS ошибок в Telegram WebView
- ✅ Единый подход для Mini App и браузера  
- ✅ Все запросы через один домен
- ✅ Простота отладки

### Структура проекта

```
web-app/
├── app/                    # Next.js App Router
│   ├── api/
│   │   └── proxy/         # 🔥 Next.js API Proxy
│   ├── calendar/          # Календарь
│   ├── chat/              # Чат с Tracy
│   ├── todo-lists/        # Списки задач
│   ├── settings/          # Настройки
│   └── meetings/          # История встреч
├── lib/
│   ├── apiClient.ts       # 🔥 Авто-определение прокси
│   └── useTelegramUser.ts # Telegram SDK
├── vercel.json            # Конфигурация Vercel
└── .env.example           # Пример переменных
```

## API

### Next.js API Routes

- **`POST /api/proxy`** - Универсальный прокси для backend API
  ```typescript
  // Request
  {
    path: '/api/events',
    method: 'GET',
    params: { user_id: 123 }
  }
  
  // Проксирует к: https://api.pasekaproduction.ru/api/events?user_id=123
  ```

### Backend API (через прокси)

**События:**
- `GET /api/events` - Список событий
- `POST /api/events` - Создать событие
- `PUT /api/events/:id` - Обновить событие
- `DELETE /api/events/:id` - Удалить событие

**Чат:**
- `GET /api/chat/messages` - История чата
- `GET /api/chat/greeting` - Приветствие
- `POST /api/chat/send` - Отправить сообщение

**Задачи:**
- `GET /api/todo-lists` - Списки задач
- `POST /api/todo-lists` - Создать список
- `POST /api/todo-lists/:id/items` - Добавить задачу

**Встречи:**
- `GET /api/meetings` - История расшифровок
- `GET /api/meetings/:id` - Детали встречи

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `NEXT_PUBLIC_API_URL` | ✅ Yes | Backend API URL (для клиента) |
| `INTERNAL_API_BASE` | ✅ Yes | Backend API URL (для сервера) |
| `NEXT_PUBLIC_TELEGRAM_BOT_USERNAME` | ⚠️ Optional | Telegram Bot username |

См. `.env.example` для примера.

## Разработка

### Scripts

```bash
# Разработка
npm run dev

# Сборка
npm run build

# Production сервер (локально)
npm start

# Lint
npm run lint

# Type check
npm run type-check
```

### Отладка

**В браузере:** DevTools Console
```
[apiClient] 🔄 Using Next.js proxy
[apiClient] 📡 Next.js Proxy GET /api/events
```

**На Vercel:** `vercel logs`

### Тестирование в Telegram

1. Запустите ngrok для локального тестирования:
   ```bash
   ngrok http 3000
   ```

2. Обновите `WEB_APP_URL` в боте на ngrok URL

3. Откройте бота в Telegram и протестируйте

## Troubleshooting

### "Load failed" в Mini App

1. Проверьте `NEXT_PUBLIC_API_URL` в Vercel
2. Проверьте `INTERNAL_API_BASE` доступен с серверов Vercel
3. Проверьте логи: `vercel logs`

### API возвращает ошибку

1. Откройте DevTools → Network
2. Найдите запрос к `/api/proxy`
3. Проверьте Response

### Telegram Mini App не открывается

1. Проверьте `WEB_APP_URL` в боте
2. Перезапустите бота
3. Проверьте, что URL доступен

## Документация

- **[VERCEL_DEPLOY.md](./VERCEL_DEPLOY.md)** - Деплой на Vercel
- **[MINI_APP_ARCHITECTURE.md](../MINI_APP_ARCHITECTURE.md)** - Архитектура Mini App

## Лицензия

MIT





