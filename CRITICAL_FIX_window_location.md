# Критическое исправление: window.location.href

## Проблема
После всех предыдущих исправлений кнопки все еще не работают в веб-приложении.

## Радикальное решение

### Что изменено (Commit: текущий)

**Файл**: `web-app/app/assistant/page.tsx`

1. **Заменил Card на div**
   - Убрал все `<Card>` и `<CardContent>` компоненты
   - Использую простые `<div>` с классами border/rounded

2. **window.location.href вместо router.push**
   ```typescript
   onClick={(e) => {
     e.preventDefault()
     e.stopPropagation()
     console.log("[Assistant] Click: Chat")
     const basePath = process.env.NODE_ENV === 'production' ? '/TRACY-AI' : ''
     window.location.href = `${basePath}/chat/`
   }}
   ```

3. **Добавлен basePath**
   - Вычисляется в runtime: `/TRACY-AI` для production
   - Пустая строка для dev

4. **Touch optimization**
   - Добавлен `style={{ touchAction: 'manipulation' }}`
   - Для корректной работы на мобильных устройствах

5. **Отладка**
   - Каждый клик логируется в консоль
   - Можно отследить срабатывание

## Почему это должно работать

1. **window.location.href** - нативный JavaScript, не зависит от React Router
2. **e.preventDefault()** - останавливает любое дефолтное поведение
3. **e.stopPropagation()** - предотвращает всплытие события
4. **touchAction: manipulation** - убирает задержку 300ms на мобильных

## Как проверить

### 1. Очистите кэш (ОБЯЗАТЕЛЬНО!)
- **Mac**: `Cmd + Shift + R`
- **Windows**: `Ctrl + Shift + F5`

### 2. Откройте консоль
- Нажмите `F12`
- Откройте вкладку Console

### 3. Попробуйте нажать любую кнопку

Вы должны увидеть в консоли:
```
[Assistant] Click: Chat
```
или
```
[Assistant] Click: Calendar
```

Если видите эти логи, но навигация не происходит → проблема в basePath или URL.

### 4. Проверьте URL в консоли

Если кликнули "Чат с Tracy", в адресной строке должно быть:
```
https://karchauskas1.github.io/TRACY-AI/chat/
```

## Если ВСЁЕЩЁ не работает

### Тест 1: Проверьте JavaScript
Откройте консоль и выполните:
```javascript
window.location.href = 'https://karchauskas1.github.io/TRACY-AI/test-navigation/'
```

Если это работает → проблема в обработчиках событий.
Если не работает → проблема в настройках браузера/Telegram.

### Тест 2: Проверьте обработчик
Откройте консоль и выполните:
```javascript
document.querySelector('[class*="cursor-pointer"]').click()
```

Должен появиться лог `[Assistant] Click: ...`

### Тест 3: Telegram WebView
Если открыто в Telegram:
1. Нажмите на три точки (меню)
2. Выберите "Открыть в Safari/Chrome"
3. Проверьте работу в браузере

## Технические детали

### basePath logic
```typescript
const basePath = process.env.NODE_ENV === 'production' ? '/TRACY-AI' : ''
```

В production (GitHub Pages):
- URL: `/TRACY-AI/chat/`

В dev (localhost):
- URL: `/chat/`

### Full click handler
```typescript
onClick={(e) => {
  e.preventDefault()           // Останавливает дефолтное действие
  e.stopPropagation()          // Предотвращает всплытие
  console.log("[Assistant] Click: Chat")  // Отладка
  const basePath = process.env.NODE_ENV === 'production' ? '/TRACY-AI' : ''
  window.location.href = `${basePath}/chat/`  // Навигация
}}
```

## Если проблема продолжается

Пожалуйста, отправьте:

1. **Скриншот консоли** (F12 → Console)
2. **URL из адресной строки**
3. **Браузер и устройство** (Chrome/Safari/iOS/Android)
4. **Где открыто** (Telegram WebView / обычный браузер)

Только с этими данными я смогу понять, где проблема.

---

**Дата**: 2026-01-13  
**Статус**: Задеплоено, ожидание проверки  
**Метод**: Максимально упрощенная навигация через window.location.href

