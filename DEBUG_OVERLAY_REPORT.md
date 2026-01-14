# 🔍 DEBUG OVERLAY - ИНСТРУМЕНТАЛЬНАЯ ДИАГНОСТИКА

## 📋 РЕАЛИЗОВАНО

### 1. Debug Overlay компонент
- ✅ Файл: `web-app/components/DebugOverlay.tsx`
- ✅ Включается через query параметр `?debug=1`
- ✅ Работает в Telegram и в браузере

### 2. Отображаемая информация
- ✅ **Current pathname**: `window.location.pathname`
- ✅ **Router pathname**: `usePathname()` из Next.js
- ✅ **navigator.userAgent**: User agent браузера/WebView
- ✅ **isTelegram**: Проверка `window.Telegram?.WebApp`
- ✅ **hydration flag**: `isMounted` state (mounted state)
- ✅ **lastClick**: timestamp, target tag, className, href
- ✅ **lastNavigationAttempt**: Последняя попытка навигации
- ✅ **lastError**: window.onerror + unhandledrejection

### 3. Capture-лог событий
- ✅ **pointerdown**: Счетчик событий (capture phase)
- ✅ **click**: Счетчик событий (capture phase)
- ✅ **touchstart**: Счетчик событий (capture phase)
- ✅ Все события логируются на `window` с `capture=true`

### 4. Перехват навигации
- ✅ Логирование "before navigate" на всех Link компонентах
- ✅ Проверка, что Link рендерится как `<a href="...">`
- ✅ Перехват `history.pushState` для отслеживания навигации
- ✅ Перехват кликов на `<a>` тегах

### 5. Мониторинг Next Router
- ✅ `usePathname()` для отслеживания изменений pathname
- ✅ Логирование каждой смены pathname в консоль
- ✅ Отображение router pathname в overlay
- ✅ **Manual nav кнопки**:
  - `/chat` через `router.push()`
  - `/calendar` через `router.push()`
  - `/chat` через `window.location.assign()` (диагностика)
  - `/calendar` через `window.location.assign()` (диагностика)

### 6. TelegramBootstrap мониторинг
- ✅ `window.__tg_bootstrap` объект с метками времени:
  - `readyCalledAt`: Когда был вызван `tg.ready()`
  - `expandCalledAt`: Когда был вызван `tg.expand()`
- ✅ Отображение в overlay с проверкой, что вызывается один раз и ДО кликов

### 7. Проверка глобальных блокировок событий
- ✅ Поиск по проекту: `preventDefault`, `stopPropagation`, `addEventListener('click'/'touch')`
- ✅ Найдено:
  - `web-app/app/meetings/new/page.tsx`: `preventDefault` для drag & drop (валидно)
  - `web-app/app/chat/page.tsx`: `preventDefault` для Enter в textarea (валидно)
  - `web-app/components/DebugOverlay.tsx`: `addEventListener` для диагностики (валидно)
- ✅ **Вывод**: Нет глобальных блокировок на Home/assistant странице

## 📊 КАК ИСПОЛЬЗОВАТЬ

### Включение Debug Overlay:
1. Откройте Telegram Mini App
2. Добавьте `?debug=1` к URL: `https://tracy-ai.vercel.app/assistant?debug=1`
3. Debug Overlay появится поверх всего контента

### Что проверить в Debug Overlay:

1. **Event Counts**:
   - При клике на карточку должны увеличиваться счетчики `pointerdown`, `click`, `touchstart`
   - Если счетчики не увеличиваются → события не доходят до window

2. **Last Click**:
   - Должен показывать последний клик с timestamp, target tag, className, href
   - Если href пустой → Link не рендерится как `<a>`

3. **Telegram Bootstrap**:
   - `ready()` и `expand()` должны быть вызваны ДО первого клика
   - Если "NOT CALLED" → TelegramBootstrap не работает

4. **Navigation**:
   - При клике на Link должен появиться `lastNavigationAttempt`
   - Если не появляется → навигация не инициируется

5. **Router Pathname**:
   - Должен меняться при успешной навигации
   - Если не меняется → router.push не работает

6. **Manual Navigation**:
   - Попробуйте кнопки "router.push" и "location.assign"
   - Если `location.assign` работает, а `router.push` нет → проблема в Next.js router

7. **Errors**:
   - Если есть ошибки, они будут показаны в разделе "Errors"

## 🔧 ИЗМЕНЕННЫЕ ФАЙЛЫ

1. **`web-app/components/DebugOverlay.tsx`** (новый)
   - Полнофункциональный Debug Overlay компонент
   - Capture-лог событий
   - Мониторинг навигации
   - Manual nav кнопки

2. **`web-app/components/TelegramBootstrap.tsx`**
   - Добавлен `window.__tg_bootstrap` объект
   - Логирование времени вызова `ready()` и `expand()`

3. **`web-app/app/layout.tsx`**
   - Добавлен `<DebugOverlay />` компонент

4. **`web-app/app/assistant/page.tsx`**
   - Добавлен `usePathname()` для мониторинга
   - Добавлено логирование "before navigate" на всех Link
   - Добавлен `useEffect` для отслеживания изменений pathname

## 🧪 ТЕСТИРОВАНИЕ

### После deployment:

1. **Откройте в Telegram Mini App (mobile)**:
   - URL: `https://tracy-ai.vercel.app/assistant?debug=1`
   - Проверьте все показания overlay
   - Попробуйте кликнуть на карточки
   - Проверьте, увеличиваются ли счетчики событий
   - Проверьте, меняется ли pathname

2. **Откройте в Telegram Desktop (macOS)**:
   - URL: `https://tracy-ai.vercel.app/assistant?debug=1`
   - Повторите все проверки
   - Особое внимание на счетчики событий (может быть меньше touchstart)

3. **Откройте в обычном браузере**:
   - URL: `https://tracy-ai.vercel.app/assistant?debug=1`
   - Сравните показания с Telegram

### Что записать в отчет:

1. **Event Counts при клике**:
   - pointerdown: X
   - click: X
   - touchstart: X

2. **Last Click**:
   - Target: `<tag>`
   - Class: `...`
   - Href: `...` (если есть)

3. **Telegram Bootstrap**:
   - ready() called at: `...` или `NOT CALLED`
   - expand() called at: `...` или `NOT CALLED`

4. **Navigation**:
   - Last Navigation Attempt: `...` или `(none)`
   - Router Pathname: `...`
   - Меняется ли pathname при клике?

5. **Manual Navigation**:
   - Работает ли `router.push`?
   - Работает ли `location.assign`?

6. **Errors**:
   - Есть ли ошибки в консоли?
   - Есть ли ошибки в overlay?

## 📝 ВАЖНЫЕ ЗАМЕЧАНИЯ

1. **Debug Overlay работает только с `?debug=1`** - не влияет на production
2. **Все события логируются в capture phase** - гарантирует перехват всех событий
3. **TelegramBootstrap выставляет `window.__tg_bootstrap`** - можно проверить в консоли
4. **Нет глобальных блокировок событий** - preventDefault используется только в валидных местах

## 🚀 DEPLOYMENT

После тестирования:
1. ✅ Перезапустить бота: `systemctl restart tracy-bot.service`
2. ✅ Сделать production deployment на Vercel
3. ✅ Подтвердить в отчете оба шага
