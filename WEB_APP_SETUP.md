# Инструкция: Настройка веб-приложения для использования Render.com API

## ✅ Что уже сделано:
- ✅ API сервер работает на Render.com: `https://tracy-api.onrender.com`
- ✅ Веб-приложение обновлено для использования `NEXT_PUBLIC_API_URL`

## 📋 Следующие шаги:

### Шаг 1: Настройте переменную окружения в веб-приложении

1. Откройте файл `web-app/.env.local` (или создайте его, если нет)

2. Добавьте строку:
   ```
   NEXT_PUBLIC_API_URL=https://tracy-api.onrender.com
   ```

   **ВАЖНО:** Замените `tracy-api.onrender.com` на реальный URL вашего сервиса на Render.com (если он другой)

### Шаг 2: Пересоберите веб-приложение

1. Перейдите в директорию `web-app`:
   ```bash
   cd web-app
   ```

2. Установите зависимости (если еще не установлены):
   ```bash
   npm install
   ```

3. Соберите веб-приложение:
   ```bash
   npm run build
   ```

   Или для production:
   ```bash
   npm run export
   ```

### Шаг 3: Задеплойте веб-приложение на GitHub Pages

После сборки файлы будут в директории `web-app/out/`. 

1. Сделайте commit и push:
   ```bash
   git add .
   git commit -m "Update web app to use Render.com API"
   git push
   ```

2. GitHub Actions автоматически задеплоит веб-приложение на GitHub Pages

### Шаг 4: Проверьте синхронизацию

1. Откройте Telegram бота
2. Создайте тестовое событие (например: "Встреча завтра в 15:00")
3. Нажмите Menu Button "TRACY" в Telegram
4. Откройте веб-приложение
5. Событие должно появиться в календаре! 🎉

## 🔍 Проверка работы API:

Вы можете проверить API напрямую:
- `https://tracy-api.onrender.com/` - информация о сервисе ✅
- `https://tracy-api.onrender.com/health` - health check
- `https://tracy-api.onrender.com/api/events?user_id=YOUR_USER_ID` - получить события (замените YOUR_USER_ID на ваш Telegram user_id)

## ⚠️ Важно:

**Free план Render.com:**
- Сервис засыпает после 15 минут бездействия
- Первый запрос может занять 30-60 секунд (холодный старт)
- Для production лучше использовать платный план

**Для production:**
- Используйте платный план Render.com для постоянной работы сервера
- Или настройте мониторинг для предотвращения засыпания



