#!/bin/bash
# Скрипт для установки SSL сертификата для api.pasekaproduction.ru
# Запустите этот скрипт после того, как DNS распространится (5-30 минут)

set -e

DOMAIN="api.pasekaproduction.ru"
EMAIL="admin@pasekaproduction.ru"
EXPECTED_IP="5.35.126.42"

echo "🔍 Проверка DNS для домена $DOMAIN..."
echo ""

# Проверяем DNS через несколько серверов
DNS_CHECKED=false
for DNS_SERVER in 8.8.8.8 1.1.1.1 208.67.222.222; do
    DNS_IP=$(dig +short $DOMAIN @$DNS_SERVER | head -1)
    if [ "$DNS_IP" == "$EXPECTED_IP" ]; then
        echo "✅ DNS настроен правильно через $DNS_SERVER: $DOMAIN → $DNS_IP"
        DNS_CHECKED=true
        break
    else
        echo "⏳ DNS еще не распространился через $DNS_SERVER (текущий IP: ${DNS_IP:-не найден}, ожидается: $EXPECTED_IP)"
    fi
done

echo ""

if [ "$DNS_CHECKED" != "true" ]; then
    echo "❌ DNS еще не распространился!"
    echo ""
    echo "📋 Что делать:"
    echo "   1. Проверьте, что DNS запись создана правильно в панели Reg.ru:"
    echo "      - Тип: A"
    echo "      - Имя: api"
    echo "      - Значение: $EXPECTED_IP"
    echo ""
    echo "   2. Подождите еще 10-30 минут для распространения DNS"
    echo ""
    echo "   3. Проверьте DNS вручную:"
    echo "      dig $DOMAIN +short @8.8.8.8"
    echo ""
    echo "   4. Когда DNS распространится, запустите этот скрипт снова"
    echo ""
    exit 1
fi

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
        echo ""
        echo "📝 Следующий шаг: Обновите веб-приложение, чтобы использовать"
        echo "   https://$DOMAIN вместо http://5.35.126.42:8080"
    else
        echo "❌ ОШИБКА: Конфигурация nginx некорректна"
        exit 1
    fi
else
    echo "❌ ОШИБКА: Не удалось установить SSL сертификат"
    echo ""
    echo "Возможные причины:"
    echo "  - DNS еще не распространился (подождите еще 10-30 минут)"
    echo "  - Порт 80 закрыт (проверьте firewall)"
    echo "  - Nginx не работает (проверьте: systemctl status nginx)"
    exit 1
fi

