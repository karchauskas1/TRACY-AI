# Резюме исправлений "Failed to fetch" и бесконечной загрузки

## Первопричина проблем

Основные проблемы были связаны с:
1. **Race condition** - компоненты пытались делать запросы до получения `user_id` из Telegram WebApp
2. **Hardcoded API URLs** - разные компоненты использовали разные URL, что усложняло поддержку
3. **Отсутствие таймаутов** - запросы могли висеть бесконечно
4. **Неточные сообщения об ошибках** - показывалось просто "Load failed" без деталей
5. **CORS** - настройки CORS на сервере были недостаточно гибкими

## Реализованные исправления

### 1. Единый API клиент (`web-app/lib/apiClient.ts`)
- ✅ Все запросы идут через единый `apiClient`
- ✅ Base URL берется из `NEXT_PUBLIC_API_URL` (env переменная)
- ✅ Защита от пустого env - показывается понятная ошибка
- ✅ Таймауты через `AbortController` (15 секунд по умолчанию)
- ✅ Детальная обработка ошибок (CORS, TIMEOUT, NETWORK, HTTP, JSON)
- ✅ Автоматическое логирование в debug систему

### 2. Хук для получения user_id (`web-app/lib/useTelegramUser.ts`)
- ✅ Устраняет race condition
- ✅ Гарантирует получение `user_id` перед использованием
- ✅ Fallback на localStorage
- ✅ Обработка ошибок

### 3. Debug система (`web-app/lib/apiDebug.ts` + `web-app/app/debug/page.tsx`)
- ✅ Логирование всех сетевых запросов
- ✅ Статистика (успешные, ошибки, таймауты, CORS)
- ✅ Страница `/debug` для мониторинга (доступна супер-пользователям)
- ✅ Показывает URL, статус, время выполнения, тип ошибки

### 4. Улучшенные сообщения об ошибках
- ✅ Вместо "Load failed" показывается конкретная причина:
  - "CORS ошибка: сервер не разрешает запросы с этого домена"
  - "Таймаут запроса: Сервер не отвечает. Попробуйте позже."
  - "Сетевая ошибка: Не удалось подключиться к серверу"
  - "HTTP 404: События не найдены"
- ✅ Кнопка "Попробовать снова" для retry

### 5. CORS на сервере (`http_server.py`)
- ✅ Правильная обработка OPTIONS (preflight) запросов
- ✅ Поддержка GitHub Pages origin (`https://karchauskas1.github.io` и подпути)
- ✅ CORS заголовки на всех ответах (включая ошибки)
- ✅ Логирование CORS запросов

## Измененные файлы

### Новые файлы:
- `web-app/lib/apiClient.ts` - единый API клиент
- `web-app/lib/useTelegramUser.ts` - хук для получения user_id
- `web-app/lib/apiDebug.ts` - система отладки
- `web-app/components/ApiDebugInit.tsx` - инициализация debug системы
- `web-app/app/debug/page.tsx` - страница отладки
- `web-app/.env.example` - пример переменных окружения

### Обновленные файлы:
- `web-app/app/calendar/CalendarPageClient.tsx` - использует apiClient и useTelegramUser
- `web-app/app/layout.tsx` - инициализация debug системы
- `web-app/app/assistant/page.tsx` - добавлена ссылка на debug страницу
- `http_server.py` - улучшены CORS настройки и логирование

## Что нужно сделать дальше

### Обновить остальные компоненты:
1. `web-app/app/todo-lists/page.tsx` - заменить hardcoded URLs на apiClient
2. `web-app/app/chat/page.tsx` - заменить hardcoded URLs на apiClient
3. `web-app/app/settings/feedback/FeedbackPageClient.tsx` - заменить hardcoded URLs на apiClient
4. Все компоненты должны использовать `useTelegramUser()` вместо собственной логики

### Настройка переменных окружения:

#### Для GitHub Pages (GitHub Actions):
1. Перейти в Settings → Secrets and variables → Actions
2. Добавить `NEXT_PUBLIC_API_URL` = `https://api.pasekaproduction.ru`

#### Для локальной разработки:
Создать файл `web-app/.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8080
```

## Проверка

После деплоя проверить:
1. ✅ Открыть приложение в обычном браузере (Safari/Chrome)
2. ✅ Открыть приложение в Telegram Mini App (iOS)
3. ✅ Проверить страницу `/debug` (для супер-пользователей)
4. ✅ Убедиться, что ошибки показывают конкретную причину
5. ✅ Проверить, что нет бесконечной загрузки

## Тестирование

1. **Тест таймаута**: Отключить интернет → должно показать "Сетевая ошибка"
2. **Тест CORS**: Проверить в Network tab, что preflight OPTIONS возвращает 204
3. **Тест user_id**: Открыть приложение не через Telegram → должно показать ошибку авторизации
4. **Тест debug**: Открыть `/debug` → должны быть видны все запросы

