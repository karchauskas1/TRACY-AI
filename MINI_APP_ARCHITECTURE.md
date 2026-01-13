# 🏗️ АРХИТЕКТУРА TELEGRAM MINI APP

## Проблема

Telegram WebView **не позволяет** делать прямые HTTP запросы к внешним API (CORS, CSP).

## ✅ ПРАВИЛЬНОЕ РЕШЕНИЕ

Использовать **Telegram Bot API как прокси**.

### Схема работы:

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│  Mini App   │ ──────> │ Telegram Bot │ ──────> │  HTTP API   │
│  (WebView)  │ <────── │   (Proxy)    │ <────── │  (Backend)  │
└─────────────┘         └──────────────┘         └─────────────┘
   postMessage            answerWebAppQuery        fetch/aiohttp
```

### Поток данных:

1. **WebApp → Bot**: `window.Telegram.WebApp.sendData(JSON.stringify(request))`
2. **Bot → API**: Обычный HTTP запрос к `api.pasekaproduction.ru`
3. **API → Bot**: JSON ответ
4. **Bot → WebApp**: `answerWebAppQuery()` или inline message

## 🔧 РЕАЛИЗАЦИЯ

### Вариант 1: iframe + postMessage ✅ ВЫБРАН

**Преимущества:**
- ✅ Двунаправленная связь
- ✅ Быстро
- ✅ Не нужно закрывать Mini App

**Схема:**
```javascript
// В WebApp
window.parent.postMessage({
  type: 'api_request',
  endpoint: '/api/chat/messages',
  method: 'GET',
  params: { user_id: 123 }
}, '*')

// Обработка ответа
window.addEventListener('message', (event) => {
  if (event.data.type === 'api_response') {
    // Обрабатываем данные
  }
})
```

**В боте:**
```python
# Добавляем обработчик WebApp data
async def web_app_data_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = json.loads(update.message.web_app_data.data)
    
    # Делаем запрос к API
    result = await make_api_request(data)
    
    # Отправляем ответ обратно
    await update.message.reply_text(
        json.dumps(result),
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("OK", callback_data="close")
        ]])
    )
```

### Вариант 2: Внедрить Telegram Bot API прямо в HTTP сервер

**Еще лучше:**

Добавить в `http_server.py` специальный эндпоинт `/api/telegram-proxy`, который:
1. Принимает запросы от бота
2. Выполняет их к внутренним эндпоинтам
3. Возвращает результат боту
4. Бот передает в WebApp

## 📝 ПЛАН РЕАЛИЗАЦИИ

### Шаг 1: Обновить HTTP сервер ✅

Добавить эндпоинт `/api/telegram-proxy` для приема запросов от бота.

### Шаг 2: Обновить бота ✅

Добавить обработчик `web_app_data` и `message` с типом `WebAppData`.

### Шаг 3: Обновить apiClient.ts ✅

Заменить прямые `fetch()` на `Telegram.WebApp.sendData()` + слушатель ответов.

### Шаг 4: Обновить все компоненты ✅

- `app/chat/page.tsx`
- `app/todo-lists/page.tsx`
- `app/calendar/CalendarPageClient.tsx`
- `app/feedback/FeedbackPageClient.tsx`

### Шаг 5: Вернуть WebApp кнопку ✅

Вернуть `web_app=WebAppInfo(url=web_url)` в `bot.py`.

### Шаг 6: Развернуть ✅

Обновить на сервере и в GitHub.

### Шаг 7: Тестирование ✅

Проверить в реальном Telegram Mini App.

## 🚀 НАЧИНАЕМ РЕАЛИЗАЦИЮ

Следующие файлы будут изменены:
1. `bot.py` - добавить WebApp data handler
2. `http_server.py` - добавить /api/telegram-proxy
3. `web-app/lib/apiClient.ts` - использовать Telegram.WebApp
4. Все компоненты веб-приложения
5. Деплой на сервер

**Время работы:** ~30-45 минут
**Сложность:** Средняя
**Результат:** Всё работает в Telegram Mini App!

