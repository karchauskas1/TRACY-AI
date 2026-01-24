"""
==============================================================================
ACTION_EXECUTOR.PY - ВЫПОЛНЕНИЕ ДЕЙСТВИЙ НАД СОБЫТИЯМИ
==============================================================================

Выполняет действия:
- Удаление событий
- Изменение событий
- Создание событий (делегирует существующей логике)

==============================================================================
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from telegram import Bot
    from tracy.intelligence.intent_classifier import UserIntent, TargetEvent
    from tracy.intelligence.entity_resolver import ResolvedEntity

logger = logging.getLogger(__name__)


class ActionStatus(str, Enum):
    """Статус выполнения действия."""
    SUCCESS = "success"
    FAILED = "failed"
    NEEDS_CONFIRMATION = "needs_confirmation"
    NEEDS_SELECTION = "needs_selection"
    NOT_FOUND = "not_found"
    CANCELLED = "cancelled"


@dataclass
class ActionResult:
    """Результат выполнения действия."""
    status: ActionStatus
    message: str

    # Данные для ответа
    event: Optional[Dict[str, Any]] = None
    events: List[Dict[str, Any]] = field(default_factory=list)

    # Для inline keyboard
    keyboard_options: Optional[List[Dict[str, str]]] = None

    # Дополнительные данные
    data: Optional[Dict[str, Any]] = None


class ActionExecutor:
    """
    Выполняет действия над событиями.
    """

    def __init__(self, db, bot: 'Bot' = None, calendar_sync=None):
        """
        Args:
            db: Database instance
            bot: Telegram Bot (для отправки уведомлений)
            calendar_sync: CalendarSync для синхронизации с внешними календарями
        """
        self._db = db
        self._bot = bot
        self._calendar_sync = calendar_sync
        logger.info("ActionExecutor инициализирован")

    def set_bot(self, bot: 'Bot') -> None:
        """Установить Telegram Bot."""
        self._bot = bot

    async def execute_delete(
        self,
        user_id: int,
        resolved: 'ResolvedEntity',
        force: bool = False
    ) -> ActionResult:
        """
        Удалить событие.

        Args:
            user_id: ID пользователя
            resolved: Результат поиска события
            force: Удалить без подтверждения

        Returns:
            ActionResult
        """
        # Нет совпадений
        if resolved.no_matches:
            return ActionResult(
                status=ActionStatus.NOT_FOUND,
                message=self._format_not_found_message(resolved.search_query)
            )

        # Множественные совпадения - нужен выбор
        if resolved.multiple_matches:
            return ActionResult(
                status=ActionStatus.NEEDS_SELECTION,
                message="Найдено несколько событий. Выберите какое удалить:",
                events=resolved.events,
                keyboard_options=self._create_event_selection_keyboard(
                    resolved.events, action="delete"
                )
            )

        # Единственное совпадение
        event = resolved.event
        if not event:
            return ActionResult(
                status=ActionStatus.FAILED,
                message="Не удалось получить событие"
            )

        # Если требуется подтверждение
        if not force:
            return ActionResult(
                status=ActionStatus.NEEDS_CONFIRMATION,
                message=self._format_delete_confirmation(event),
                event=event,
                keyboard_options=[
                    {"text": "✅ Да, удалить", "callback_data": f"smart_delete_confirm_{event['id']}"},
                    {"text": "❌ Отмена", "callback_data": "smart_delete_cancel"}
                ]
            )

        # Удаляем событие
        try:
            event_id = event['id']
            title = event.get('title', 'Событие')

            # Удаляем из базы данных
            success = self._db.delete_event(event_id)

            if success:
                # Удаляем из внешнего календаря если есть
                if self._calendar_sync:
                    try:
                        await self._delete_from_calendar(user_id, event)
                    except Exception as e:
                        logger.warning(f"Не удалось удалить из внешнего календаря: {e}")

                logger.info(f"Событие удалено: {event_id} ({title})")

                return ActionResult(
                    status=ActionStatus.SUCCESS,
                    message=f"✅ Событие «{title}» удалено",
                    event=event
                )
            else:
                return ActionResult(
                    status=ActionStatus.FAILED,
                    message=f"❌ Не удалось удалить событие «{title}»"
                )

        except Exception as e:
            logger.error(f"Ошибка удаления события: {e}")
            return ActionResult(
                status=ActionStatus.FAILED,
                message=f"❌ Ошибка при удалении: {str(e)}"
            )

    async def execute_update(
        self,
        user_id: int,
        resolved: 'ResolvedEntity',
        target: 'TargetEvent',
        user_timezone: str = "Europe/Moscow"
    ) -> ActionResult:
        """
        Изменить событие.

        Args:
            user_id: ID пользователя
            resolved: Результат поиска события
            target: Данные для изменения
            user_timezone: Часовой пояс

        Returns:
            ActionResult
        """
        # Нет совпадений
        if resolved.no_matches:
            return ActionResult(
                status=ActionStatus.NOT_FOUND,
                message=self._format_not_found_message(resolved.search_query)
            )

        # Множественные совпадения
        if resolved.multiple_matches:
            return ActionResult(
                status=ActionStatus.NEEDS_SELECTION,
                message="Найдено несколько событий. Выберите какое изменить:",
                events=resolved.events,
                keyboard_options=self._create_event_selection_keyboard(
                    resolved.events, action="update"
                )
            )

        # Единственное совпадение
        event = resolved.event
        if not event:
            return ActionResult(
                status=ActionStatus.FAILED,
                message="Не удалось получить событие"
            )

        try:
            event_id = event['id']
            title = event.get('title', 'Событие')
            changes = []

            # Применяем изменения
            update_data = {}

            if target.new_title:
                update_data['title'] = target.new_title
                changes.append(f"название: {target.new_title}")

            if target.new_date or target.new_time:
                new_datetime = self._parse_new_datetime(
                    event, target.new_date, target.new_time, user_timezone
                )
                if new_datetime:
                    update_data['start_time'] = new_datetime.isoformat()
                    changes.append(f"время: {new_datetime.strftime('%d.%m.%Y %H:%M')}")

            if not update_data:
                return ActionResult(
                    status=ActionStatus.FAILED,
                    message="Не указано что изменить"
                )

            # Обновляем в базе данных
            success = self._db.update_event(event_id, **update_data)

            if success:
                logger.info(f"Событие обновлено: {event_id} ({title})")

                return ActionResult(
                    status=ActionStatus.SUCCESS,
                    message=f"✅ Событие «{title}» изменено:\n" + "\n".join(f"• {c}" for c in changes),
                    event=event,
                    data={"changes": changes}
                )
            else:
                return ActionResult(
                    status=ActionStatus.FAILED,
                    message=f"❌ Не удалось изменить событие «{title}»"
                )

        except Exception as e:
            logger.error(f"Ошибка изменения события: {e}")
            return ActionResult(
                status=ActionStatus.FAILED,
                message=f"❌ Ошибка при изменении: {str(e)}"
            )

    async def execute_query(
        self,
        user_id: int,
        resolved: 'ResolvedEntity'
    ) -> ActionResult:
        """
        Показать найденные события.

        Args:
            user_id: ID пользователя
            resolved: Результат поиска

        Returns:
            ActionResult
        """
        if resolved.no_matches:
            return ActionResult(
                status=ActionStatus.NOT_FOUND,
                message=self._format_query_not_found(resolved.search_query)
            )

        events = resolved.events
        message = self._format_events_list(events, resolved.search_query)

        return ActionResult(
            status=ActionStatus.SUCCESS,
            message=message,
            events=events
        )

    def _format_not_found_message(self, query: Optional[str]) -> str:
        """Форматировать сообщение когда событие не найдено."""
        if query:
            return f"❌ Событие «{query}» не найдено.\n\nВозможно, оно уже прошло или было удалено."
        return "❌ Событие не найдено."

    def _format_query_not_found(self, query: Optional[str]) -> str:
        """Форматировать сообщение для пустого результата поиска."""
        if query:
            return f"📭 По запросу «{query}» событий не найдено."
        return "📭 У вас пока нет предстоящих событий."

    def _format_delete_confirmation(self, event: Dict[str, Any]) -> str:
        """Форматировать запрос подтверждения удаления."""
        title = event.get('title', 'Событие')
        date_str = event.get('start_time', '')

        date_formatted = ""
        if date_str:
            try:
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                date_formatted = f"\n📅 {dt.strftime('%d.%m.%Y %H:%M')}"
            except:
                pass

        return f"🗑 Удалить событие «{title}»?{date_formatted}"

    def _format_events_list(
        self,
        events: List[Dict[str, Any]],
        query: Optional[str] = None
    ) -> str:
        """Форматировать список событий."""
        if not events:
            return "📭 Событий не найдено."

        lines = []

        if query:
            lines.append(f"🔍 Найдено по запросу «{query}»:\n")
        else:
            lines.append("📋 Ваши события:\n")

        for i, event in enumerate(events[:10], 1):
            title = event.get('title', 'Без названия')
            date_str = event.get('start_time', '')

            date_formatted = ""
            if date_str:
                try:
                    dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    date_formatted = dt.strftime('%d.%m %H:%M')
                except:
                    pass

            lines.append(f"{i}. {title} — {date_formatted}")

        if len(events) > 10:
            lines.append(f"\n... и ещё {len(events) - 10} событий")

        return "\n".join(lines)

    def _create_event_selection_keyboard(
        self,
        events: List[Dict[str, Any]],
        action: str = "delete"
    ) -> List[Dict[str, str]]:
        """Создать кнопки для выбора события."""
        options = []

        for event in events[:5]:  # Максимум 5 кнопок
            title = event.get('title', 'Событие')[:20]
            event_id = event.get('id')
            date_str = event.get('start_time', '')

            date_short = ""
            if date_str:
                try:
                    dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    date_short = f" ({dt.strftime('%d.%m')})"
                except:
                    pass

            options.append({
                "text": f"{title}{date_short}",
                "callback_data": f"smart_{action}_{event_id}"
            })

        options.append({
            "text": "❌ Отмена",
            "callback_data": f"smart_{action}_cancel"
        })

        return options

    def _parse_new_datetime(
        self,
        event: Dict[str, Any],
        new_date: Optional[str],
        new_time: Optional[str],
        timezone: str
    ) -> Optional[datetime]:
        """Парсить новую дату/время для события."""
        import dateparser
        import pytz

        try:
            tz = pytz.timezone(timezone)
            now = datetime.now(tz)

            # Базовая дата/время из существующего события
            current_dt = None
            if event.get('start_time'):
                try:
                    current_dt = datetime.fromisoformat(
                        event['start_time'].replace('Z', '+00:00')
                    ).astimezone(tz)
                except:
                    current_dt = now

            if not current_dt:
                current_dt = now

            # Парсим новую дату
            if new_date:
                parsed_date = dateparser.parse(
                    new_date,
                    settings={
                        'TIMEZONE': timezone,
                        'RETURN_AS_TIMEZONE_AWARE': True,
                        'RELATIVE_BASE': now,
                        'PREFER_DATES_FROM': 'future'
                    }
                )
                if parsed_date:
                    current_dt = current_dt.replace(
                        year=parsed_date.year,
                        month=parsed_date.month,
                        day=parsed_date.day
                    )

            # Парсим новое время
            if new_time:
                parsed_time = dateparser.parse(
                    new_time,
                    settings={
                        'TIMEZONE': timezone,
                        'RETURN_AS_TIMEZONE_AWARE': True
                    }
                )
                if parsed_time:
                    current_dt = current_dt.replace(
                        hour=parsed_time.hour,
                        minute=parsed_time.minute,
                        second=0,
                        microsecond=0
                    )

            return current_dt

        except Exception as e:
            logger.error(f"Ошибка парсинга даты/времени: {e}")
            return None

    async def _delete_from_calendar(
        self,
        user_id: int,
        event: Dict[str, Any]
    ) -> None:
        """Удалить событие из внешнего календаря."""
        if not self._calendar_sync:
            return

        calendar_event_id = event.get('calendar_event_id')
        if not calendar_event_id:
            return

        try:
            # Получаем информацию о подключении к календарю
            calendar_connection = self._db.get_calendar_connection(user_id)
            if not calendar_connection:
                return

            provider = calendar_connection.get('provider')
            if provider == 'google':
                # Удаляем из Google Calendar
                from calendar_google import GoogleCalendarSync
                google_sync = GoogleCalendarSync(self._db)
                await google_sync.delete_event(user_id, calendar_event_id)

        except Exception as e:
            logger.warning(f"Ошибка удаления из внешнего календаря: {e}")
