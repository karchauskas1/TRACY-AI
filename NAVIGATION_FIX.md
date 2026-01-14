# 🔧 FIX: НАВИГАЦИЯ НЕ РАБОТАЕТ В TELEGRAM MINI APP

## 📋 ПРОБЛЕМА

**Симптомы:**
- Клики доходят (Event Counts увеличиваются)
- `router.push(/chat) called successfully` логируется
- Но pathname НЕ меняется и навигация фактически не происходит

**Возможные причины:**
1. ChunkLoadError - Next.js не может загрузить чанки для новой страницы
2. Runtime crash на целевой странице
3. Агрессивное кеширование в Telegram WebView (старые чанки)
4. Проблема с router.push в Next.js App Router в Telegram WebView

## ✅ ИСПРАВЛЕНИЯ

### 1. ChunkErrorHandler компонент

**Файл:** `web-app/components/ChunkErrorHandler.tsx` (новый)

**Функциональность:**
- Перехватывает ChunkLoadError через `window.onerror` и `unhandledrejection`
- Перехватывает 404 на `_next/static` и `_next/data` через перехват `fetch`
- При обнаружении ошибки делает hard reload с cache-busting параметром

**Код:**
```typescript
// Проверяем на ChunkLoadError
if (errorString.includes("ChunkLoadError") || ...) {
  // Делаем hard reload с cache-busting
  const currentUrl = new URL(window.location.href)
  currentUrl.searchParams.set("_reload", Date.now().toString())
  window.location.href = currentUrl.toString()
}
```

### 2. Cache-busting для Telegram URL

**Файл:** `bot.py`
**Строки:** 3689, 175-178, 194

**Изменения:**
- Добавлен `?v=YYYYMMDDHHMM` к WEB_APP_URL при установке Menu Button
- Добавлен cache-busting в команде `/web`
- Версия меняется каждую минуту (при перезапуске бота)

**Код:**
```python
import datetime
app_version = datetime.datetime.now().strftime("%Y%m%d%H%M")
web_url_with_version = f"{web_url}?v={app_version}"
```

### 3. Cache-Control headers

**Файл:** `web-app/next.config.js`
**Строки:** 44-53

**Изменения:**
- Добавлен `Cache-Control: no-store` для HTML страниц
- Исключены статические файлы (`_next`, `static`, `favicon`, файлы с расширениями)
- Предотвращает кеширование HTML в Telegram WebView

**Код:**
```javascript
{
  source: '/:path((?!_next|static|favicon|.*\\..*).*)',
  headers: [
    {
      key: 'Cache-Control',
      value: 'no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0',
    },
  ],
}
```

### 4. Мониторинг навигации

**Файл:** `web-app/app/assistant/page.tsx`
**Строки:** 181-200, 231-250, 311-330

**Изменения:**
- После `router.push` проверяем через 500мс, изменился ли pathname
- Если pathname не изменился → делаем fallback на `window.location.href`
- Логируем успех/неудачу навигации

**Код:**
```typescript
router.push("/chat")
logger.info('AssistantPage', 'router.push(/chat) called successfully')

// Мониторинг навигации: проверяем через 500мс
setTimeout(() => {
  const newPathname = window.location.pathname
  if (newPathname !== "/chat") {
    logger.error('AssistantPage', 'Navigation failed - pathname did not change', ...)
    // Fallback: hard navigation
    window.location.href = "/chat"
  } else {
    logger.info('AssistantPage', 'Navigation successful - pathname changed to /chat')
  }
}, 500)
```

## 📊 ИЗМЕНЕННЫЕ ФАЙЛЫ

1. **`web-app/components/ChunkErrorHandler.tsx`** (новый)
   - Глобальный обработчик ошибок загрузки чанков
   - Перехват ChunkLoadError, 404 на _next/static
   - Hard reload при обнаружении ошибок

2. **`web-app/app/layout.tsx`**
   - Добавлен `<ChunkErrorHandler />` компонент

3. **`web-app/next.config.js`**
   - Добавлен Cache-Control: no-store для HTML страниц

4. **`web-app/app/assistant/page.tsx`**
   - Добавлен мониторинг навигации с fallback на `window.location.href`
   - Для всех карточек: /chat, /calendar, /todo-lists

5. **`bot.py`**
   - Добавлен cache-busting `?v=YYYYMMDDHHMM` к WEB_APP_URL
   - В Menu Button и команде /web

## 🧪 ПРОВЕРКА

После deployment проверить:

1. **Network запросы при клике:**
   - Открыть DevTools → Network
   - Кликнуть на карточку
   - Проверить:
     - Запросы к `/_next/static/chunks/**` - должны быть 200, не 404
     - Запросы к `/_next/data/**` - должны быть 200, не 404
     - Нет ошибок загрузки чанков

2. **Console ошибки:**
   - Открыть DevTools → Console
   - Кликнуть на карточку
   - Проверить:
     - Нет "ChunkLoadError"
     - Нет "Loading chunk failed"
     - Нет "Failed to fetch"
     - Нет "404" для _next/static

3. **Навигация:**
   - Кликнуть на карточку
   - Pathname должен измениться
   - Страница должна загрузиться
   - В логах должно быть "Navigation successful"

4. **Fallback:**
   - Если router.push не работает, должен сработать fallback на `window.location.href`
   - В логах должно быть "Navigation failed - pathname did not change" → fallback

## 🚀 DEPLOYMENT

- ✅ Изменения закоммичены и запушены в `main`
- ✅ Бот перезапущен на сервере
- ✅ Vercel автоматически задеплоит изменения

## 📝 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ

После deployment:
- ✅ Клики работают
- ✅ router.push вызывает навигацию
- ✅ Pathname меняется при клике
- ✅ Страницы загружаются без ошибок чанков
- ✅ Нет 404 на _next/static
- ✅ Cache-busting предотвращает кеширование старых версий
- ✅ Fallback на window.location.href работает, если router.push не сработал

## 🔍 ДИАГНОСТИКА

Если навигация все еще не работает:

1. **Проверить Network:**
   - Какие запросы идут при клике?
   - Есть ли 404 на _next/static?
   - Какие статусы у запросов?

2. **Проверить Console:**
   - Есть ли ChunkLoadError?
   - Есть ли другие ошибки?
   - Что показывают логи навигации?

3. **Проверить логи:**
   - `window.__TRACY_LOGGER.getLogsAsText()` - что показывают логи?
   - Есть ли "Navigation failed" или "Navigation successful"?

4. **Проверить cache-busting:**
   - Открыть Menu Button URL - есть ли `?v=...`?
   - Обновить страницу - меняется ли версия?
