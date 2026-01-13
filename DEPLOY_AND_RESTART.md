# Инструкция по деплою и перезапуску

## ✅ GitHub Pages деплой

Изменения уже отправлены в GitHub:
- Commit: `9991699 Fix: Системные исправления Failed to fetch и бесконечной загрузки`
- GitHub Actions автоматически задеплоит веб-приложение на GitHub Pages

Проверить статус деплоя можно здесь:
https://github.com/karchauskas1/TRACY-AI/actions

## 🔄 Перезапуск бота на сервере

Для применения изменений в `http_server.py` (CORS исправления) нужно перезапустить бота на сервере.

### Вариант 1: Через SSH (если есть доступ)

```bash
ssh root@5.35.126.42
cd /root/TRACY  # или /opt/tracy-ai-bot (зависит от установки)
git pull origin main
pkill -f "python.*bot.py"
sleep 2
nohup python3 bot.py > logs/bot.log 2>&1 &
```

### Вариант 2: Если используется systemd

```bash
ssh root@5.35.126.42
cd /root/TRACY  # или /opt/tracy-ai-bot
git pull origin main
systemctl restart tracy-bot
systemctl status tracy-bot
```

### Вариант 3: Если используется supervisor

```bash
ssh root@5.35.126.42
cd /root/TRACY
git pull origin main
supervisorctl restart tracy-bot
```

## 📋 Что изменилось на сервере

1. **http_server.py** - улучшены CORS настройки:
   - Правильная обработка OPTIONS запросов
   - Поддержка GitHub Pages origin
   - Логирование CORS запросов

## ✅ Проверка после перезапуска

1. Проверить, что HTTP сервер запущен:
```bash
curl http://localhost:8080/health
```

2. Проверить CORS:
```bash
curl -X OPTIONS -H "Origin: https://karchauskas1.github.io" \
  -H "Access-Control-Request-Method: GET" \
  -v http://localhost:8080/api/events
```

Должен вернуть 204 с заголовками CORS.

3. Проверить логи:
```bash
tail -f logs/bot.log
# или
journalctl -u tracy-bot -f
```

## 🌐 Веб-приложение

Веб-приложение будет автоматически обновлено через GitHub Actions.
URL: https://karchauskas1.github.io/TRACY-AI/

После деплоя проверьте:
- ✅ Календарь загружается без ошибок
- ✅ Списки задач работают
- ✅ Чат с Tracy работает
- ✅ Обратная связь загружается (для супер-пользователей)
- ✅ Debug страница доступна (для супер-пользователей)

