# Обновление веб-приложения для использования HTTPS домена

## ✅ SSL установлен успешно!

- **Домен**: `api.pasekaproduction.ru`
- **HTTPS**: ✅ Работает
- **HTTP → HTTPS редирект**: ✅ Настроен автоматически
- **Сертификат действителен до**: 2026-04-12 (89 дней)
- **Автоматическое обновление**: ✅ Настроено

## 📋 Что нужно обновить

Старый API URL: `http://5.35.126.42:8080`  
Новый API URL: `https://api.pasekaproduction.ru/api/`

## 📄 Файлы для обновления

Нужно обновить следующие файлы в `web-app/app/`:

1. `app/calendar/CalendarPageClient.tsx`
2. `app/chat/page.tsx`
3. `app/todo-lists/page.tsx`
4. `app/todo-lists/TodoListDetailClient.tsx`
5. `app/settings/feedback/FeedbackPageClient.tsx`
6. `app/meetings/history/page.tsx`
7. `app/calendar/list/page.tsx`

## 🔧 Изменения

Заменить:
```typescript
let apiBaseUrl = "http://5.35.126.42:8080"
if (typeof window !== "undefined" && window.location.hostname === "localhost") {
  apiBaseUrl = "http://localhost:8080"
}
```

На:
```typescript
let apiBaseUrl = "https://api.pasekaproduction.ru"
if (typeof window !== "undefined" && window.location.hostname === "localhost") {
  apiBaseUrl = "http://localhost:8080"
}
```

И обновить пути API с `/api/...` на `/api/...` (остается без изменений, так как `/api/` добавляется автоматически в nginx).

## 🎯 После обновления

1. Веб-приложение будет использовать HTTPS
2. Mixed Content Policy проблема будет решена
3. API будет доступен по безопасному соединению
