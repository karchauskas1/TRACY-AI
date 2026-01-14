# 🔍 Root-Cause Analysis: 404 в Telegram Mini App на Vercel

## 0) Собранные факты

### 1. URL, который открывает Telegram Mini App
- **Источник**: `bot.py:165` - `WEB_APP_URL` из переменной окружения
- **Формат**: `https://your-project.vercel.app` (без basePath)
- **Fallback в коде**: `bot.py:3352` - старый URL `https://karchauskas1.github.io/TRACY-AI/`

### 2. Тип 404 ошибки
**Вероятная причина**: 404 на **странице** из-за:
- Старых ссылок с basePath `/TRACY-AI` в коде
- Кэширования старого URL в Telegram
- Deep links с неправильным basePath

### 3. Сравнение поведения
- **Браузер**: Работает (если открыть напрямую Vercel URL)
- **Telegram**: 404 (если открывается URL со старым basePath или кэшированным)

### 4. Конфигурация роутинга Next.js
✅ **App Router** используется (`app/` директория)
✅ `app/page.tsx` существует
✅ `app/layout.tsx` существует  
✅ `app/not-found.tsx` существует
✅ `next.config.js` - **НЕТ** `basePath`, `assetPrefix`, `output: 'export'`
✅ `vercel.json` - `trailingSlash: false`, `cleanUrls: true`

### 5. Найденные проблемы

#### ❌ КРИТИЧНО: Старые basePath ссылки

1. **`web-app/app/click-test/page.tsx:109`**
   ```typescript
   const basePath = process.env.NODE_ENV === 'production' ? '/TRACY-AI' : ''
   window.location.href = `${basePath}/assistant/`
   ```
   **Проблема**: Использует старый basePath в production

2. **`web-app/app/test-navigation/page.tsx:44`**
   ```typescript
   basePath: {process.env.NEXT_PUBLIC_BASE_PATH || "/TRACY-AI"}
   ```
   **Проблема**: Fallback на старый basePath

3. **`bot.py:3352`**
   ```python
   web_app_url = config.WEB_APP_URL or "https://karchauskas1.github.io/TRACY-AI/"
   ```
   **Проблема**: Fallback на старый GitHub Pages URL

## 1) Root Cause

**Основная причина**: Остатки миграции с GitHub Pages на Vercel

1. В коде остались ссылки на старый basePath `/TRACY-AI`
2. Telegram может кэшировать старый URL
3. Deep links могут содержать старый basePath
4. Fallback URL в боте указывает на старый GitHub Pages

**Конкретный запрос, который получает 404**:
- Если Telegram открывает: `https://your-project.vercel.app/TRACY-AI/assistant/` → 404
- Если код делает: `window.location.href = '/TRACY-AI/assistant/'` → 404

## 2) Fix

### Файлы для исправления:

1. `web-app/app/click-test/page.tsx` - убрать basePath
2. `web-app/app/test-navigation/page.tsx` - убрать basePath
3. `bot.py` - обновить fallback URL (опционально, но лучше)

### Дополнительные проверки:

1. Убедиться, что `WEB_APP_URL` в боте указывает на Vercel URL
2. Проверить, нет ли других ссылок на `/TRACY-AI` в коде
3. Очистить кэш Telegram (если возможно)

## 3) Smoke Test Checklist

После фикса проверить:

- [ ] Открыть Vercel URL в браузере → `/` работает
- [ ] Открыть Vercel URL в браузере → `/assistant` работает
- [ ] Открыть в Telegram Mini App → `/` работает
- [ ] Открыть в Telegram Mini App → `/assistant` работает
- [ ] Network tab: все запросы к `/_next/static/*` возвращают 200
- [ ] Network tab: запросы к `/api/proxy` работают
- [ ] Нет ошибок 404 в консоли браузера/Telegram

## 4) Другие найденные проблемы

1. **CORS**: Решено через `/api/proxy` ✅
2. **Telegram SDK**: Загружается корректно ✅
3. **Роутинг**: App Router настроен правильно ✅
4. **Environment variables**: Нужно проверить в Vercel Dashboard
