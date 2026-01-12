# Инструкция по обновлению кода на сервере

## Проблема
API endpoints `/api/todo-lists` и `/api/chat/*` возвращают 404, потому что код на сервере устарел.

## Решение
Необходимо обновить код на сервере и перезапустить бота.

## Шаги обновления

1. Подключиться к серверу:
```bash
ssh root@5.35.126.42
```

2. Перейти в директорию проекта:
```bash
cd /root/TRACY
```

3. Обновить код из репозитория:
```bash
git pull origin main
```

4. Убедиться, что новые файлы присутствуют:
```bash
grep -n "add_get.*todo-lists\|add_get.*chat" http_server.py
```

Должны быть видны строки:
- `app.router.add_get('/api/todo-lists', get_todo_lists_handler)`
- `app.router.add_get('/api/chat/messages', get_chat_messages_handler)`
- `app.router.add_get('/api/chat/greeting', generate_chat_greeting_handler)`
- `app.router.add_post('/api/chat/send', send_chat_message_handler)`

5. Проверить, что таблицы в БД созданы:
```bash
python3 -c "from database import Database; db = Database(); print('Database initialized')"
```

6. Перезапустить бота:
```bash
# Остановить текущий процесс бота
pkill -f "python.*bot.py"
# Или если используется systemd:
systemctl stop tracy-bot  # если есть service

# Запустить бота заново
nohup python3 bot.py > /root/TRACY/logs/bot.log 2>&1 &
# Или через systemd:
systemctl start tracy-bot
```

7. Проверить, что HTTP сервер запущен:
```bash
ps aux | grep -E "python.*bot.py|aiohttp" | grep -v grep
```

8. Проверить логи:
```bash
tail -50 /root/TRACY/logs/bot.log
```

9. Проверить доступность API:
```bash
curl "http://localhost:8080/api/todo-lists?user_id=308477378"
curl "http://localhost:8080/api/chat/greeting?user_id=308477378"
```

## Автоматический скрипт обновления

Если нужно автоматизировать процесс, можно использовать следующий скрипт:

```bash
#!/bin/bash
cd /root/TRACY
git pull origin main
pkill -f "python.*bot.py"
sleep 2
nohup python3 bot.py > /root/TRACY/logs/bot.log 2>&1 &
echo "Bot restarted"
```
