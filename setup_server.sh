#!/bin/bash
# Скрипт для настройки сервера после развертывания
# Запускать на сервере после deploy.sh

set -e

APP_DIR="/opt/tracy-ai-bot"
WEB_APP_DIR="/opt/tracy-web-app"

echo "🔧 Настройка сервера TRACY AI BOT..."

# Проверяем наличие .env файла
if [ ! -f "$APP_DIR/.env" ]; then
    echo "⚠️  Файл .env не найден. Создаю из примера..."
    if [ -f "$APP_DIR/env.example" ]; then
        cp "$APP_DIR/env.example" "$APP_DIR/.env"
        echo "✅ Файл .env создан. Пожалуйста, отредактируйте его: nano $APP_DIR/.env"
    else
        echo "❌ Файл env.example не найден!"
        exit 1
    fi
fi

# Настраиваем базу данных PostgreSQL
echo "🗄️  Настраиваю базу данных PostgreSQL..."
sudo -u postgres psql << EOF || true
CREATE DATABASE tracy;
CREATE USER tracy_user WITH PASSWORD 'tracy_password_123';
GRANT ALL PRIVILEGES ON DATABASE tracy TO tracy_user;
\q
EOF

# Обновляем DATABASE_URL в .env если он не установлен
if ! grep -q "DATABASE_URL=" "$APP_DIR/.env" || grep -q "DATABASE_URL=$" "$APP_DIR/.env"; then
    echo "DATABASE_URL=postgresql://tracy_user:tracy_password_123@localhost:5432/tracy" >> "$APP_DIR/.env"
    echo "✅ DATABASE_URL добавлен в .env"
fi

# Создаем необходимые директории
mkdir -p "$APP_DIR/data" "$APP_DIR/tokens" /var/log/tracy

# Устанавливаем права доступа
chmod +x "$APP_DIR"/*.py
chmod +x "$APP_DIR"/*.sh 2>/dev/null || true

# Собираем веб-приложение
echo "🏗️  Собираю веб-приложение..."
cd "$WEB_APP_DIR"

# Создаем .env.local для веб-приложения с правильным API URL
cat > .env.local << EOF
NEXT_PUBLIC_API_URL=http://5.35.126.42/api
EOF

npm install
npm run build

# Обновляем конфигурацию nginx для правильного пути к веб-приложению
echo "🌐 Обновляю конфигурацию nginx..."
sudo tee /etc/nginx/sites-available/tracy > /dev/null << 'NGINX_EOF'
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
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # CORS для preflight
        if ($request_method = 'OPTIONS') {
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
        root /opt/tracy-web-app/out;
        try_files $uri $uri/ /index.html;
        index index.html;
    }
}
NGINX_EOF

# Перезагружаем systemd и запускаем сервисы
echo "🔄 Перезагружаю systemd и запускаю сервисы..."
systemctl daemon-reload
systemctl enable tracy-bot tracy-api
systemctl restart tracy-bot tracy-api
systemctl restart nginx

echo "✅ Настройка завершена!"
echo ""
echo "📊 Статус сервисов:"
systemctl status tracy-bot --no-pager -l | head -5
echo ""
systemctl status tracy-api --no-pager -l | head -5
echo ""
echo "📝 Просмотр логов:"
echo "   journalctl -u tracy-bot -f"
echo "   journalctl -u tracy-api -f"
echo "   tail -f /var/log/tracy/bot.log"
echo "   tail -f /var/log/tracy/api.log"

