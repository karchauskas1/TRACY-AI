# Статус настройки SSL для api.pasekaproduction.ru

## ✅ Что сделано

1. **Nginx конфигурация обновлена**
   - `server_name` изменен на `api.pasekaproduction.ru`
   - Конфигурация готова для SSL
   - Nginx перезагружен и работает

2. **Скрипт установки SSL создан**
   - Файл: `setup_ssl_api_domain.sh`
   - Автоматически проверяет DNS
   - Устанавливает SSL сертификат через certbot
   - Настраивает редирект HTTP → HTTPS

## ⏳ Текущий статус

**DNS еще не распространился** (это нормально, требуется 5-30 минут, иногда до часа)

DNS запись создана правильно:
- Домен: `api.pasekaproduction.ru`
- Тип: A
- Значение: `5.35.126.42`

## 📋 Что нужно сделать

### Шаг 1: Подождать распространения DNS (5-30 минут)

Проверьте DNS вручную через 10-15 минут:
```bash
dig api.pasekaproduction.ru +short @8.8.8.8
# Ожидаемый результат: 5.35.126.42
```

Или проверьте онлайн:
- https://dnschecker.org/#A/api.pasekaproduction.ru
- Введите: `api.pasekaproduction.ru`
- Выберите тип: A
- Должен вернуться IP: `5.35.126.42`

### Шаг 2: Установить SSL сертификат

Когда DNS распространится, выполните на сервере:

```bash
# Подключитесь к серверу
ssh root@5.35.126.42

# Запустите скрипт установки SSL
bash setup_ssl_api_domain.sh
```

Или выполните вручную:
```bash
certbot --nginx -d api.pasekaproduction.ru \
    --non-interactive \
    --agree-tos \
    --email admin@pasekaproduction.ru \
    --redirect

nginx -t
systemctl reload nginx
```

### Шаг 3: Обновить веб-приложение

После установки SSL, нужно обновить веб-приложение, чтобы использовать HTTPS домен вместо HTTP IP.

Новый API URL: `https://api.pasekaproduction.ru/api/`

## 🔍 Проверка после установки SSL

1. **HTTPS работает:**
   ```bash
   curl -I https://api.pasekaproduction.ru
   # Должен вернуться 200 OK
   ```

2. **HTTP перенаправляет на HTTPS:**
   ```bash
   curl -I http://api.pasekaproduction.ru
   # Должен вернуться 301 Redirect на https://
   ```

3. **API доступен:**
   ```bash
   curl https://api.pasekaproduction.ru/api/events?user_id=308477378
   ```

## 📝 Примечания

- SSL сертификат будет автоматически обновляться каждые 60 дней
- После установки SSL, все HTTP запросы автоматически перенаправляются на HTTPS
- Веб-приложение нужно будет обновить для использования нового HTTPS домена

