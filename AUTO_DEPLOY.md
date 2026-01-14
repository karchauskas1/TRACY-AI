# 🚀 Автоматический деплой TRACY AI Bot

## Быстрый деплой

Для автоматического деплоя всех изменений выполните:

```bash
./deploy.sh "Описание изменений"
```

Или просто:
```bash
./deploy.sh
```

## Что делает скрипт

1. ✅ **Коммитит изменения** в git
2. ✅ **Отправляет в GitHub** (push)
3. ✅ **Перезапускает бота** на сервере
4. ✅ **Автоматический деплой на Vercel** (если проект подключен через GitHub)

## Требования

### Для автоматического деплоя на Vercel через GitHub:

1. Проект должен быть подключен к Vercel через GitHub
2. В настройках Vercel должен быть включен **Auto Deploy** для ветки `main`
3. Переменные окружения должны быть настроены в Vercel Dashboard

### Проверка подключения:

1. Откройте [Vercel Dashboard](https://vercel.com/dashboard)
2. Найдите проект `TRACY-AI` или создайте новый
3. Подключите репозиторий `karchauskas1/TRACY-AI`
4. Установите:
   - **Framework Preset**: Next.js
   - **Root Directory**: `web-app`
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`

### Переменные окружения в Vercel:

Добавьте в Vercel Dashboard → Settings → Environment Variables:

| Variable | Value | Required |
|----------|-------|----------|
| `NEXT_PUBLIC_API_URL` | `https://api.pasekaproduction.ru` | ✅ Yes |
| `INTERNAL_API_BASE` | `https://api.pasekaproduction.ru` | ✅ Yes |
| `NEXT_PUBLIC_TELEGRAM_BOT_USERNAME` | `your_bot_username` | ⚠️ Optional |

## Альтернатива: Деплой через Vercel CLI

Если хотите использовать CLI вместо GitHub:

1. Получите токен: [Vercel Tokens](https://vercel.com/account/tokens)
2. Установите переменную окружения:
   ```bash
   export VERCEL_TOKEN=your_token_here
   ```
3. Скрипт автоматически использует токен для деплоя

## Ручной деплой

Если нужно выполнить деплой вручную:

```bash
# 1. Коммит и push
git add .
git commit -m "Описание изменений"
git push origin main

# 2. Перезапуск бота
ssh root@5.35.126.42
cd /opt/tracy-ai-bot
systemctl restart tracy-bot.service

# 3. Деплой на Vercel (если не через GitHub)
cd web-app
npx vercel --prod
```

## Мониторинг

После деплоя проверьте:

- ✅ **GitHub**: https://github.com/karchauskas1/TRACY-AI
- ✅ **Vercel**: https://vercel.com/dashboard
- ✅ **Бот**: Отправьте `/web` в Telegram боту

## Troubleshooting

### Деплой на Vercel не происходит автоматически

1. Проверьте, подключен ли проект в Vercel Dashboard
2. Убедитесь, что Auto Deploy включен для ветки `main`
3. Проверьте логи в Vercel Dashboard → Deployments

### Ошибка при перезапуске бота

1. Проверьте подключение к серверу: `ssh root@5.35.126.42`
2. Проверьте статус сервиса: `systemctl status tracy-bot.service`
3. Проверьте логи: `journalctl -u tracy-bot.service -f`

### Ошибка при push в GitHub

1. Проверьте права доступа к репозиторию
2. Убедитесь, что токен GitHub актуален
3. Проверьте подключение: `git remote -v`


