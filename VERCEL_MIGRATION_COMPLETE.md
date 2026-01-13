# ✅ МИГРАЦИЯ НА VERCEL ЗАВЕРШЕНА!

**Дата:** 13 января 2026  
**Статус:** 🎉 ВСЁ ГОТОВО К ДЕПЛОЮ

---

## 📦 ЧТО СДЕЛАНО

### 1. ✅ Обновлен Next.js конфиг

**Удалено:**
```javascript
output: 'export',          // ❌ Static export
basePath: '/TRACY-AI',     // ❌ GitHub Pages basePath
```

**Добавлено:**
```javascript
// SSG/CSR режим для Vercel
reactStrictMode: false,    // Для Telegram SDK
swcMinify: true,          // Оптимизация
images: { unoptimized: false }  // Vercel Image Optimization
```

### 2. ✅ Создан /api/proxy Route Handler

**Файл:** `web-app/app/api/proxy/route.ts`

**Функционал:**
- Принимает: `{ path, method, params, body }`
- Проксирует к Backend API
- Обрабатывает ошибки
- Логирование requests

**Пример использования:**
```typescript
POST /api/proxy
{
  path: '/api/events',
  method: 'GET',
  params: { user_id: 123 }
}

// Проксирует к: https://api.pasekaproduction.ru/api/events?user_id=123
```

### 3. ✅ Обновлен apiClient

**Логика:**
```typescript
// Production (Vercel)
if (!isLocalhost) {
  // Используем /api/proxy
  fetch('/api/proxy', { ... })
}

// Localhost
else {
  // Прямой запрос к API
  fetch('http://localhost:8080/api/...', { ... })
}
```

**Преимущества:**
- Автоматическое определение окружения
- Нет CORS в Telegram WebView
- Единый подход для всех клиентов

### 4. ✅ Создана документация

**Файлы:**
- `web-app/VERCEL_DEPLOY.md` - подробный гайд по деплою
- `web-app/.env.example` - пример переменных окружения
- `web-app/vercel.json` - конфигурация Vercel
- `UPDATE_BOT_FOR_VERCEL.md` - обновление бота
- `web-app/README.md` - обновлен с новой архитектурой

### 5. ✅ Environment Variables

**Требуются:**
```env
NEXT_PUBLIC_API_URL=https://api.pasekaproduction.ru
INTERNAL_API_BASE=https://api.pasekaproduction.ru
NEXT_PUBLIC_TELEGRAM_BOT_USERNAME=your_bot_username
```

---

## 🏗️ АРХИТЕКТУРА

### До (GitHub Pages):

```
Mini App → ❌ CORS Error → Backend API
         ↓
     Python Proxy
         ↓
     Backend API
```

**Проблемы:**
- Static export ограничения
- basePath костыли
- Зависимость от внешнего Python proxy
- CORS в Telegram WebView

### После (Vercel):

```
Mini App/Browser → /api/proxy (Next.js Edge) → Backend API
```

**Преимущества:**
- ✅ Нет CORS ошибок
- ✅ Полноценный Next.js (SSG/CSR)
- ✅ Корневые роуты
- ✅ Vercel Edge Functions
- ✅ Единый API клиент
- ✅ Простая отладка

---

## 🚀 СЛЕДУЮЩИЕ ШАГИ

### Шаг 1: Deploy на Vercel

**Вариант A: Web UI (рекомендуется)**
1. https://vercel.com/new
2. Import Repository
3. Root Directory: `web-app`
4. Framework: Next.js
5. Deploy!

**Вариант B: CLI**
```bash
cd web-app
npm i -g vercel
vercel
```

### Шаг 2: Environment Variables

В Vercel Dashboard → Settings → Environment Variables добавьте:

| Variable | Value |
|----------|-------|
| `NEXT_PUBLIC_API_URL` | `https://api.pasekaproduction.ru` |
| `INTERNAL_API_BASE` | `https://api.pasekaproduction.ru` |
| `NEXT_PUBLIC_TELEGRAM_BOT_USERNAME` | `your_bot` |

**Важно:** Для всех окружений (Production, Preview, Development)

### Шаг 3: Обновить бота

После деплоя получите URL (например, `tracy-web.vercel.app`):

```bash
ssh root@5.35.126.42
cd /opt/tracy-ai-bot
nano .env
```

Измените:
```env
WEB_APP_URL=https://tracy-web.vercel.app
```

Перезапустите:
```bash
systemctl restart tracy-bot.service
```

### Шаг 4: Тестирование

Откройте бота и отправьте `/web`. Проверьте:

**4 Сценария:**
1. ✅ **Mini App: Чат с Tracy** - должен открываться без ошибок
2. ✅ **Mini App: Списки задач** - создание/редактирование работает
3. ✅ **Mini App: Календарь** - события загружаются
4. ✅ **Браузер: Демо-режим** - работает предсказуемо

---

## 📊 ИЗМЕНЕНИЯ В ФАЙЛАХ

### Изменено:

