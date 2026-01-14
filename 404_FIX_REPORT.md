# 🔧 Fix Report: 404 в Telegram Mini App на Vercel

## Root Cause

**Основная проблема**: Остатки миграции с GitHub Pages на Vercel - в коде остались ссылки на старый basePath `/TRACY-AI`, что вызывает 404 при открытии в Telegram Mini App.

**Конкретные запросы, которые получают 404**:
- `https://your-project.vercel.app/TRACY-AI/assistant/` → 404 (неправильный basePath)
- Любые навигации с использованием старого basePath

## Исправленные файлы

### 1. `web-app/app/click-test/page.tsx`
**Было**:
```typescript
const basePath = process.env.NODE_ENV === 'production' ? '/TRACY-AI' : ''
window.location.href = `${basePath}/assistant/`
```

**Стало**:
```typescript
window.location.href = '/assistant'
```

### 2. `web-app/app/test-navigation/page.tsx`
**Было**:
```typescript
basePath: {process.env.NEXT_PUBLIC_BASE_PATH || "/TRACY-AI"}
```

**Стало**:
```typescript
basePath: (none - root domain)
```

### 3. `bot.py` (строка 3352)
**Было**:
```python
web_app_url = config.WEB_APP_URL or "https://karchauskas1.github.io/TRACY-AI/"
web_app_url_with_events = f"{web_app_url}calendar?events={encoded_data}"
```

**Стало**:
```python
web_app_url = config.WEB_APP_URL
if not web_app_url:
    logger.warning("⚠️ WEB_APP_URL не настроен, не могу отправить события в веб-приложение")
    return
# Убираем trailing slash если есть
web_app_url = web_app_url.rstrip('/')
web_app_url_with_events = f"{web_app_url}/calendar?events={encoded_data}"
```

## Проверка конфигурации

✅ **next.config.js**: Нет `basePath`, `assetPrefix`, `output: 'export'`
✅ **vercel.json**: `trailingSlash: false`, `cleanUrls: true`
✅ **App Router**: Используется правильно (`app/` директория)
✅ **Роутинг**: Все страницы существуют (`app/page.tsx`, `app/assistant/page.tsx`, etc.)

## Дополнительные рекомендации

### 1. Проверьте WEB_APP_URL в боте

Убедитесь, что на сервере бота в `.env` установлен правильный Vercel URL:

```bash
ssh root@5.35.126.42
cd /opt/tracy-ai-bot
cat .env | grep WEB_APP_URL
```

Должно быть:
```
WEB_APP_URL=https://your-project.vercel.app
```

**НЕ должно быть**:
```
WEB_APP_URL=https://karchauskas1.github.io/TRACY-AI/
```

### 2. Перезапустите бота после изменений

```bash
ssh root@5.35.126.42
cd /opt/tracy-ai-bot
systemctl restart tracy-bot.service
```

### 3. Очистите кэш Telegram (если проблема сохраняется)

- Закройте и откройте Telegram заново
- Или переустановите Telegram (крайний случай)

## Smoke Test Checklist

После деплоя проверьте:

### В браузере (Safari/Chrome):
- [ ] `https://your-project.vercel.app/` → Загружается, редирект на `/assistant` или `/login`
- [ ] `https://your-project.vercel.app/assistant` → Загружается корректно
- [ ] `https://your-project.vercel.app/calendar` → Загружается корректно
- [ ] Network tab: все запросы к `/_next/static/*` возвращают 200
- [ ] Network tab: запросы к `/api/proxy` работают (POST с body)

### В Telegram Mini App:
- [ ] Открыть через `/web` команду в боте
- [ ] Главная страница (`/`) загружается
- [ ] Редирект на `/assistant` работает
- [ ] Навигация между страницами работает
- [ ] Нет ошибок 404 в консоли (если доступна)
- [ ] Network requests: все `/_next/static/*` возвращают 200

### Проверка конкретных путей:
- [ ] `GET /` → 200
- [ ] `GET /assistant` → 200
- [ ] `GET /calendar` → 200
- [ ] `GET /_next/static/chunks/main-*.js` → 200
- [ ] `POST /api/proxy` → 200 (с правильным body)

## Другие найденные проблемы (не критичные)

1. ✅ **CORS**: Решено через `/api/proxy` route
2. ✅ **Telegram SDK**: Загружается корректно в `layout.tsx`
3. ✅ **Роутинг**: App Router настроен правильно
4. ⚠️ **Environment variables**: Убедитесь, что в Vercel Dashboard настроены:
   - `NEXT_PUBLIC_API_URL`
   - `INTERNAL_API_BASE`
   - `NEXT_PUBLIC_TELEGRAM_BOT_USERNAME` (опционально)

## Следующие шаги

1. ✅ Исправлены все ссылки на старый basePath
2. ✅ Обновлен fallback URL в боте
3. ⏭️ **Деплой изменений**:
   ```bash
   ./deploy.sh "Fix 404: remove old basePath references"
   ```
4. ⏭️ **Проверка** по smoke test checklist выше
5. ⏭️ **Мониторинг**: Проверьте логи Vercel после деплоя

## Если проблема сохраняется

1. **Проверьте логи Vercel**:
   ```bash
   cd web-app
   npx vercel logs
   ```

2. **Проверьте Network trace в Telegram**:
   - Откройте DevTools (если возможно)
   - Или используйте remote debugging для iOS/Android
   - Найдите конкретный запрос, который возвращает 404

3. **Проверьте, какой URL открывает Telegram**:
   - В боте проверьте `WEB_APP_URL`
   - Убедитесь, что это Vercel URL, а не GitHub Pages

4. **Проверьте Vercel deployment**:
   - Убедитесь, что деплой прошел успешно
   - Проверьте, что используется Production deployment, а не Preview
