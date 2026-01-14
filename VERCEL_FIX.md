# 🔧 КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ 404 ОШИБОК

## ✅ ЧТО ПРОВЕРЕНО:

1. **Локальная сборка работает** - все роуты генерируются правильно
2. **Структура проекта правильная** - все page.tsx на месте
3. **Root Directory = web-app** - настроено правильно

## 🐛 ВОЗМОЖНЫЕ ПРИЧИНЫ 404:

### 1. Environment Variables не установлены

**Проверьте в Vercel Dashboard:**
- Settings → Environment Variables
- Должны быть:
  - `NEXT_PUBLIC_API_URL=https://api.pasekaproduction.ru`
  - `NEXT_PUBLIC_TELEGRAM_BOT_USERNAME=ваш_бот_username`

### 2. Build Command неправильный

**Проверьте в Vercel Dashboard:**
- Settings → General → Build & Development Settings
- Build Command должен быть: `npm run build`
- Output Directory должен быть: `.next`

### 3. Кеш Vercel

**Решение:**
1. Deployments → последний деплой
2. Три точки "..." → "Redeploy"
3. Или Settings → General → Clear Build Cache

## 🧪 ТЕСТОВАЯ СТРАНИЦА:

После деплоя проверьте:
- `https://ваш-домен.vercel.app/test` - должна открыться тестовая страница
- Если `/test` работает, а другие нет - проблема в коде страниц
- Если `/test` тоже 404 - проблема в настройках Vercel

## 📋 ЧЕКЛИСТ:

- [ ] Root Directory = `web-app`
- [ ] Build Command = `npm run build`
- [ ] Output Directory = `.next`
- [ ] Environment Variables установлены
- [ ] Сделан Redeploy после изменений
- [ ] Проверена тестовая страница `/test`

