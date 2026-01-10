# Деплой веб-приложения на GitHub Pages

## Быстрый старт

1. **Создай репозиторий на GitHub** (если еще нет)

2. **Запуши код:**
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/ТВОЙ_USERNAME/tracy-ai-bot.git
git branch -M main
git push -u origin main
```

3. **Включи GitHub Pages:**
   - Зайди в Settings → Pages
   - Source: `GitHub Actions`
   - Сохрани

4. **После первого деплоя получи URL:**
   - Будет доступен в Settings → Pages
   - Формат: `https://твой-username.github.io/tracy-ai-bot/`

5. **Добавь URL в `.env` бота:**
```env
WEB_APP_URL=https://твой-username.github.io/tracy-ai-bot/
```

6. **Настрой BotFather:**
   - Открой @BotFather
   - `/setmenubutton`
   - Выбери бота
   - Отправь URL веб-приложения
   - Отправь название: `🌐 TRACY`

Готово! Веб-приложение будет автоматически деплоиться при каждом push в `main`.


