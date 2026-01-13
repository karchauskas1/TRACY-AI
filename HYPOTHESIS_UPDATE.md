# 🔍 Обновленные гипотезы на основе анализа кода

## Найденная проблема:

В коде есть несколько мест, где сохраняется пользователь в localStorage:
- `web-app/app/page.tsx` - сохраняет при первом открытии
- `web-app/app/login/page.tsx` - сохраняет при логине
- `web-app/app/calendar/page.tsx` - сохраняет при открытии календаря
- `web-app/app/assistant/page.tsx` - сохраняет при открытии главной страницы

## Новая гипотеза H: Проблема с порядком загрузки компонентов

**Гипотеза H**: Компоненты (CalendarPageClient, TodoListsPage, ChatPage) пытаются получить user_id ДО того, как родительский компонент (page.tsx) сохранил его в localStorage.

**Доказательства**:
- CalendarPageClient загружается сразу при монтировании
- useEffect в CalendarPageClient может выполниться раньше, чем useEffect в page.tsx
- Если Telegram WebApp не предоставляет initDataUnsafe сразу, user_id не будет найден

## Решение:

Нужно убедиться, что:
1. user_id сохраняется в localStorage ПЕРЕД загрузкой данных
2. Компоненты ждут, пока user_id будет доступен
3. Добавить проверку и ожидание user_id перед API запросами
