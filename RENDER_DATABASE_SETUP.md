# Настройка базы данных на Render.com

## Проблема

Вы получили ошибку:
```json
{"error": "Failed to get or create user"}
```

Это означает, что API на Render.com не может подключиться к базе данных PostgreSQL.

## Решение

### Шаг 1: Создайте PostgreSQL базу данных на Render.com

1. Откройте Render.com Dashboard: https://dashboard.render.com
2. Нажмите **"New +"** → **"PostgreSQL"**
3. Настройки:
   - **Name**: `tracy-db` (или любое другое имя)
   - **Database**: (оставьте по умолчанию)
   - **User**: (оставьте по умолчанию)
   - **Region**: выберите тот же регион, где ваш Web Service (`tracy-api`)
   - **PostgreSQL Version**: (оставьте последнюю версию)
   - **Plan**: **Free** (или платный, если нужен)
4. Нажмите **"Create Database"**
5. **ВАЖНО**: После создания скопируйте **"Internal Database URL"** (не External!)
   - Он выглядит так: `postgresql://tracy-db_user:password@dpg-xxxxx-a/tracy-db`
   - Этот URL нужен для подключения из Web Service

### Шаг 2: Добавьте DATABASE_URL в Web Service

1. Перейдите в ваш **Web Service** на Render.com (например, `tracy-api`)
2. Откройте вкладку **"Environment"**
3. Найдите переменную `DATABASE_URL` (или добавьте её, если нет):
   - **Key**: `DATABASE_URL`
   - **Value**: вставьте **Internal Database URL** из шага 1
   - Например: `postgresql://tracy-db_user:password@dpg-xxxxx-a/tracy-db`
4. Нажмите **"Save Changes"**

### Шаг 3: Перезапустите Web Service

1. После добавления переменной Render.com автоматически перезапустит сервис
2. Или нажмите **"Manual Deploy"** → **"Deploy latest commit"**
3. Дождитесь завершения деплоя (обычно 2-3 минуты)

### Шаг 4: Проверьте логи

1. Перейдите в ваш Web Service на Render.com
2. Откройте вкладку **"Logs"**
3. Должны быть логи вида:
   ```
   Используется PostgreSQL
   🚀 Запуск API сервера на порту 10000
   ```
   Если есть ошибки подключения к базе данных - проверьте `DATABASE_URL`

### Шаг 5: Проверьте API

1. Откройте в браузере: `https://tracy-api.onrender.com/health`
   - Должно вернуться: `{"status": "ok", "timestamp": "..."}`
2. Откройте: `https://tracy-api.onrender.com/api/events?user_id=308477378`
   - Должно вернуться: `{"success": true, "events": [], "count": 0, "timestamp": "..."}`
   - Если все еще ошибка - проверьте логи на Render.com

## Важно

⚠️ **Internal Database URL vs External Database URL:**
- **Internal Database URL** - используется внутри Render.com (для Web Services)
- **External Database URL** - для подключения извне (например, с вашего компьютера)

Для Web Service нужно использовать **Internal Database URL**!

## Если все еще не работает

1. Проверьте логи на Render.com в разделе "Logs"
2. Убедитесь, что `DATABASE_URL` правильно скопирован (без пробелов)
3. Убедитесь, что PostgreSQL база данных создана и работает (зеленый статус)
4. Попробуйте пересоздать базу данных





