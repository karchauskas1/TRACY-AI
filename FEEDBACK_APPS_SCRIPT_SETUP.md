# Настройка Google Apps Script для обратной связи

## Быстрая установка

### Шаг 1: Открой Google Sheets таблицу
1. Открой свою таблицу Google Sheets
2. Скопируй ID таблицы из URL (между `/d/` и `/edit`)
   - Пример: `https://docs.google.com/spreadsheets/d/ABC123XYZ456/edit`
   - ID: `ABC123XYZ456`

### Шаг 2: Открой Apps Script
1. В таблице: **Расширения** → **Apps Script**
2. Удали весь код по умолчанию
3. Скопируй код из файла `feedback_apps_script.js`
4. Вставь в редактор Apps Script

### Шаг 3: Настрой ID таблицы
1. В коде найди строку:
   ```javascript
   const SPREADSHEET_ID = 'YOUR_SPREADSHEET_ID_HERE';
   ```
2. Замени `YOUR_SPREADSHEET_ID_HERE` на ID своей таблицы
3. Или оставь как есть, если скрипт привязан к текущей таблице

### Шаг 4: Сохрани и запусти
1. Нажми **Сохранить** (Ctrl+S / Cmd+S)
2. Назови проект: `TRACY Feedback`
3. Вернись в таблицу - появится меню **"TRACY Feedback"**
4. Используй меню для тестирования

## Использование

### Вариант 1: Через меню в Google Sheets
1. В таблице: **TRACY Feedback** → **Добавить тестовую запись**
2. Проверь, что запись появилась в листе "Тестировщик Катя"

### Вариант 2: Через HTTP запрос (Webhook)
1. **Развернуть** → **Новое развертывание**
2. Тип: **Веб-приложение**
3. Описание: `TRACY Feedback Webhook`
4. Выполнять от имени: **Меня**
5. У кого есть доступ: **Все**
6. Нажми **Развернуть**
7. Скопируй **URL веб-приложения**

#### Использование URL в Python боте:
Добавь в `.env`:
```
FEEDBACK_WEBHOOK_URL=https://script.google.com/macros/s/YOUR_SCRIPT_ID/exec
```

Или используй напрямую в `feedback_service.py` для отправки через HTTP вместо Google Sheets API.

## Настройка маппинга user_id → лист

В коде настрой маппинг:
```javascript
const SHEET_MAPPING = {
  '332023536': 'Тестировщик Катя',
  '123456789': 'Другой лист',
  // Добавь свои user_id здесь
};
```

## Функции

- `addFeedback(type, userId, comment, screenshotUrl)` - Добавить обратную связь
- `getOrCreateSheet(sheetName)` - Создать лист, если его нет
- `doPost(e)` - HTTP POST обработчик (для webhook)
- `doGet(e)` - HTTP GET обработчик (для тестирования)

## Тестирование

### Через меню:
1. **TRACY Feedback** → **Добавить тестовую запись**
2. Проверь лист "Тестировщик Катя"

### Через URL:
```
https://script.google.com/macros/s/YOUR_SCRIPT_ID/exec?action=test
```

### Через curl:
```bash
curl -X POST "https://script.google.com/macros/s/YOUR_SCRIPT_ID/exec" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "баг",
    "user_id": "332023536",
    "comment": "Тестовое сообщение",
    "screenshot_url": "https://example.com/screenshot.jpg"
  }'
```

## Интеграция с Python ботом

Если хочешь использовать Apps Script вместо Google Sheets API:

1. Получи URL веб-приложения (см. выше)
2. Обнови `feedback_service.py` для отправки HTTP запросов
3. Или используй оба метода (Apps Script как резервный)

## Автоматическое создание листов

Скрипт автоматически создает листы при первом использовании:
- "Тестировщик Катя" (для user_id 332023536)
- "Общий" (для остальных user_id)

## Форматирование

Скрипт автоматически:
- Добавляет заголовки с форматированием
- Настраивает ширину колонок
- Чередует цвета строк
- Создает гиперссылки на скриншоты

