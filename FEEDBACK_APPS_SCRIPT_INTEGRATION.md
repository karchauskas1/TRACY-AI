# Интеграция Apps Script с Python ботом

## ✅ Готово

URL веб-приложения Apps Script интегрирован в Python бота:
```
https://script.google.com/macros/s/AKfycbzQ17_OdWUEaXtLJINWj9zJVZjsJsRQDYwD6uAwHMKYYv9ssmgb8C9D-IEWbho95399rg/exec
```

## Как это работает

### Автоматическое использование Apps Script

Если в `.env` указан `FEEDBACK_APPS_SCRIPT_URL`, бот **автоматически** будет использовать Apps Script webhook вместо прямого Google Sheets API.

### Преимущества Apps Script

1. **Не требует OAuth авторизации** - не нужно авторизовать каждого пользователя
2. **Проще настройка** - просто скопируй URL
3. **Автоматическое создание листов** - Apps Script сам создает нужные листы
4. **Форматирование** - автоматическое форматирование таблицы

### Fallback механизм

Если Apps Script не работает (ошибка сети, таймаут), бот автоматически переключится на обычный способ записи через Google Sheets API (если настроен OAuth).

## Настройка

### 1. Добавь URL в `.env`

```bash
FEEDBACK_APPS_SCRIPT_URL=https://script.google.com/macros/s/AKfycbzQ17_OdWUEaXtLJINWj9zJVZjsJsRQDYwD6uAwHMKYYv9ssmgb8C9D-IEWbho95399rg/exec
```

### 2. (Опционально) Настрой маппинг user_id

Если нужно добавить других пользователей в Apps Script, отредактируй `feedback_apps_script.js`:

```javascript
const SHEET_MAPPING = {
  '332023536': 'Тестировщик Катя',
  '123456789': 'Другой лист',  // Добавь здесь
};
```

### 3. Перезапусти бота

После добавления URL в `.env` перезапусти бота, чтобы изменения вступили в силу.

## Тестирование

### Через бота

1. Отправь боту: `/start` → "💬 Обратная связь"
2. Выбери "Сообщить о баге" или "Сделать предложение"
3. Введи текст
4. (Опционально) Отправь скриншот
5. Проверь таблицу Google Sheets - должна появиться запись в листе "Тестировщик Катя"

### Прямой тест Apps Script

```bash
curl -X POST "https://script.google.com/macros/s/AKfycbzQ17_OdWUEaXtLJINWj9zJVZjsJsRQDYwD6uAwHMKYYv9ssmgb8C9D-IEWbho95399rg/exec" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "баг",
    "user_id": "332023536",
    "comment": "Тестовое сообщение",
    "screenshot_url": "https://example.com/screenshot.jpg"
  }'
```

Ожидаемый ответ:
```json
{
  "success": true,
  "number": 1,
  "date": "2026-01-12 18:45:00",
  "sheet": "Тестировщик Катя"
}
```

## Логирование

Бот логирует все операции с обратной связью:

- ✅ Успешная отправка через Apps Script
- ⚠️ Fallback на Google Sheets API (если Apps Script не сработал)
- ❌ Ошибки отправки

Проверь логи бота для диагностики:
```bash
tail -f bot.log | grep -i feedback
```

## Два способа записи

### Способ 1: Apps Script (рекомендуется)
- ✅ Не требует OAuth
- ✅ Проще настройка
- ✅ Автоматическое форматирование
- ⚠️ Зависит от доступности Apps Script

### Способ 2: Google Sheets API (резервный)
- ✅ Прямой доступ к API
- ✅ Больше контроля
- ⚠️ Требует OAuth для каждого пользователя
- ⚠️ Нужна настройка credentials

## Устранение неполадок

### Apps Script не работает

1. Проверь, что URL правильный
2. Проверь, что веб-приложение развернуто с доступом "Все"
3. Проверь логи бота на наличие ошибок
4. Бот автоматически переключится на Google Sheets API

### Записи не появляются в таблице

1. Проверь, что скрипт правильно установлен в Apps Script
2. Проверь, что лист "Тестировщик Катя" существует
3. Проверь логи Apps Script: **Вид** → **Журнал выполнения** в редакторе Apps Script

### Ошибка 401/403

- Убедись, что веб-приложение развернуто с доступом "Все"
- Проверь настройки развертывания в Apps Script

