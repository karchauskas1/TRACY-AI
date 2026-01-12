#!/bin/bash
# Скрипт для автоматической установки SSL сертификата через certbot
# Запустите этот скрипт ПОСЛЕ настройки DNS записи для домена yourbody.com

set -e

DOMAIN="yourbody.com"
EMAIL="admin@yourbody.com"  # Замените на ваш email

echo "🔍 Проверка DNS для домена $DOMAIN..."
DNS_IP=$(dig +short $DOMAIN @8.8.8.8 | head -1)
EXPECTED_IP="5.35.126.42"

if [ "$DNS_IP" != "$EXPECTED_IP" ]; then
    echo "❌ ОШИБКА: DNS не настроен!"
    echo "   Текущий IP: $DNS_IP (ожидается: $EXPECTED_IP)"
    echo ""
    echo "📋 Инструкция по настройке DNS:"
    echo "   1. Войдите в панель управления доменом у вашего регистратора"
    echo "   2. Найдите раздел 'DNS Management' / 'DNS Records'"
    echo "   3. Добавьте A-запись:"
    echo "      - Имя: @ (или оставьте пустым)"
    echo "      - Тип: A"
    echo "      - Значение: $EXPECTED_IP"
    echo "   4. Сохраните изменения и подождите 5-30 минут"
    echo ""
    echo "   Затем запустите этот скрипт снова."
    exit 1
fi

echo "✅ DNS настроен правильно: $DOMAIN → $DNS_IP"

echo ""
echo "🔧 Проверка необходимых пакетов..."
if ! command -v certbot &> /dev/null; then
    echo "❌ Certbot не установлен. Установка..."
    apt-get update
    apt-get install -y certbot python3-certbot-nginx
fi

if ! command -v nginx &> /dev/null; then
    echo "❌ Nginx не установлен. Установка..."
    apt-get update
    apt-get install -y nginx
fi

echo "✅ Все необходимые пакеты установлены"

echo ""
echo "🔒 Установка SSL сертификата через certbot..."
certbot --nginx -d $DOMAIN \
    --non-interactive \
    --agree-tos \
    --email $EMAIL \
    --redirect \
    --quiet

if [ $? -eq 0 ]; then
    echo "✅ SSL сертификат успешно установлен!"
    
    echo ""
    echo "🔍 Проверка конфигурации nginx..."
    nginx -t
    
    if [ $? -eq 0 ]; then
        echo "✅ Конфигурация nginx корректна"
        
        echo ""
        echo "🔄 Перезагрузка nginx..."
        systemctl reload nginx
        
        echo ""
        echo "✅ Готово! SSL сертификат установлен и настроен."
        echo ""
        echo "📋 Проверьте:"
        echo "   - HTTPS работает: https://$DOMAIN"
        echo "   - HTTP перенаправляет на HTTPS: http://$DOMAIN"
        echo "   - API доступен: https://$DOMAIN/api/events"
        echo ""
        echo "🔒 Сертификат будет автоматически обновляться каждые 60 дней."
    else
        echo "❌ ОШИБКА: Конфигурация nginx некорректна"
        exit 1
    fi
else
    echo "❌ ОШИБКА: Не удалось установить SSL сертификат"
    echo ""
    echo "Возможные причины:"
    echo "  - DNS еще не распространился (подождите 5-30 минут)"
    echo "  - Порт 80 закрыт (проверьте firewall)"
    echo "  - Nginx не работает (проверьте: systemctl status nginx)"
    exit 1
fi

