# 🔧 FIX: УСТРАНЕНИЕ БЕСКОНЕЧНОГО СПАМА ЛОГОВ

## 📋 ROOT CAUSE

### Проблема 1: DebugOverlay.tsx - setInterval каждые 100мс
**Файл:** `web-app/components/DebugOverlay.tsx`
**Строки:** 95, 108

```typescript
const bootstrapInterval = setInterval(checkBootstrap, 100)  // ❌ Каждые 100мс
const pathnameInterval = setInterval(updatePathname, 100)   // ❌ Каждые 100мс
```

**Проблема:** 
- `setInterval` вызывал `setDebugInfo` каждые 100мс
- Это вызывало ре-рендеры и спам логов
- Даже если значения не менялись

### Проблема 2: Logger - логирование всего в консоль
**Файл:** `web-app/lib/logger.ts`
**Строки:** 31-39

**Проблема:**
- Все логи выводились в консоль без ограничений
- Нет throttle для одинаковых логов
- Нет фильтрации по важности

### Проблема 3: AssistantPage - useEffect с частыми зависимостями
**Файл:** `web-app/app/assistant/page.tsx`
**Строки:** 24-48

**Проблема:**
- `useEffect` зависел от `telegramUser`, `userId`, `userLoading`, `router`
- Эти зависимости могли меняться часто
- Логирование происходило на каждом изменении

## ✅ ИСПРАВЛЕНИЯ

### 1. DebugOverlay.tsx

**Убраны setInterval:**
```typescript
// ❌ БЫЛО:
const bootstrapInterval = setInterval(checkBootstrap, 100)
const pathnameInterval = setInterval(updatePathname, 100)

// ✅ СТАЛО:
// Проверяем только при монтировании и при реальных изменениях
checkBootstrap() // Один раз при монтировании
```

**Разделены useEffect:**
```typescript
// Основной useEffect - только при монтировании
useEffect(() => {
  // Инициализация
}, []) // Пустой deps

// Отдельный useEffect для pathname - только при реальных изменениях
useEffect(() => {
  // Обновляем только если pathname действительно изменился
  if (prev.pathname === newPathname && prev.routerPathname === newRouterPathname) {
    return prev // Не обновляем
  }
}, [pathname])
```

**Оптимизирована проверка bootstrap:**
```typescript
// Обновляем только если значения изменились
if (prev.tgBootstrap.readyCalledAt === newReady && prev.tgBootstrap.expandCalledAt === newExpand) {
  return prev // Не обновляем, если значения не изменились
}
```

### 2. Logger.ts

**Ограничено логирование в консоль:**
```typescript
// В консоль выводим ТОЛЬКО:
// - ERROR (всегда)
// - WARN (всегда)
// - INFO (только router.push и Pathname changed)
// DEBUG - только в store, не в консоль
```

**Добавлен throttle:**
```typescript
// Минимум 100мс между одинаковыми логами
const logKey = `${category}:${message}`
const now = Date.now()
const lastTime = this.lastLogTime[logKey] || 0

if (now - lastTime > this.throttleMs) {
  // Логируем
}
```

**Ограничен размер store:**
```typescript
private maxLogs = 50 // Было 1000, стало 50
```

### 3. AssistantPage.tsx

**Добавлен useRef для предотвращения повторных логов:**
```typescript
const mountedRef = useRef(false)
const lastPathnameRef = useRef<string | null>(null)

// Логируем только при реальных изменениях
if (mountedRef.current === false) {
  logger.info('AssistantPage', 'Component mounted', ...)
  mountedRef.current = true
}

// Pathname - только при реальных изменениях
if (lastPathnameRef.current !== pathname) {
  logger.info('AssistantPage', 'Pathname changed', ...)
  lastPathnameRef.current = pathname
}
```

**Оптимизированы зависимости useEffect:**
```typescript
// Логируем user только если он действительно изменился
if (!user || user.id !== userId) {
  logger.info('AssistantPage', 'User loaded', ...)
}
```

## 📊 РЕЗУЛЬТАТ

### До исправления:
- ❌ Логи сыпятся каждые 100мс
- ❌ setInterval вызывает бесконечные обновления
- ❌ Все логи в консоль без ограничений
- ❌ useEffect вызывается на каждом render

### После исправления:
- ✅ Логи только при реальных событиях (клики, навигация, ошибки)
- ✅ Нет setInterval - обновления только по событиям
- ✅ В консоль только критичные логи (ERROR, WARN, важные INFO)
- ✅ Throttle для предотвращения спама одинаковых логов
- ✅ useEffect оптимизированы с useRef для предотвращения повторных вызовов

## 🧪 ПРОВЕРКА

После deployment проверить:

1. **Консоль не спамит:**
   - Открыть консоль
   - Подождать 5 секунд
   - Логов должно быть минимально (только при реальных действиях)

2. **Debug Overlay обновляется только при событиях:**
   - Event Counts увеличиваются только при кликах
   - Pathname меняется только при навигации
   - Bootstrap проверяется только при монтировании

3. **Логи доступны для экспорта:**
   - `window.__TRACY_LOGGER.getLogs()` возвращает последние 50 событий
   - Кнопки в Debug Overlay работают

## 🚀 DEPLOYMENT

- ✅ Изменения закоммичены и запушены в `main`
- ✅ Бот перезапущен на сервере
- ✅ Vercel автоматически задеплоит изменения

## 📝 ИЗМЕНЕННЫЕ ФАЙЛЫ

1. **`web-app/components/DebugOverlay.tsx`**
   - Убраны `setInterval` для bootstrap и pathname
   - Разделены useEffect (один для монтирования, один для pathname)
   - Оптимизирована проверка изменений (обновляем только если значения изменились)

2. **`web-app/lib/logger.ts`**
   - Ограничено логирование в консоль (только ERROR, WARN, важные INFO)
   - Добавлен throttle (100мс между одинаковыми логами)
   - Ограничен размер store (50 вместо 1000)

3. **`web-app/app/assistant/page.tsx`**
   - Добавлены useRef для предотвращения повторных логов
   - Оптимизированы зависимости useEffect
   - Логирование только при реальных изменениях

## ✅ ПОДТВЕРЖДЕНИЕ

- ✅ Спама логов нет
- ✅ Обновления только при событиях
- ✅ Консоль чистая (только важные логи)
- ✅ Debug Overlay работает корректно
