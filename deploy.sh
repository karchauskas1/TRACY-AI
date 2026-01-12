#!/bin/bash
# Скрипт развертывания TRACY AI BOT на сервере
# Использование: ./deploy.sh

set -e

SERVER="root@5.35.126.42"
SERVER_PASSWORD="7WoEpj3HWex7Fg1Q26"
APP_DIR="/opt/tracy-ai-bot"
WEB_APP_DIR="/opt/tracy-web-app"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🚀 Начинаю развертывание TRACY AI BOT на сервер..."

# Проверяем наличие sshpass
if ! command -v sshpass &> /dev/null; then
    echo "❌ sshpass не установлен. Устанавливаю..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if ! command -v brew &> /dev/null; then
            echo "❌ Homebrew не установлен. Установите его с https://brew.sh"
            exit 1
        fi
        brew install hudochenko/sshpass/sshpass
    else
        echo "❌ Установите sshpass: sudo apt-get install sshpass"
        exit 1
    fi
fi

# Функция для выполнения команд на сервере
ssh_exec() {
    sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "$SERVER" "$@"
}

# Функция для копирования файлов на сервер
scp_copy() {
    sshpass -p "$SERVER_PASSWORD" scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -r "$@"
}

echo "📦 Устанавливаю необходимые пакеты на сервере..."
ssh_exec "apt-get update && apt-get install -y python3 python3-pip python3-venv nodejs npm nginx postgresql postgresql-contrib git sshpass"

echo "📁 Создаю директории на сервере..."
ssh_exec "mkdir -p $APP_DIR $WEB_APP_DIR /var/log/tracy"

echo "📤 Копирую файлы бота на сервер..."
cd "$SCRIPT_DIR"

# Создаем временный архив для передачи файлов
TEMP_DIR=$(mktemp -d)
ARCHIVE_FILE="$TEMP_DIR/tracy-bot.tar.gz"

# Создаем архив, исключая ненужные файлы
tar --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.git' \
    --exclude='node_modules' \
    --exclude='out' \
    --exclude='.next' \
    --exclude='bot.log' \
    --exclude='bot.pid' \
    --exclude='web-app/node_modules' \
    --exclude='web-app/out' \
    --exclude='web-app/.next' \
    --exclude='deploy.sh' \
    --exclude='setup_server.sh' \
    -czf "$ARCHIVE_FILE" .

# Копируем архив на сервер
scp_copy "$ARCHIVE_FILE" "$SERVER:/tmp/tracy-bot.tar.gz"

# Распаковываем на сервере
ssh_exec "cd $APP_DIR && tar -xzf /tmp/tracy-bot.tar.gz && rm /tmp/tracy-bot.tar.gz"

# Очищаем временный файл
rm -f "$ARCHIVE_FILE"
rmdir "$TEMP_DIR" 2>/dev/null || true

echo "🐍 Настраиваю Python окружение..."
ssh_exec "cd $APP_DIR && python3 -m venv venv && source venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt"

echo "📦 Настраиваю Node.js окружение для веб-приложения..."
ssh_exec "cd $WEB_APP_DIR && npm install"

echo "🔧 Настраиваю systemd сервисы..."
ssh_exec "cat > /etc/systemd/system/tracy-bot.service << 'SERVICE_EOF'
[Unit]
Description=TRACY AI Telegram Bot
After=network.target postgresql.service

[Service]
Type=simple
User=root
WorkingDirectory=$APP_DIR
Environment=\"PATH=$APP_DIR/venv/bin\"
# Переменные окружения загружаются через python-dotenv из .env файла
ExecStart=$APP_DIR/venv/bin/python $APP_DIR/bot.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/tracy/bot.log
StandardError=append:/var/log/tracy/bot.log

[Install]
WantedBy=multi-user.target
SERVICE_EOF"

ssh_exec "cat > /etc/systemd/system/tracy-api.service << 'SERVICE_EOF'
[Unit]
Description=TRACY AI API Server
After=network.target postgresql.service

[Service]
Type=simple
User=root
WorkingDirectory=$APP_DIR
Environment=\"PATH=$APP_DIR/venv/bin\"
# Переменные окружения загружаются через python-dotenv из .env файла
ExecStart=$APP_DIR/venv/bin/python $APP_DIR/api_server.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/tracy/api.log
StandardError=append:/var/log/tracy/api.log

[Install]
WantedBy=multi-user.target
SERVICE_EOF"

echo "🌐 Настраиваю nginx..."
ssh_exec "cat > /etc/nginx/sites-available/tracy << 'NGINX_EOF'
# API сервер
server {
    listen 80;
    server_name _;

    # CORS headers для API
    add_header Access-Control-Allow-Origin *;
    add_header Access-Control-Allow-Methods 'GET, POST, OPTIONS';
    add_header Access-Control-Allow-Headers 'Content-Type, Authorization';

    # API endpoints
    location /api/ {
        proxy_pass http://localhost:8080/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \\\$http_upgrade;
        proxy_set_header Connection \"upgrade\";
        proxy_set_header Host \\\$host;
        proxy_set_header X-Real-IP \\\$remote_addr;
        proxy_set_header X-Forwarded-For \\\$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \\\$scheme;
        
        # CORS для preflight
        if (\\\$request_method = 'OPTIONS') {
            add_header Access-Control-Allow-Origin *;
            add_header Access-Control-Allow-Methods 'GET, POST, OPTIONS';
            add_header Access-Control-Allow-Headers 'Content-Type, Authorization';
            add_header Content-Length 0;
            add_header Content-Type text/plain;
            return 204;
        }
    }

    # Веб-приложение
    location / {
        root $WEB_APP_DIR/out;
        try_files \\\$uri \\\$uri/ /index.html;
        index index.html;
    }
}
NGINX_EOF"

ssh_exec "ln -sf /etc/nginx/sites-available/tracy /etc/nginx/sites-enabled/tracy"
ssh_exec "rm -f /etc/nginx/sites-enabled/default"

echo "✅ Развертывание завершено!"
echo ""
echo "📋 Следующие шаги:"
echo "1. Подключитесь к серверу: ssh $SERVER"
echo "2. Создайте файл .env в $APP_DIR с необходимыми переменными окружения"
echo "3. Настройте базу данных PostgreSQL"
echo "4. Соберите веб-приложение: cd $WEB_APP_DIR && npm run build"
echo "5. Запустите сервисы:"
echo "   systemctl daemon-reload"
echo "   systemctl enable tracy-bot tracy-api"
echo "   systemctl start tracy-bot tracy-api"
echo "   systemctl restart nginx"
echo ""
echo "📝 Проверьте логи:"
echo "   journalctl -u tracy-bot -f"
echo "   journalctl -u tracy-api -f"

