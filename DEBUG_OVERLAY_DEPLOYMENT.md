# 🚀 DEBUG OVERLAY - DEPLOYMENT И ТЕСТИРОВАНИЕ

## ✅ РЕАЛИЗОВАНО

### Debug Overlay компонент
- ✅ Создан `web-app/components/DebugOverlay.tsx`
- ✅ Интегрирован в `web-app/app/layout.tsx`
- ✅ Обновлен `web-app/components/TelegramBootstrap.tsx` для экспорта данных
- ✅ Добавлено логирование навигации в `web-app/app/assistant/page.tsx`

### Функциональность
- ✅ Включается через `?debug=1` в URL
- ✅ Capture-лог событий (pointerdown, click, touchstart)
- ✅ Мониторинг Next.js Router (usePathname)
- ✅ Проверка TelegramBootstrap (ready/expand)
- ✅ Manual nav кнопки (router.push и location.assign)
- ✅ Отслеживание ошибок (window.onerror + unhandledrejection)
- ✅ Проверка глобальных блокировок событий

## 📋 DEPLOYMENT STATUS

### ✅ Выполнено:
1. ✅ Изменения закоммичены и запушены в `main`
2. ✅ Vercel автоматически задеплоит изменения

### ⏳ Требуется выполнить вручную:
1. **Перезапустить бота на сервере**:
   ```bash
   ssh root@5.35.126.42
   systemctl restart tracy-bot.service
   systemctl status tracy-bot.service --no-pager
   ```

2. **Дождаться Vercel deployment**:
   - Проверить статус: https://vercel.com/dashboard
   - Production domain: `https://tracy-ai.vercel.app`
   - Убедиться, что deployment завершен успешно

## 🧪 ТЕСТИРОВАНИЕ

### Шаг 1: Открыть Debug Overlay

1. **В Telegram Mini App (mobile)**:
   - Откройте: `https://tracy-ai.vercel.app/assistant?debug=1`
   - Debug Overlay должен появиться поверх контента

2. **В Telegram Desktop (macOS)**:
   - Откройте: `https://tracy-ai.vercel.app/assistant?debug=1`
   - Debug Overlay должен появиться

3. **В обычном браузере**:
   - Откройте: `https://tracy-ai.vercel.app/assistant?debug=1`
   - Для сравнения показаний

### Шаг 2: Проверить показания Overlay

#### A. Telegram Bootstrap
- **ready() called at**: Должно быть время (не "NOT CALLED")
- **expand() called at**: Должно быть время (не "NOT CALLED")
- **Вывод**: Если "NOT CALLED" → TelegramBootstrap не работает

#### B. Event Counts (до клика)
- Запишите начальные значения:
  - pointerdown: X
  - click: X
  - touchstart: X

#### C. Клик на карточку "Чат с Tracy"
1. Кликните на карточку
2. Проверьте Event Counts:
   - pointerdown: должно увеличиться
   - click: должно увеличиться
   - touchstart: должно увеличиться (в mobile)
3. Проверьте Last Click:
   - Target: должен быть `<A>` или `<DIV>`
   - Class: должен содержать классы карточки
   - Href: должен быть `https://tracy-ai.vercel.app/chat`
4. Проверьте Navigation:
   - Last Navigation Attempt: должен показать URL
   - Router Pathname: должен измениться на `/chat`
5. Проверьте Errors:
   - Должно быть "No errors" или показать ошибку

#### D. Manual Navigation
1. Кликните "Manual Navigation" → `/chat (router.push)`
   - Проверьте, изменился ли Router Pathname
   - Если не изменился → router.push не работает
2. Кликните "Manual Navigation" → `/chat (location.assign)`
   - Проверьте, изменился ли Pathname
   - Если изменился → навигация работает через location.assign

### Шаг 3: Записать отчет

Заполните таблицу:

| Параметр | Mobile Telegram | Desktop Telegram | Браузер |
|---|---|---|---|
| **Telegram Bootstrap** |
| ready() called | ✅ / ❌ | ✅ / ❌ | N/A |
| expand() called | ✅ / ❌ | ✅ / ❌ | N/A |
| **Event Counts (до клика)** |
| pointerdown | X | X | X |
| click | X | X | X |
| touchstart | X | X | X |
| **Event Counts (после клика)** |
| pointerdown | X | X | X |
| click | X | X | X |
| touchstart | X | X | X |
| **Last Click** |
| Target | `<tag>` | `<tag>` | `<tag>` |
| Class | `...` | `...` | `...` |
| Href | `...` | `...` | `...` |
| **Navigation** |
| Last Navigation Attempt | `...` | `...` | `...` |
| Router Pathname изменился? | ✅ / ❌ | ✅ / ❌ | ✅ / ❌ |
| **Manual Navigation** |
| router.push работает? | ✅ / ❌ | ✅ / ❌ | ✅ / ❌ |
| location.assign работает? | ✅ / ❌ | ✅ / ❌ | ✅ / ❌ |
| **Errors** |
| Есть ошибки? | ✅ / ❌ | ✅ / ❌ | ✅ / ❌ |
| Текст ошибки | `...` | `...` | `...` |

## 🔍 ДИАГНОСТИКА ПРОБЛЕМ

### Если Event Counts не увеличиваются:
- **Проблема**: События не доходят до window
- **Возможные причины**: Глобальная блокировка событий, overlay блокирует клики
- **Решение**: Проверить, нет ли overlay с `pointer-events: none` или `z-index` выше

### Если Last Click показывает `<DIV>` вместо `<A>`:
- **Проблема**: Link не рендерится как `<a>` тег
- **Возможные причины**: Next.js Link не работает, CSS скрывает тег
- **Решение**: Проверить в DevTools, что Link рендерится как `<a>`

### Если Router Pathname не меняется:
- **Проблема**: Next.js Router не работает
- **Возможные причины**: Проблема с hydration, router не инициализирован
- **Решение**: Проверить, что `isMounted: YES`, попробовать `location.assign`

### Если TelegramBootstrap "NOT CALLED":
- **Проблема**: TelegramBootstrap не выполняется
- **Возможные причины**: SDK не загружен, ошибка в инициализации
- **Решение**: Проверить консоль на ошибки, проверить загрузку SDK

### Если location.assign работает, а router.push нет:
- **Проблема**: Next.js Router не работает в Telegram WebView
- **Возможные причины**: Проблема с клиентской навигацией в WebView
- **Решение**: Использовать `location.assign` как fallback

## 📝 ФИНАЛЬНЫЙ ОТЧЕТ

После тестирования верните отчет с:

1. **Фактические показания overlay** (скрин/текст):
   - Event Counts до и после клика
   - Last Click данные
   - Navigation данные
   - Telegram Bootstrap статус
   - Errors (если есть)

2. **Выводы**:
   - Приходят ли клики? (Event Counts увеличиваются?)
   - Mounted ли React? (isMounted: YES?)
   - Меняется ли pathname? (Router Pathname меняется?)
   - Есть ли ошибки? (Errors раздел)
   - Срабатывает ли router.push? (Manual nav тест)
   - Что делает location.assign? (Manual nav тест)

3. **Подтверждение deployment**:
   - ✅ Бот перезапущен: `systemctl restart tracy-bot.service`
   - ✅ Vercel deployment завершен: `https://tracy-ai.vercel.app`

## 🎯 СЛЕДУЮЩИЕ ШАГИ

После получения отчета с фактическими показаниями overlay:
1. Проанализирую данные
2. Определю точную причину проблемы
3. Реализую фикс на основе инструментальных данных
4. Протестирую фикс
