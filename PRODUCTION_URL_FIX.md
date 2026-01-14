# 🔒 Фиксация Production URL для Telegram Mini App

## Проблема

Telegram-бот использовал preview deployment URL (`https://tracy-ele1bcvza-karchauskas-projects.vercel.app`), что **НЕДОПУСТИМО** для Telegram Mini App.

**Почему это проблема**:
- Telegram кэширует Menu Button URL
- Preview deployments нестабильны
- Preview deployments могут быть удалены
- Preview deployments могут содержать устаревший код
- Это ломает Mini App в проде

## Решение

### 1. Зафиксирован Production URL

**Production domain**: `https://tracy-ai.vercel.app`

Этот URL:
- ✅ Используется в Telegram Menu Button
- ✅ Используется в коде бота
- ✅ Используется в `.env`
- ✅ НИГДЕ не переопределяется

### 2. Добавлена валидация URL

**Файл**: `config.py`

**Функция**: `is_valid_production_url(url: str) -> bool`

**Запрещает**:
- ❌ Preview URLs (содержат `-projects.vercel.app`)
- ❌ URLs с hash/slug (например, `tracy-abc123.vercel.app`)
- ❌ localhost
- ❌ не-HTTPS URLs

**Разрешает только**:
- ✅ Явные production домены из allowlist
- ✅ Production Vercel domains без hash

**Allowlist production доменов**:
```python
ALLOWED_PRODUCTION_DOMAINS = [
    "tracy-ai.vercel.app",  # Основной production domain
]
```

### 3. Обновлен код установки Menu Button

**Файл**: `bot.py` (строка 3678-3690)

**Логика**:
1. Проверяет `WEB_APP_URL` из конфигурации
2. Валидирует через `config.is_valid_production_url()`
3. Если валиден → устанавливает Menu Button
4. Если не валиден → **НЕ устанавливает** и логирует ошибку

**Пример логирования**:
```
❌ WEB_APP_URL не является production URL: https://tracy-ele1bcvza-karchauskas-projects.vercel.app
   Preview deployments ЗАПРЕЩЕНЫ для Telegram Mini App.
   Используйте только production domain (например: https://tracy-ai.vercel.app)
```

### 4. Обновлена команда /web

**Файл**: `bot.py` (функция `web_command`)

**Логика**:
- Проверяет валидность URL перед использованием
- Если не валиден → показывает сообщение пользователю
- Логирует ошибку

### 5. Добавлена документация

**Файл**: `config.py`

**Комментарии**:
```python
# Telegram Mini App ВСЕГДА использует production domain.
# Preview deployments ЗАПРЕЩЕНЫ.
# 
# Production URL должен быть явно указан в .env:
# WEB_APP_URL=https://tracy-ai.vercel.app
#
# НЕ используйте:
# - preview URLs (содержат -projects.vercel.app или hash)
# - branch deployments
# - автоматическую генерацию URL
```

## Измененные файлы

1. ✅ `config.py`
   - Добавлена функция `is_valid_production_url()`
   - Добавлен `ALLOWED_PRODUCTION_DOMAINS`
   - Добавлена документация

2. ✅ `bot.py`
   - Обновлена установка Menu Button с валидацией
   - Обновлена команда `/web` с валидацией

## Настройка .env

**На сервере бота** (`/opt/tracy-ai-bot/.env`):

```env
WEB_APP_URL=https://tracy-ai.vercel.app
```

**НЕ используйте**:
```env
# ❌ НЕПРАВИЛЬНО
WEB_APP_URL=https://tracy-ele1bcvza-karchauskas-projects.vercel.app
WEB_APP_URL=https://tracy-abc123.vercel.app
WEB_APP_URL=http://localhost:3000
```

## Проверка

После применения изменений:

1. **Проверьте логи бота**:
   ```
   ✅ Menu Button установлен с production URL: https://tracy-ai.vercel.app
   ```

2. **Проверьте Menu Button в Telegram**:
   - Откройте бота в Telegram
   - Проверьте Menu Button (кнопка внизу)
   - Должен открываться `https://tracy-ai.vercel.app`

3. **Проверьте команду /web**:
   - Отправьте `/web` боту
   - Должен открыться production URL

## Архитектурная защита

**Теперь невозможно**:
- ❌ Установить preview URL через код
- ❌ Установить preview URL через .env (будет отклонен)
- ❌ Автоматически подхватить preview URL из CI/CD

**Гарантировано**:
- ✅ Только production URL может быть установлен
- ✅ Валидация происходит на уровне кода
- ✅ Ошибки логируются явно
- ✅ Поведение стабильно между деплоями

## Результат

После фикса:
- ✅ Telegram Menu Button всегда открывает production
- ✅ Preview deployments никогда не попадают в Telegram
- ✅ Поведение стабильно между деплоями
- ✅ Баг не может повториться архитектурно
