"""
==============================================================================
TOOLS.PY - ИНСТРУМЕНТЫ АГЕНТА
==============================================================================

Набор функций которые агент может вызывать для выполнения действий.
LLM сам решает какие инструменты использовать на основе запроса пользователя.

Каждый инструмент:
- Имеет описание для LLM (что делает, когда использовать)
- Имеет параметры с описаниями
- Возвращает результат который LLM использует для формирования ответа

==============================================================================
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Callable, Awaitable
from enum import Enum
import json
import pytz
import dateparser

logger = logging.getLogger(__name__)


# =============================================================================
# Tool Definitions (JSON Schema для OpenAI function calling)
# =============================================================================

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "search_events",
            "description": """Поиск событий пользователя. Используй когда:
- Пользователь спрашивает о своих событиях ("что у меня завтра?", "какие планы на неделю?")
- Нужно найти конкретное событие по названию ("когда встреча с Катей?")
- Нужно проверить есть ли свободное время
- Перед удалением/изменением события - сначала найди его""",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Поисковый запрос по названию события (например 'встреча с Катей', 'обед', 'тренировка'). Оставь пустым для получения всех событий."
                    },
                    "date_from": {
                        "type": "string",
                        "description": "Начало периода поиска. Относительная дата ('сегодня', 'завтра', 'понедельник') или абсолютная (2025-01-27)"
                    },
                    "date_to": {
                        "type": "string",
                        "description": "Конец периода поиска. Относительная или абсолютная дата."
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Максимальное количество событий (по умолчанию 10)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_event",
            "description": """Создать новое событие в календаре. Используй когда:
- Пользователь хочет добавить событие ("встреча завтра в 15:00", "обучение в понедельник с 16 до 20")
- Пользователь упоминает дату/время + что-то что нужно сделать
- Даже если формулировка неявная ("позвонить маме в 18:00" = событие)""",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Название события. Извлеки из сообщения пользователя суть."
                    },
                    "date": {
                        "type": "string",
                        "description": "Дата события. Относительная ('завтра', 'понедельник', 'через 2 дня') или абсолютная (2025-01-27)"
                    },
                    "start_time": {
                        "type": "string",
                        "description": "Время начала в формате HH:MM (например '15:00', '09:30')"
                    },
                    "end_time": {
                        "type": "string",
                        "description": "Время окончания в формате HH:MM. Если не указано - не передавай."
                    },
                    "description": {
                        "type": "string",
                        "description": "Описание события (опционально)"
                    },
                    "reminder_minutes": {
                        "type": "integer",
                        "description": "За сколько минут напомнить (по умолчанию 15)"
                    }
                },
                "required": ["title", "date", "start_time"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_event",
            "description": """Удалить событие. Используй когда:
- Пользователь явно просит удалить ("удали", "отмени", "убери")
- Пользователь отвечает на сообщение о событии словом "удали"
- Пользователь говорит "удали встречу с Катей" - сначала найди событие через search_events!

ВАЖНО: Если event_id неизвестен, сначала используй search_events чтобы найти событие.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "event_id": {
                        "type": "integer",
                        "description": "ID события для удаления. Получи через search_events или из контекста reply."
                    },
                    "confirm": {
                        "type": "boolean",
                        "description": "Подтверждение удаления. Если false - спроси подтверждение у пользователя."
                    }
                },
                "required": ["event_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_event",
            "description": """Изменить существующее событие. Используй когда:
- Пользователь хочет перенести событие ("перенеси на 16:00", "сдвинь на завтра")
- Пользователь хочет изменить название
- Пользователь отвечает на сообщение о событии с новым временем

ВАЖНО: Если event_id неизвестен, сначала используй search_events чтобы найти событие.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "event_id": {
                        "type": "integer",
                        "description": "ID события для изменения"
                    },
                    "new_title": {
                        "type": "string",
                        "description": "Новое название (если меняется)"
                    },
                    "new_date": {
                        "type": "string",
                        "description": "Новая дата (относительная или абсолютная)"
                    },
                    "new_start_time": {
                        "type": "string",
                        "description": "Новое время начала HH:MM"
                    },
                    "new_end_time": {
                        "type": "string",
                        "description": "Новое время окончания HH:MM"
                    }
                },
                "required": ["event_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ask_user",
            "description": """Задать уточняющий вопрос пользователю. Используй когда:
- Не хватает информации для выполнения действия
- Найдено несколько событий и нужно уточнить какое
- Нужно подтверждение перед важным действием (удаление)
- Запрос неоднозначен

Примеры:
- "Какое событие удалить - встречу в 15:00 или обед в 13:00?"
- "На какое время перенести?"
- "Уточни дату - какой именно понедельник?"
- "Удалить событие 'Обед с клиентом' на завтра в 13:00?"
""",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "Вопрос для пользователя"
                    },
                    "options": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Варианты ответа (опционально). Если есть - покажи как кнопки."
                    },
                    "context": {
                        "type": "string",
                        "description": "Контекст вопроса для сохранения (что делаем после ответа)"
                    }
                },
                "required": ["question"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_response",
            "description": """Отправить финальный ответ пользователю. Используй когда:
- Действие выполнено успешно и нужно сообщить результат
- Нужно ответить на вопрос пользователя
- Произошла ошибка и нужно объяснить

Это терминальное действие - после него диалог завершается.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Текст ответа пользователю. Будь дружелюбным но лаконичным."
                    },
                    "show_events": {
                        "type": "boolean",
                        "description": "Показать список событий в красивом формате"
                    }
                },
                "required": ["message"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_datetime",
            "description": """Получить текущую дату и время в часовом поясе пользователя.
Используй когда нужно понять:
- Какой сегодня день недели
- Какой ближайший понедельник/вторник/etc
- Текущее время для планирования""",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]


