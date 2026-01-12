# Исправление ошибки с параметром use_apps_script

## Проблема
Ошибка: `FeedbackService.submit_feedback() got an unexpected keyword argument 'use_apps_script'`

## Причина
На сервере была старая версия файла `feedback_service.py` без параметра `use_apps_script`.

## Решение
1. ✅ Обновлен `feedback_service.py` на сервере
2. ✅ Бот перезапущен
3. ✅ Параметр `use_apps_script` теперь присутствует в методе `submit_feedback`

## Проверка
После обновления метод `submit_feedback` имеет следующие параметры:
- `feedback_type: str`
- `comment: str`
- `screenshot_url: Optional[str] = None`
- `use_apps_script: bool = False` ✅

## Статус
✅ Исправлено - обратная связь должна работать корректно.

