# Быстрое развертывание на сервер

## Шаг 1: Запустите скрипт развертывания

```bash
cd "/Users/karchauskas/-TG bots/TRACY AI BOT"
./deploy.sh
```

Скрипт автоматически:
- Установит все необходимые пакеты
- Скопирует файлы на сервер
- Настроит окружения Python и Node.js
- Создаст systemd сервисы
- Настроит nginx

## Шаг 2: Настройка на сервере

Подключитесь к серверу:

```bash
ssh root@5.35.126.42
# Пароль: 7WoEpj3HWex7Fg1Q26
```

Запустите скрипт настройки:

```bash
/opt/tracy-ai-bot/setup_server.sh
```

## Шаг 3: Настройте переменные окружения

Отредактируйте `.env` файл:

```bash
nano /opt/tracy-ai-bot/.env
```

Убедитесь, что установлены все необходимые переменные:
- `TELEGRAM_BOT_TOKEN` - токен Telegram бота
- `OPENROUTER_API_KEY` - ключ API OpenRouter
- `GOOGLE_CLIENT_ID` и `GOOGLE_CLIENT_SECRET` - OAuth данные Google
- `GOOGLE_REDIRECT_URI=http://5.35.126.42/oauth-callback`
- `DATABASE_URL=postgresql://tracy_user:tracy_password_123@localhost:5432/tracy`
- `WEB_APP_URL=http://5.35.126.42`

## Шаг 4: Обновите Google OAuth настройки

1. Перейдите в [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Найдите ваш OAuth 2.0 Client ID
3. Добавьте `http://5.35.126.42/oauth-callback` в список разрешенных redirect URIs

## Шаг 5: Перезапустите сервисы

```bash
systemctl daemon-reload
systemctl restart tracy-bot tracy-api nginx
```

## Проверка работы

Проверьте статус сервисов:

```bash
systemctl status tracy-bot
systemctl status tracy-api
systemctl status nginx
```

Просмотрите логи:

```bash
journalctl -u tracy-bot -f
journalctl -u tracy-api -f
```

Откройте в браузере: http://5.35.126.42

## Полезные команды

```bash
# Перезапуск сервисов
systemctl restart tracy-bot tracy-api

# Просмотр логов
tail -f /var/log/tracy/bot.log
tail -f /var/log/tracy/api.log

# Проверка портов
netstat -tlnp | grep 8080

# Проверка nginx
nginx -t
systemctl status nginx
```