1. **`web-app/next.config.js`**
   - Удалено: `output: 'export'`, `basePath`
   - Добавлено: серверный режим, оптимизации

2. **`web-app/lib/apiClient.ts`**
   - Добавлено: автоопределение окружения
   - Добавлено: использование `/api/proxy` на production

3. **`web-app/README.md`**
   - Обновлена архитектура
   - Добавлены инструкции Vercel

### Создано:

4. **`web-app/app/api/proxy/route.ts`** ⭐ НОВЫЙ
   - Next.js API Route для прокси

5. **`web-app/vercel.json`** ⭐ НОВЫЙ
   - Конфигурация Vercel

6. **`web-app/.env.example`** ⭐ НОВЫЙ
   - Пример переменных окружения

7. **`web-app/VERCEL_DEPLOY.md`** ⭐ НОВЫЙ
   - Подробный гайд по деплою

8. **`UPDATE_BOT_FOR_VERCEL.md`** ⭐ НОВЫЙ
   - Инструкции по обновлению бота

### Удалено:

- ❌ Python `/api/telegram-proxy` (больше не нужен)
- ❌ Костыли с basePath
- ❌ Hardcoded домены в коде

---

## 🔧 ТЕХНИЧЕСКИЕ ДЕТАЛИ

### API Proxy

**Эндпоинт:** `POST /api/proxy`

**Request:**
```json
{
  "path": "/api/events",
  "method": "GET",
  "params": { "user_id": 123 },
  "body": null
}
```

**Response:** Прозрачный прокси результата от Backend API

**Headers:**
- `Content-Type: application/json`
- `User-Agent: Tracy-WebApp-Proxy/1.0`

**Error Handling:**
- 400: Invalid request
- 503: Backend unavailable
- 504: Request timeout
- 500: Proxy error

### apiClient Logic

```typescript
// Определяем окружение
const isLocalhost = window.location.hostname === 'localhost'

if (isLocalhost) {
  // Development: прямой запрос
  fetch('http://localhost:8080/api/events')
} else {
  // Production: через прокси
  fetch('/api/proxy', {
    method: 'POST',
    body: JSON.stringify({
      path: '/api/events',
      method: 'GET'
    })
  })
}
```

---

## 🐛 Troubleshooting

### "Load failed" в Mini App

**Причина:** Неправильные environment variables

**Решение:**
1. Проверьте Vercel → Settings → Environment Variables
2. Убедитесь, что `INTERNAL_API_BASE` доступен с серверов Vercel
3. Проверьте логи: `vercel logs`

### API возвращает 503

**Причина:** Backend недоступен с Vercel

**Решение:**
1. Проверьте firewall на backend сервере
2. Убедитесь, что `5.35.126.42` доступен извне
3. Проверьте: `curl https://api.pasekaproduction.ru/health`

### Telegram Mini App не открывается

**Причина:** Неправильный `WEB_APP_URL` в боте

**Решение:**
1. Проверьте `.env` на сервере бота
2. Убедитесь, что URL корректный HTTPS
3. Перезапустите бота

### DevTools показывает CORS

**Это нормально на localhost!** На production через `/api/proxy` CORS нет.

---

## ✅ CHECKLIST ПЕРЕД ЗАПУСКОМ

- [ ] Vercel проект создан
- [ ] Repository подключен
- [ ] Root Directory: `web-app`
- [ ] Framework: Next.js
- [ ] Environment Variables добавлены:
  - [ ] `NEXT_PUBLIC_API_URL`
  - [ ] `INTERNAL_API_BASE`
  - [ ] `NEXT_PUBLIC_TELEGRAM_BOT_USERNAME`
- [ ] Первый deploy запущен
- [ ] URL получен от Vercel
- [ ] `WEB_APP_URL` обновлен в боте
- [ ] Бот перезапущен
- [ ] Telegram `/web` работает
- [ ] Все 4 сценария протестированы

---

## 🎉 РЕЗУЛЬТАТ

**ДО:**
- ❌ Static export с ограничениями
- ❌ basePath костыли
- ❌ Зависимость от внешнего прокси
- ❌ CORS ошибки в Mini App

**ПОСЛЕ:**
- ✅ Полноценный Next.js на Vercel
- ✅ Корневые роуты без basePath
- ✅ Встроенный Next.js proxy
- ✅ Нет CORS в Mini App
- ✅ Единый API клиент
- ✅ Vercel Edge Functions
- ✅ Автоматический CI/CD

**ГОТОВО К ДЕПЛОЮ!** 🚀

---

## 📚 Документация

- **[VERCEL_DEPLOY.md](web-app/VERCEL_DEPLOY.md)** - Гайд по деплою
- **[UPDATE_BOT_FOR_VERCEL.md](UPDATE_BOT_FOR_VERCEL.md)** - Обновление бота
- **[web-app/README.md](web-app/README.md)** - README проекта

---

**Автор:** AI Assistant  
**Дата:** 13.01.2026  
**Время:** ~60 минут  
**Статус:** ✅ ЗАВЕРШЕНО

