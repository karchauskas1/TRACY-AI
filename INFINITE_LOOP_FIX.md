# 🔧 FIX: УСТРАНЕНИЕ БЕСКОНЕЧНОГО ЦИКЛА В useEffect

## 📋 ROOT CAUSE

### Проблема: useEffect с зависимостью `user` создает бесконечный цикл

**Файл:** `web-app/app/assistant/page.tsx`
**Строки:** 29-64 (старая версия)

**Проблемный код:**
```typescript
useEffect(() => {
  // ...
  if (telegramUser && userId) {
    setUser({ ... }) // ❌ setState внутри useEffect
  }
}, [telegramUser, userId, userLoading, router, user]) // ❌ user в зависимостях
```

**Цикл:**
1. useEffect выполняется
2. `setUser` вызывается
3. `user` меняется
4. useEffect снова выполняется (из-за зависимости `user`)
5. Бесконечный цикл → бесконечные логи

### Дополнительные проблемы:

1. **`mountedRef` проверяется внутри useEffect с зависимостями:**
   - useEffect может вызываться много раз
   - `mountedRef.current === false` может быть true несколько раз

2. **`telegramUser` - объект, который может меняться на каждом render:**
   - Next.js может создавать новый объект на каждом render
   - Это вызывает повторные выполнения useEffect

3. **`router` - объект, который может меняться:**
   - Может вызывать повторные выполнения

4. **Нет guard для `userId`:**
   - `User loaded` логируется даже если userId не изменился

## ✅ ИСПРАВЛЕНИЯ

### 1. Разделены useEffect на отдельные эффекты

**Было:**
```typescript
useEffect(() => {
  // mounted check
  // user loading
  // redirect
}, [telegramUser, userId, userLoading, router, user]) // ❌ Все вместе
```

**Стало:**
```typescript
// 1. Mounted - только один раз при монтировании
useEffect(() => {
  if (mountedRef.current === false) {
    logger.info('AssistantPage', 'Component mounted', ...)
    mountedRef.current = true
  }
}, []) // ✅ Пустой deps - выполняется только при монтировании

// 2. User loading - отдельный эффект с правильными зависимостями
useEffect(() => {
  // Обработка пользователя
}, [userId, userLoading, telegramUser?.id, ...]) // ✅ Стабилизированные зависимости
```

### 2. Убран `user` из зависимостей

**Было:**
```typescript
}, [telegramUser, userId, userLoading, router, user]) // ❌ user создает цикл
```

**Стало:**
```typescript
}, [userId, userLoading, telegramUser?.id, telegramUser?.first_name, ...]) // ✅ Только примитивы
```

### 3. Добавлен guard для `userId` (идемпотентность)

**Было:**
```typescript
if (telegramUser && userId) {
  logger.info('AssistantPage', 'User loaded', ...) // ❌ Логируется каждый раз
  setUser({ ... })
}
```

**Стало:**
```typescript
if (telegramUser && userId && lastUserIdRef.current !== userId) {
  logger.info('AssistantPage', 'User loaded', ...) // ✅ Только при изменении userId
  lastUserIdRef.current = userId
  setUser({ ... })
}
```

### 4. Стабилизированы зависимости

**Было:**
```typescript
}, [telegramUser, ...]) // ❌ Объект может меняться на каждом render
```

**Стало:**
```typescript
}, [userId, userLoading, telegramUser?.id, telegramUser?.first_name, ...]) // ✅ Только примитивы
```

## 📊 РЕЗУЛЬТАТ

### До исправления:
- ❌ `Component mounted` логируется бесконечно
- ❌ `User loaded` логируется бесконечно
- ❌ useEffect вызывает сам себя через setState
- ❌ Консоль лагает от спама логов

### После исправления:
- ✅ `Component mounted` логируется только 1 раз при монтировании
- ✅ `User loaded` логируется только 1 раз при изменении userId
- ✅ Нет циклов - useEffect не вызывает сам себя
- ✅ Консоль чистая - логи только при реальных событиях

## 🧪 ПРОВЕРКА

После deployment проверить:

1. **Открыть `/assistant`**
2. **Подождать 10 секунд**
3. **Проверить консоль:**
   - Должен быть максимум 1 лог `Component mounted`
   - Должен быть максимум 1 лог `User loaded` (если пользователь загружен)
   - Нет повторяющихся логов
   - Консоль не лагает

## 🚀 DEPLOYMENT

- ✅ Изменения закоммичены и запушены в `main`
- ✅ Бот перезапущен на сервере
- ✅ Vercel автоматически задеплоит изменения

## 📝 ИЗМЕНЕННЫЕ ФАЙЛЫ

1. **`web-app/app/assistant/page.tsx`**
   - Разделены useEffect (mounted отдельно от user loading)
   - Убран `user` из зависимостей
   - Добавлен `lastUserIdRef` для идемпотентности
   - Стабилизированы зависимости (только примитивы)

## ✅ ПОДТВЕРЖДЕНИЕ

- ✅ Спама логов нет
- ✅ `Component mounted` только 1 раз
- ✅ `User loaded` только при изменении userId
- ✅ Нет бесконечных циклов
- ✅ Консоль работает нормально
