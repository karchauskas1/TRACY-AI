# 🚀 Деплой TRACY Web App на Vercel

## Быстрый старт

### 1. Подготовка

1. Создайте аккаунт на [Vercel](https://vercel.com)
2. Установите Vercel CLI (опционально):
   ```bash
   npm i -g vercel
   ```

### 2. Деплой

#### Вариант A: Через веб-интерфейс (рекомендуется)

1. Откройте [Vercel Dashboard](https://vercel.com/dashboard)
2. Нажмите **"Add New Project"**
3. Импортируйте репозиторий GitHub
4. В настройках проекта:
   - **Framework Preset**: Next.js
   - **Root Directory**: `web-app`
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`

#### Вариант B: Через CLI

```bash
cd web-app
vercel
```

### 3. Environment Variables

Добавьте в Vercel Dashboard → Settings → Environment Variables:

| Variable | Value | Required |
|----------|-------|----------|
| `NEXT_PUBLIC_API_URL` | `https://api.pasekaproduction.ru` | ✅ Yes |
| `INTERNAL_API_BASE` | `https://api.pasekaproduction.ru` | ✅ Yes |
| `NEXT_PUBLIC_TELEGRAM_BOT_USERNAME` | `your_bot_username` | ⚠️ Optional |

**Для всех окружений:** Production, Preview, Development

### 4. Обновите бота

После деплоя получите URL (например, `tracy-web.vercel.app`):

```bash
ssh root@5.35.126.42
cd /opt/tracy-ai-bot
nano .env
```

Добавьте:
```env
WEB_APP_URL=https://tracy-web.vercel.app
```

Перезапустите бота:
```bash
systemctl restart tracy-bot.service
```

### 5. Проверка

Откройте Telegram бота и отправьте `/web`. Должна открыться Mini App.

Проверьте:
- ✅ Чат с Tracy работает
- ✅ Списки задач работают
- ✅ Календарь загружается
- ✅ История встреч доступна

---

## 🏗️ Архитектура

### Прокси для обхода CORS

```
Telegram Mini App → /api/proxy (Next.js API Route) → Backend API
```

**Преимущества:**
1. ✅ Нет CORS ошибок в Telegram WebView
2. ✅ Единый подход для Mini App и браузера
3. ✅ Все запросы через один домен
4. ✅ Простота отладки

### Структура

```
web-app/
├── app/
│   ├── api/
│   │   └── proxy/
│   │       └── route.ts      # Прокси для backend API
│   ├── (pages)/
│   └── layout.tsx
├── lib/
│   └── apiClient.ts          # Автоматически использует прокси
├── next.config.js            # БЕЗ export/basePath
├── vercel.json               # Конфигурация Vercel
└── .env.example              # Пример переменных окружения
```

---

## 🔧 Разработка

### Локально

```bash
cd web-app

# Установить зависимости
npm install

# Скопировать .env
cp .env.example .env.local

# Отредактировать .env.local
nano .env.local

# Запустить dev сервер
npm run dev
```

Откройте http://localhost:3000

### Environment Variables

Создайте `web-app/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8080
INTERNAL_API_BASE=http://localhost:8080
NEXT_PUBLIC_TELEGRAM_BOT_USERNAME=your_bot_dev
```

---

## 🐛 Troubleshooting

### Ошибка "Load failed" в Mini App

**Причина:** Неправильный `NEXT_PUBLIC_API_URL` или `INTERNAL_API_BASE`

**Решение:**
1. Проверьте переменные окружения в Vercel
2. Перезапустите деплой
3. Проверьте логи: `vercel logs`

### API возвращает 503

**Причина:** Backend API недоступен с серверов Vercel

**Решение:**
1. Проверьте, что `INTERNAL_API_BASE` корректен
2. Убедитесь, что backend доступен извне
3. Проверьте firewall на backend сервере

### Telegram Mini App не открывается

**Причина:** Неправильный URL в боте

**Решение:**
1. Проверьте `WEB_APP_URL` в `.env` на сервере бота
2. Перезапустите бота: `systemctl restart tracy-bot.service`
3. Отправьте `/web` в Telegram

---

## 📊 Мониторинг

### Vercel Dashboard

- **Analytics**: Просмотры, пользователи, регионы
- **Logs**: Логи функций и API routes
- **Deployments**: История деплоев

### Useful Commands

```bash
# Логи последнего деплоя
vercel logs

# Список деплоев
vercel ls

# Открыть в браузере
vercel open
```

---

## 🚀 CI/CD

Vercel автоматически деплоит:
- **Production**: При push в `main`
- **Preview**: При создании Pull Request

Каждый PR получает уникальный preview URL для тестирования.

---

## 📚 Документация

- [Next.js on Vercel](https://nextjs.org/docs/deployment)
- [Vercel Environment Variables](https://vercel.com/docs/concepts/projects/environment-variables)
- [Telegram Mini Apps](https://core.telegram.org/bots/webapps)

---

## ✅ Checklist после деплоя

- [ ] Environment variables добавлены
- [ ] Домен прописан в боте (`WEB_APP_URL`)
- [ ] Бот перезапущен
- [ ] Проверено в Telegram Mini App
- [ ] Проверено в обычном браузере
- [ ] Все 4 сценария работают:
  - [ ] Чат с Tracy
  - [ ] Списки задач
  - [ ] Календарь
  - [ ] История встреч

---

**Готово!** Ваше приложение работает на Vercel! 🎉

