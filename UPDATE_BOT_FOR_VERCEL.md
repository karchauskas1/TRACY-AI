# 🤖 Обновление бота для Vercel

## После деплоя на Vercel

### 1. Получите URL от Vercel

После деплоя Vercel предоставит URL вида:
- `https://your-project-name.vercel.app`
- Или custom domain: `https://tracy.yourdomain.com`

### 2. Обновите .env на сервере бота

```bash
ssh root@5.35.126.42
cd /opt/tracy-ai-bot
nano .env
```

Измените:
```env
# Было (GitHub Pages):
WEB_APP_URL=https://karchauskas1.github.io/TRACY-AI/

# Стало (Vercel):
WEB_APP_URL=https://your-project-name.vercel.app
```

Сохраните: `Ctrl+O`, `Enter`, `Ctrl+X`

### 3. Перезапустите бота

```bash
systemctl restart tracy-bot.service
systemctl status tracy-bot.service
```

Должно быть: `active (running)`

### 4. Проверьте

```bash
journalctl -u tracy-bot.service -n 50 --no-pager
```

Должно быть:
```
✅ Menu Button установлен: https://your-project-name.vercel.app
```

### 5. Тестируйте в Telegram

1. Откройте бота
2. Отправьте `/web`
3. Должна открыться Mini App с новым URL
4. Проверьте все функции:
   - Чат с Tracy
   - Списки задач
   - Календарь
   - История встреч

---

## Автоматическое обновление (опционально)

Если вы хотите, чтобы бот автоматически обновлял URL при деплое:

### Создайте Vercel Deploy Hook

1. Vercel Dashboard → Settings → Git
2. Create Deploy Hook
3. Скопируйте URL

### Добавьте веб-хук на сервер

```bash
# На сервере бота
cd /opt/tracy-ai-bot
nano update_web_url.sh
```

```bash
#!/bin/bash
# Автообновление WEB_APP_URL после деплоя

NEW_URL="https://your-project-name.vercel.app"

# Обновляем .env
sed -i "s|WEB_APP_URL=.*|WEB_APP_URL=$NEW_URL|" /opt/tracy-ai-bot/.env

# Перезапускаем бота
systemctl restart tracy-bot.service

echo "✅ WEB_APP_URL обновлен на $NEW_URL"
```

Сделайте исполняемым:
```bash
chmod +x update_web_url.sh
```

---

## Troubleshooting

### Бот не открывает Mini App

**Проверьте URL:**
```bash
cat /opt/tracy-ai-bot/.env | grep WEB_APP_URL
```

Должно быть корректным HTTPS URL.

### Mini App открывается, но не работает

1. Проверьте Environment Variables в Vercel
2. Проверьте логи: `vercel logs`
3. Проверьте DevTools в Telegram (Desktop версия)

### "ERR_CONNECTION_REFUSED"

URL неверный или сайт не задеплоен. Проверьте:
```bash
curl -I https://your-project-name.vercel.app
```

Должно быть: `HTTP/2 200`

---

## Готово! 🎉

Теперь бот использует Vercel вместо GitHub Pages!

