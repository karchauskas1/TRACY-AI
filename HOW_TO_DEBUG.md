# 🔍 КАК ПРАВИЛЬНО СМОТРЕТЬ ЛОГИ И ДАВАТЬ ОБРАТНУЮ СВЯЗЬ

## 📋 ПРОБЛЕМА

Мы топчемся на месте, потому что не получаем точных данных о том, что происходит. Нужна структурированная система логирования и четкие инструкции.

## ✅ РЕШЕНИЕ

Создана система структурированного логирования с категориями и метками времени.

## 🎯 КАК СМОТРЕТЬ ЛОГИ В TELEGRAM WEBVIEW

### Вариант 1: Telegram Desktop (macOS/Windows/Linux)

1. **Откройте Telegram Desktop**
2. **Откройте Mini App** (через Menu Button или команду `/web`)
3. **Откройте DevTools**:
   - **macOS**: `Cmd + Option + I` или `View → Developer → Show Web Inspector`
   - **Windows/Linux**: `Ctrl + Shift + I` или `View → Developer → Show Web Inspector`
4. **Перейдите на вкладку Console**
5. **Фильтруйте логи**: Введите в поиск `[INFO]` или `[ERROR]` или `[AssistantPage]`

### Вариант 2: Telegram Mobile (iOS/Android)

**iOS:**
1. Подключите iPhone к Mac
2. Откройте Safari на Mac
3. `Develop → [Ваш iPhone] → [Telegram WebView]`
4. Откройте Console

**Android:**
1. Включите USB Debugging на Android
2. Подключите к компьютеру
3. Откройте Chrome на компьютере
4. `chrome://inspect` → найдите Telegram WebView
5. Откройте Console

### Вариант 3: Обычный браузер (для сравнения)

1. Откройте `https://tracy-ai.vercel.app/assistant` в браузере
2. Откройте DevTools (`F12` или `Cmd+Option+I`)
3. Перейдите на вкладку Console

## 📊 ФОРМАТ ЛОГОВ

Логи имеют структурированный формат:

```
[Время] [Уровень] [Категория] Сообщение | Data: {...}
```

**Примеры:**
```
[14:20:15] [INFO] [AssistantPage] Component mounted | Data: {"userLoading":false,"userId":"123456"}
[14:20:16] [DEBUG] [AssistantPage] Click on Чат с Tracy | Data: {"targetTag":"DIV","currentTargetTag":"DIV"}
[14:20:16] [INFO] [AssistantPage] Calling router.push(/chat) | Data: {"beforePathname":"/assistant"}
[14:20:16] [INFO] [AssistantPage] router.push(/chat) called successfully
[14:20:17] [INFO] [AssistantPage] Pathname changed | Data: {"pathname":"/chat"}
```

## 🔍 КАК ЭКСПОРТИРОВАТЬ ЛОГИ

### Способ 1: Через консоль браузера

1. Откройте консоль
2. Выполните команду:
```javascript
// Получить все логи в текстовом формате
window.__TRACY_LOGGER.getLogsAsText()

// Или экспортировать в JSON
window.__TRACY_LOGGER.exportLogs()
```

3. Скопируйте результат и отправьте

### Способ 2: Через Debug Overlay

1. Откройте `?debug=1`
2. В Debug Overlay будет раздел "Logs Export"
3. Скопируйте логи

## 📝 ФОРМАТ ОБРАТНОЙ СВЯЗИ

### Обязательные данные:

1. **Среда тестирования:**
   - [ ] Telegram Desktop (macOS/Windows/Linux)
   - [ ] Telegram Mobile (iOS/Android)
   - [ ] Обычный браузер

2. **Действие:**
   - Что именно вы делали? (например: "Кликнул на карточку 'Чат с Tracy'")

3. **Результат:**
   - Что произошло? (например: "Переход не произошел, остался на /assistant")
   - Есть ли ошибки в консоли?

4. **Логи из консоли:**
   - Скопируйте все логи с префиксом `[AssistantPage]` или `[ERROR]`
   - Или выполните `window.__TRACY_LOGGER.getLogsAsText()` и отправьте результат

5. **Debug Overlay данные** (если доступен):
   - Event Counts (до и после клика)
   - Last Click данные
   - Router Pathname (изменился ли?)
   - Errors (если есть)

### Пример правильной обратной связи:

```
Среда: Telegram Desktop (macOS)
Действие: Кликнул на карточку "Чат с Tracy"
Результат: Переход не произошел, остался на /assistant

Логи из консоли:
[14:20:16] [DEBUG] [AssistantPage] Click on Чат с Tracy | Data: {"targetTag":"DIV","currentTargetTag":"DIV"}
[14:20:16] [INFO] [AssistantPage] Calling router.push(/chat) | Data: {"beforePathname":"/assistant"}
[14:20:16] [INFO] [AssistantPage] router.push(/chat) called successfully
[14:20:17] [INFO] [AssistantPage] Pathname changed | Data: {"pathname":"/assistant"}

Debug Overlay:
- Event Counts: click: 78 (увеличился)
- Last Click: Target: DIV
- Router Pathname: /assistant (НЕ изменился!)
- Errors: Нет

Вывод: router.push вызывается, но pathname не меняется
```

## 🎯 ЧТО ИСКАТЬ В ЛОГАХ

### 1. Проверка клика:
```
[DEBUG] [AssistantPage] Click on ...
```
- Должен появиться при каждом клике
- Если нет → клик не доходит до обработчика

### 2. Проверка router.push:
```
[INFO] [AssistantPage] Calling router.push(...)
[INFO] [AssistantPage] router.push(...) called successfully
```
- Должны появиться оба лога
- Если нет второго → ошибка в router.push

### 3. Проверка изменения pathname:
```
[INFO] [AssistantPage] Pathname changed | Data: {"pathname":"/chat"}
```
- Должен появиться после успешной навигации
- Если pathname не изменился → навигация не произошла

### 4. Проверка ошибок:
```
[ERROR] [AssistantPage] Error in router.push(...)
```
- Если есть → это причина проблемы

## 🚨 ЧАСТЫЕ ПРОБЛЕМЫ И РЕШЕНИЯ

### Проблема: Логи не видны в консоли
**Решение:**
1. Убедитесь, что консоль открыта
2. Проверьте фильтры (может быть включен фильтр по уровню)
3. Попробуйте очистить консоль и повторить действие

### Проблема: window.__TRACY_LOGGER не определен
**Решение:**
1. Обновите страницу
2. Убедитесь, что код загрузился
3. Проверьте, нет ли ошибок загрузки скриптов

### Проблема: Логи слишком много
**Решение:**
1. Используйте фильтры в консоли: `[AssistantPage]` или `[ERROR]`
2. Экспортируйте только нужные логи через `window.__TRACY_LOGGER.getLogs()`

## 📌 ВАЖНО

1. **Всегда копируйте логи полностью** - даже если кажется, что они не важны
2. **Указывайте точное время** - когда произошло действие
3. **Описывайте результат** - что вы видите, а не что вы думаете
4. **Прикрепляйте скриншоты** - если возможно

## 🎯 ЦЕЛЬ

Получить точные данные о том, что происходит:
- ✅ Клик доходит до обработчика?
- ✅ router.push вызывается?
- ✅ router.push выполняется успешно?
- ✅ pathname меняется?
- ✅ Есть ли ошибки?

С этими данными мы сможем точно определить проблему и исправить её.
