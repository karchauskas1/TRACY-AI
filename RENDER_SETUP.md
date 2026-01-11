# Инструкция по настройке Render.com

## Что вы уже сделали:
✅ Создали Web Service на Render.com (Free план)
✅ Настроили Environment

## Что нужно сделать дальше:

### Шаг 1: Подключите PostgreSQL базу данных

1. На Render.com Dashboard нажмите **"New"** → **"PostgreSQL"**
2. Настройки:
   - **Name**: `tracy-db`
   - **Database**: (оставьте по умолчанию)
   - **User**: (оставьте по умолчанию)
   - **Region**: выберите тот же, где ваш Web Service
   - **Plan**: **Free**
3. Нажмите **"Create Database"**
4. **ВАЖНО**: После создания скопируйте **"Internal Database URL"** - он понадобится на следующем шаге

### Шаг 2: Настройте Web Service

1. Перейдите в ваш Web Service на Render.com
2. Во вкладке **"Environment"** добавьте переменные:

   **Обязательные переменные:**
   - `DATABASE_URL` - вставьте Internal Database URL из PostgreSQL (который скопировали на шаге 1)
   - `PORT` - оставьте пустым (Render сам установит)

   **Опционально (если нужно):**
   - `DATABASE_PATH` - можно оставить пустым (используем PostgreSQL)

3. Во вкладке **"Settings"** убедитесь, что:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python api_server.py`

4. Сохраните настройки

### Шаг 3: Деплой на Render.com

✅ **Код уже загружен в GitHub!** (api_server.py и Procfile)

1. На Render.com во вкладке **"Settings"** → **"Build & Deploy"**:
   - Убедитесь, что **"Auto-Deploy"** включен (должен автоматически подхватить изменения)
   - Или нажмите **"Manual Deploy"** → **"Deploy latest commit"**

2. Дождитесь завершения деплоя (обычно 2-3 минуты)

### Шаг 4: Проверьте работу API

1. После деплоя откройте ваш сервис на Render.com
2. Скопируйте URL (например: `https://your-service-name.onrender.com`)
3. Откройте в браузере: `https://your-service-name.onrender.com/health`
4. Должен вернуться: `{"status": "ok", "timestamp": "..."}`

### Шаг 5: Настройте веб-приложение

1. Откройте файл `web-app/.env.local` (или создайте его)
2. Добавьте:
   ```
   NEXT_PUBLIC_API_URL=https://your-service-name.onrender.com
   ```
   (замените `your-service-name` на имя вашего сервиса)

3. Пересоберите веб-приложение и задеплойте на GitHub Pages

### Шаг 6: Обновите CalendarPageClient.tsx

Нужно обновить URL для запроса событий. Откройте `web-app/app/calendar/CalendarPageClient.tsx` и найдите строку:

```typescript
const apiUrl = `http://localhost:8080/api/events?user_id=${user.id}`
```

Замените на:

```typescript
const apiUrl = process.env.NEXT_PUBLIC_API_URL 
  ? `${process.env.NEXT_PUBLIC_API_URL}/api/events?user_id=${user.id}`
  : `http://localhost:8080/api/events?user_id=${user.id}`
```

## Важно:

⚠️ **Free план Render.com:**
- Сервис засыпает после 15 минут бездействия
- Первый запрос может занять 30-60 секунд (холодный старт)
- Для production лучше использовать платный план

✅ **После настройки:**
- Откройте веб-приложение через Menu Button в Telegram
- События должны автоматически синхронизироваться!

## Помощь:

Если что-то не работает:
1. Проверьте логи на Render.com: Dashboard → Ваш сервис → Logs
2. Убедитесь, что DATABASE_URL правильно настроен
3. Проверьте, что все файлы загружены в GitHub

