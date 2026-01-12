# Инструкция: Что делать дальше после настройки Render.com

## ✅ Что уже сделано:
- ✅ Код загружен в GitHub (api_server.py, Procfile)
- ✅ PostgreSQL база данных создана
- ✅ Web Service настроен

## 📋 Следующие шаги:

### Шаг 1: Проверьте настройки Web Service на Render.com

1. Откройте ваш Web Service на Render.com
2. Перейдите во вкладку **"Settings"**
3. Убедитесь, что:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python api_server.py` ⚠️ **ВАЖНО: должно быть `api_server.py`, а не `api.py`!**

4. Если Start Command неправильный - исправьте и сохраните

### Шаг 2: Проверьте Environment Variables

1. Во вкладке **"Environment"** убедитесь, что есть:
   - `DATABASE_URL` - должен быть Internal Database URL из PostgreSQL
   - `PORT` - можно оставить пустым (Render сам установит)

### Шаг 3: Запустите деплой

1. Если **Auto-Deploy** включен - Render автоматически начнет деплой после push
2. Если нет - нажмите **"Manual Deploy"** → **"Deploy latest commit"**
3. Дождитесь завершения (обычно 2-3 минуты)

### Шаг 4: Проверьте работу API

1. После успешного деплоя скопируйте URL вашего сервиса (например: `https://tracy-api.onrender.com`)
2. Откройте в браузере: `https://ваш-сервис.onrender.com/health`
3. Должен вернуться JSON: `{"status": "ok", "timestamp": "..."}`

**Если видите ошибку:**
- Проверьте логи: Dashboard → Ваш сервис → Logs
- Убедитесь, что Start Command правильный: `python api_server.py`
- Проверьте, что DATABASE_URL правильно настроен

### Шаг 5: Настройте веб-приложение

1. Откройте файл `web-app/.env.local` (или создайте его, если нет)
2. Добавьте строку:
   ```
   NEXT_PUBLIC_API_URL=https://ваш-сервис.onrender.com
   ```
   (замените `ваш-сервис` на реальное имя вашего сервиса на Render.com)

3. Обновите `web-app/app/calendar/CalendarPageClient.tsx`:
   - Найдите строку: `const apiUrl = \`http://localhost:8080/api/events?user_id=${user.id}\``
   - Замените на:
   ```typescript
   const apiUrl = process.env.NEXT_PUBLIC_API_URL 
     ? `${process.env.NEXT_PUBLIC_API_URL}/api/events?user_id=${user.id}`
     : `http://localhost:8080/api/events?user_id=${user.id}`
   ```

4. Пересоберите и задеплойте веб-приложение на GitHub Pages

### Шаг 6: Проверьте синхронизацию

1. Откройте Telegram бота
2. Создайте тестовое событие (например: "Встреча завтра в 15:00")
3. Нажмите Menu Button "TRACY" в Telegram
4. Откройте веб-приложение
5. Событие должно появиться в календаре!

## ⚠️ Важные замечания:

**Free план Render.com:**
- Сервис засыпает после 15 минут бездействия
- Первый запрос после пробуждения может занять 30-60 секунд
- Для production лучше использовать платный план

**Если что-то не работает:**
1. Проверьте логи на Render.com: Dashboard → Ваш сервис → Logs
2. Убедитесь, что DATABASE_URL правильно настроен
3. Проверьте, что Start Command: `python api_server.py` (не `api.py`!)
4. Убедитесь, что PostgreSQL база данных запущена

## 🎉 Готово!

После выполнения всех шагов синхронизация событий должна работать!




