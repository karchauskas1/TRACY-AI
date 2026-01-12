# Развертывание TRACY AI BOT на сервере

## Информация о сервере

- **IP адрес**: 5.35.126.42
- **Пользователь**: root
- **Пароль**: 7WoEpj3HWex7Fg1Q26

## Быстрое развертывание

### Шаг 1: Развертывание файлов

Запустите скрипт развертывания с локальной машины:

```bash
chmod +x deploy.sh
./deploy.sh
```

Этот скрипт:
- Установит необходимые пакеты (Python, Node.js, nginx, PostgreSQL)
- Скопирует файлы бота и веб-приложения на сервер
- Настроит Python и Node.js окружения
- Создаст systemd сервисы
- Настроит nginx

### Шаг 2: Настройка на сервере

Подключитесь к серверу:

```bash
ssh root@5.35.126.42
# Пароль: 7WoEpj3HWex7Fg1Q26
```

Запустите скрипт настройки:

```bash
chmod +x /opt/tracy-ai-bot/setup_server.sh
/opt/tracy-ai-bot/setup_server.sh
```

### Шаг 3: Настройка переменных окружения

Отредактируйте файл `.env`:

```bash
nano /opt/tracy-ai-bot/.env
```

Убедитесь, что установлены следующие переменные:

```env
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# OpenRouter API
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=gpt-4o-mini

# Google Calendar OAuth
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
GOOGLE_REDIRECT_URI=http://5.35.126.42/oauth-callback

# ВАЖНО: Обновите GOOGLE_REDIRECT_URI в настройках Google OAuth Console:
# https://console.cloud.google.com/apis/credentials
# Добавьте http://5.35.126.42/oauth-callback в список разрешенных redirect URIs

# Database
DATABASE_URL=postgresql://tracy_user:tracy_password_123@localhost:5432/tracy

# Server
HOST=0.0.0.0
PORT=8080

# Default timezone
DEFAULT_TIMEZONE=Europe/Moscow

# Web Application
WEB_APP_URL=http://5.35.126.42
```

**ВАЖНО**: 
1. Обновите `GOOGLE_REDIRECT_URI` в настройках Google OAuth Console (https://console.cloud.google.com/apis/credentials) на `http://5.35.126.42/oauth-callback`
2. Убедитесь, что все токены и ключи API правильно установлены в `.env`

### Шаг 4: Перезапуск сервисов

После изменения `.env` перезапустите сервисы:

```bash
systemctl restart tracy-bot tracy-api
```

## Управление сервисами

### Проверка статуса

```bash
systemctl status tracy-bot
systemctl status tracy-api
systemctl status nginx
```

### Просмотр логов

```bash
# Логи бота
journalctl -u tracy-bot -f
tail -f /var/log/tracy/bot.log

# Логи API
journalctl -u tracy-api -f
tail -f /var/log/tracy/api.log

# Логи nginx
tail -f /var/log/nginx/error.log
tail -f /var/log/nginx/access.log
```

### Перезапуск сервисов

```bash
systemctl restart tracy-bot
systemctl restart tracy-api
systemctl restart nginx
```

### Остановка сервисов

```bash
systemctl stop tracy-bot
systemctl stop tracy-api
```

### Запуск сервисов

```bash
systemctl start tracy-bot
systemctl start tracy-api
```

## Структура на сервере

```
/opt/tracy-ai-bot/          # Основное приложение бота
├── bot.py                  # Главный файл бота
├── api_server.py           # API сервер
├── .env                    # Переменные окружения
├── venv/                   # Python виртуальное окружение
└── ...

/opt/tracy-web-app/         # Веб-приложение
├── out/                    # Собранное приложение (после npm run build)
├── package.json
└── ...

/var/log/tracy/             # Логи
├── bot.log
└── api.log
```

## Настройка базы данных

База данных PostgreSQL создается автоматически скриптом `setup_server.sh`.

Параметры по умолчанию:
- **База данных**: `tracy`
- **Пользователь**: `tracy_user`
- **Пароль**: `tracy_password_123`

Для изменения пароля:

```bash
sudo -u postgres psql
ALTER USER tracy_user WITH PASSWORD 'новый_пароль';
\q
```

Затем обновите `DATABASE_URL` в `.env`.

## Настройка веб-приложения

Веб-приложение собирается автоматически при запуске `setup_server.sh`.

Для пересборки:

```bash
cd /opt/tracy-web-app
npm run build
systemctl restart nginx
```

## Обновление приложения

1. Обновите файлы на сервере (используйте `deploy.sh` или скопируйте вручную)
2. Перезапустите сервисы:

```bash
systemctl restart tracy-bot tracy-api
```

Если изменились зависимости Python:

```bash
cd /opt/tracy-ai-bot
source venv/bin/activate
pip install -r requirements.txt
systemctl restart tracy-bot tracy-api
```

Если изменились зависимости Node.js:

```bash
cd /opt/tracy-web-app
npm install
npm run build
systemctl restart nginx
```

## Настройка домена (опционально)

Если у вас есть домен, настройте его в nginx:

1. Обновите `/etc/nginx/sites-available/tracy`:

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    # ... остальная конфигурация
}
```

2. Перезапустите nginx:

```bash
systemctl restart nginx
```

3. Обновите `WEB_APP_URL` и `GOOGLE_REDIRECT_URI` в `.env`

## Устранение неполадок

### Бот не запускается

1. Проверьте логи: `journalctl -u tracy-bot -n 50`
2. Проверьте `.env` файл: `cat /opt/tracy-ai-bot/.env`
3. Проверьте права доступа: `ls -la /opt/tracy-ai-bot`

### API не отвечает

1. Проверьте, что API сервер запущен: `systemctl status tracy-api`
2. Проверьте порт: `netstat -tlnp | grep 8080`
3. Проверьте логи: `journalctl -u tracy-api -n 50`

### Веб-приложение не загружается

1. Проверьте nginx: `systemctl status nginx`
2. Проверьте, что приложение собрано: `ls -la /opt/tracy-web-app/out`
3. Проверьте логи nginx: `tail -f /var/log/nginx/error.log`

### Проблемы с базой данных

1. Проверьте, что PostgreSQL запущен: `systemctl status postgresql`
2. Проверьте подключение: `psql -U tracy_user -d tracy -h localhost`
3. Проверьте `DATABASE_URL` в `.env`

## Безопасность

⚠️ **ВАЖНО**: После развертывания:

1. Измените пароль базы данных на более безопасный
2. Настройте firewall (если необходимо)
3. Рассмотрите использование HTTPS (Let's Encrypt)
4. Не храните пароли в открытом виде в скриптах