# =============================================================================
# Tool Executor - выполнение инструментов
# =============================================================================

class ToolExecutor:
    """
    Выполняет инструменты агента.
    Каждый метод соответствует одному tool из TOOLS_SCHEMA.
    """

    def __init__(self, db, user_timezone: str = "Europe/Moscow"):
        self._db = db
        self._timezone = user_timezone
        self._tz = pytz.timezone(user_timezone)
        self._pending_events: List[Dict] = []  # События для показа
        logger.info("ToolExecutor инициализирован")

    def set_timezone(self, timezone: str):
        """Установить часовой пояс пользователя."""
        self._timezone = timezone
        self._tz = pytz.timezone(timezone)

    async def execute(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        user_id: int
    ) -> Dict[str, Any]:
        """
        Выполнить инструмент.

        Args:
            tool_name: Название инструмента
            arguments: Аргументы
            user_id: ID пользователя

        Returns:
            Результат выполнения
        """
        logger.info(f"Executing tool: {tool_name} with args: {arguments}")

        handlers = {
            "search_events": self._search_events,
            "create_event": self._create_event,
            "delete_event": self._delete_event,
            "update_event": self._update_event,
            "ask_user": self._ask_user,
            "send_response": self._send_response,
            "get_current_datetime": self._get_current_datetime,
        }

        handler = handlers.get(tool_name)
        if not handler:
            return {"error": f"Unknown tool: {tool_name}"}

        try:
            result = await handler(user_id=user_id, **arguments)
            logger.info(f"Tool {tool_name} result: {result}")
            return result
        except Exception as e:
            logger.error(f"Tool {tool_name} error: {e}", exc_info=True)
            return {"error": str(e)}

    async def _search_events(
        self,
        user_id: int,
        query: str = None,
        date_from: str = None,
        date_to: str = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Поиск событий."""
        now = datetime.now(self._tz)

        # Парсим даты
        start_date = None
        end_date = None

        if date_from:
            parsed = dateparser.parse(
                date_from,
                settings={
                    'TIMEZONE': self._timezone,
                    'RETURN_AS_TIMEZONE_AWARE': True,
                    'RELATIVE_BASE': now,
                    'PREFER_DATES_FROM': 'future'
                }
            )
            if parsed:
                start_date = parsed.replace(hour=0, minute=0, second=0)

        if date_to:
            parsed = dateparser.parse(
                date_to,
                settings={
                    'TIMEZONE': self._timezone,
                    'RETURN_AS_TIMEZONE_AWARE': True,
                    'RELATIVE_BASE': now,
                    'PREFER_DATES_FROM': 'future'
                }
            )
            if parsed:
                end_date = parsed.replace(hour=23, minute=59, second=59)

        # Получаем события
        days = 90
        if end_date:
            days = max(90, (end_date - now).days + 7)

        events = self._db.get_upcoming_events(user_id, days=days)

        if not events:
            return {
                "found": False,
                "count": 0,
                "events": [],
                "message": "Событий не найдено"
            }

        # Фильтруем по дате
        if start_date or end_date:
            filtered = []
            for event in events:
                event_dt = self._parse_event_datetime(event)
                if event_dt:
                    if start_date and event_dt < start_date:
                        continue
                    if end_date and event_dt > end_date:
                        continue
                    filtered.append(event)
            events = filtered

        # Фильтруем по запросу
        if query:
            query_lower = query.lower()
            events = [
                e for e in events
                if query_lower in (e.get('title') or '').lower()
                or query_lower in (e.get('description') or '').lower()
            ]

        # Форматируем для ответа
        formatted_events = []
        for event in events[:limit]:
            formatted_events.append(self._format_event(event))

        self._pending_events = formatted_events

        return {
            "found": bool(formatted_events),
            "count": len(formatted_events),
            "events": formatted_events,
            "message": f"Найдено {len(formatted_events)} событий" if formatted_events else "Событий не найдено"
        }

    async def _create_event(
        self,
        user_id: int,
        title: str,
        date: str,
        start_time: str,
        end_time: str = None,
        description: str = None,
        reminder_minutes: int = 15
    ) -> Dict[str, Any]:
        """Создать событие."""
        now = datetime.now(self._tz)

        # Парсим дату
        parsed_date = dateparser.parse(
            date,
            settings={
                'TIMEZONE': self._timezone,
                'RETURN_AS_TIMEZONE_AWARE': True,
                'RELATIVE_BASE': now,
                'PREFER_DATES_FROM': 'future'
            }
        )

        if not parsed_date:
            return {"success": False, "error": f"Не удалось распознать дату: {date}"}

        # 🔴 ЖЁСТКИЙ ЗАПРЕТ: Никогда не создаём события в прошлом!
        if parsed_date < now:
            # Проверяем это день недели?
            weekdays = ['понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота', 'воскресенье',
                       'пн', 'вт', 'ср', 'чт', 'пт', 'сб', 'вс', 'monday', 'tuesday', 'wednesday',
                       'thursday', 'friday', 'saturday', 'sunday']
            is_weekday = any(wd in date.lower() for wd in weekdays)

            if is_weekday:
                # День недели в прошлом → сдвигаем на неделю вперёд
                parsed_date = parsed_date + timedelta(days=7)
                logger.info(f"⏰ День недели '{date}' был в прошлом, переносим на +7 дней: {parsed_date}")
            else:
                # Просто дата в прошлом → на следующий день
                parsed_date = parsed_date + timedelta(days=1)
                logger.info(f"⏰ Дата '{date}' в прошлом, переносим на завтра: {parsed_date}")

        # Парсим время начала
        try:
            hour, minute = map(int, start_time.split(':'))
            event_start = parsed_date.replace(hour=hour, minute=minute, second=0, microsecond=0)

            # 🔴 Финальная проверка: если время уже прошло сегодня - на завтра
            if event_start < now:
                event_start = event_start + timedelta(days=1)
                logger.info(f"⏰ Время '{start_time}' уже прошло, переносим на завтра: {event_start}")
        except:
            return {"success": False, "error": f"Неверный формат времени: {start_time}"}

        # Парсим время окончания
        event_end = None
        if end_time:
            try:
                hour, minute = map(int, end_time.split(':'))
                event_end = parsed_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
            except:
                pass

        # 🔴 По умолчанию событие длится 1 час если end_time не указан
        if not event_end:
            event_end = event_start + timedelta(hours=1)
            logger.info(f"⏰ end_time не указан, устанавливаем +1 час: {event_end}")

        # Создаём событие
        event_id = self._db.save_event(
            user_id=user_id,
            title=title,
            description=description,
            start_time=event_start,
            end_time=event_end,
            status='confirmed'
        )

        if event_id:
            # Форматируем дату для ответа
            weekday = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]
            day_name = weekday[event_start.weekday()]

            time_str = f"{event_start.strftime('%H:%M')} - {event_end.strftime('%H:%M')}"

            return {
                "success": True,
                "event_id": event_id,
                "title": title,
                "date": event_start.strftime('%d.%m.%Y'),
                "day_name": day_name,
                "time": time_str,
                "message": f"Событие '{title}' создано на {day_name}, {event_start.strftime('%d.%m')} в {time_str}"
            }
        else:
            return {"success": False, "error": "Не удалось создать событие"}

    async def _delete_event(
        self,
        user_id: int,
        event_id: int,
        confirm: bool = False
    ) -> Dict[str, Any]:
        """Удалить событие."""
        # Получаем событие
        event = self._db.get_event(event_id)

        if not event:
            return {"success": False, "error": "Событие не найдено"}

        if event.get('user_id') != user_id:
            return {"success": False, "error": "Это не ваше событие"}

        title = event.get('title', 'Событие')

        if not confirm:
            # Нужно подтверждение
            return {
                "success": False,
                "needs_confirmation": True,
                "event_id": event_id,
                "title": title,
                "message": f"Удалить событие '{title}'?"
            }

        # Удаляем
        success = self._db.delete_event(event_id)

        if success:
            return {
                "success": True,
                "event_id": event_id,
                "title": title,
                "message": f"Событие '{title}' удалено"
            }
        else:
            return {"success": False, "error": "Не удалось удалить событие"}

    async def _update_event(
        self,
        user_id: int,
        event_id: int,
        new_title: str = None,
        new_date: str = None,
        new_start_time: str = None,
        new_end_time: str = None
    ) -> Dict[str, Any]:
        """Изменить событие."""
        # Получаем событие
        event = self._db.get_event(event_id)

        if not event:
            return {"success": False, "error": "Событие не найдено"}

        if event.get('user_id') != user_id:
            return {"success": False, "error": "Это не ваше событие"}

        now = datetime.now(self._tz)
        updates = {}
        changes = []

        # Новое название
        if new_title:
            updates['title'] = new_title
            changes.append(f"название: {new_title}")

        # Новая дата/время
        if new_date or new_start_time:
            current_dt = self._parse_event_datetime(event) or now

            if new_date:
                parsed = dateparser.parse(
                    new_date,
                    settings={
                        'TIMEZONE': self._timezone,
                        'RETURN_AS_TIMEZONE_AWARE': True,
                        'RELATIVE_BASE': now,
                        'PREFER_DATES_FROM': 'future'
                    }
                )
                if parsed:
                    current_dt = current_dt.replace(
                        year=parsed.year,
                        month=parsed.month,
                        day=parsed.day
                    )
                    changes.append(f"дата: {parsed.strftime('%d.%m.%Y')}")

            if new_start_time:
                try:
                    hour, minute = map(int, new_start_time.split(':'))
                    current_dt = current_dt.replace(hour=hour, minute=minute)
                    changes.append(f"время: {new_start_time}")
                except:
                    pass

            updates['start_time'] = current_dt.isoformat()

        if new_end_time:
            # Парсим время окончания относительно start_time
            if 'start_time' in updates:
                base_dt = datetime.fromisoformat(updates['start_time'])
            else:
                base_dt = self._parse_event_datetime(event) or now

            try:
                hour, minute = map(int, new_end_time.split(':'))
                end_dt = base_dt.replace(hour=hour, minute=minute)
                updates['end_time'] = end_dt.isoformat()
                changes.append(f"окончание: {new_end_time}")
            except:
                pass

        if not updates:
            return {"success": False, "error": "Не указано что изменить"}

        # Обновляем
        success = self._db.update_event(event_id, **updates)

        if success:
            return {
                "success": True,
                "event_id": event_id,
                "changes": changes,
                "message": f"Событие изменено: " + ", ".join(changes)
            }
        else:
            return {"success": False, "error": "Не удалось изменить событие"}

    async def _ask_user(
        self,
        user_id: int,
        question: str,
        options: List[str] = None,
        context: str = None
    ) -> Dict[str, Any]:
        """Задать вопрос пользователю."""
        return {
            "type": "question",
            "question": question,
            "options": options,
            "context": context,
            "waiting_for_response": True
        }

    async def _send_response(
        self,
        user_id: int,
        message: str,
        show_events: bool = False
    ) -> Dict[str, Any]:
        """Отправить ответ пользователю."""
        result = {
            "type": "response",
            "message": message,
            "final": True
        }

        if show_events and self._pending_events:
            result["events"] = self._pending_events

        return result

    async def _get_current_datetime(self, user_id: int) -> Dict[str, Any]:
        """Получить текущую дату/время."""
        now = datetime.now(self._tz)
        weekday = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]

        return {
            "date": now.strftime('%Y-%m-%d'),
            "time": now.strftime('%H:%M'),
            "day_of_week": weekday[now.weekday()],
            "day_of_week_num": now.weekday(),
            "formatted": f"{weekday[now.weekday()]}, {now.strftime('%d.%m.%Y %H:%M')}",
            "timezone": self._timezone
        }

    def _parse_event_datetime(self, event: Dict) -> Optional[datetime]:
        """Парсить datetime события."""
        date_str = event.get('start_time', '')
        if not date_str:
            return None

        try:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.astimezone(self._tz)
        except:
            return None

    def _format_event(self, event: Dict) -> Dict[str, Any]:
        """Форматировать событие для ответа."""
        dt = self._parse_event_datetime(event)
        weekday = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]

        formatted = {
            "id": event.get('id'),
            "title": event.get('title', 'Без названия'),
            "description": event.get('description'),
        }

        if dt:
            formatted["date"] = dt.strftime('%d.%m.%Y')
            formatted["time"] = dt.strftime('%H:%M')
            formatted["day_name"] = weekday[dt.weekday()]
            formatted["formatted"] = f"{dt.strftime('%d.%m')} ({weekday[dt.weekday()]}) {dt.strftime('%H:%M')}"

        # Время окончания
        end_str = event.get('end_time', '')
        if end_str:
            try:
                end_dt = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
                formatted["end_time"] = end_dt.astimezone(self._tz).strftime('%H:%M')
            except:
                pass

        return formatted
