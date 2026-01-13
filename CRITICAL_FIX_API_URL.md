# Критическое исправление: NEXT_PUBLIC_API_URL

## Проблема
В статическом экспорте Next.js (`output: 'export'`) переменные окружения `NEXT_PUBLIC_*` должны быть доступны во время сборки, но они могут не инжектиться правильно в runtime.

## Решение
1. **Fallback в apiClient.ts**: Добавлен fallback на `https://api.pasekaproduction.ru` если переменная не установлена
2. **Инжекция в window**: В `layout.tsx` добавлен скрипт, который устанавливает `window.__NEXT_PUBLIC_API_URL__`
3. **Проверка в getApiBaseUrl()**: Функция теперь проверяет несколько источников:
   - `window.__NEXT_PUBLIC_API_URL__` (инжектится в layout)
   - `process.env.NEXT_PUBLIC_API_URL` (из next.config.js)
   - Fallback на основе hostname

## Проверка
После деплоя проверьте в консоли браузера:
```javascript
console.log(window.__NEXT_PUBLIC_API_URL__)
console.log(process.env.NEXT_PUBLIC_API_URL)
```

## Важно
Убедитесь, что в GitHub Secrets установлено:
- `NEXT_PUBLIC_API_URL=https://api.pasekaproduction.ru`

## Статус
✅ Исправлено в коммитах:
- `9fdab72` - Добавлен fallback для NEXT_PUBLIC_API_URL в runtime
- `85ad907` - Инжекция API URL в window для статического экспорта

