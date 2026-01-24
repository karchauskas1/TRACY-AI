"""
==============================================================================
ENUMS.PY - ПЕРЕЧИСЛЕНИЯ ДЛЯ ТИПОБЕЗОПАСНОСТИ
==============================================================================

Все типы данных, которые раньше были magic strings, теперь являются Enum.
Это обеспечивает:
- Автодополнение в IDE
- Проверку типов
- Защиту от опечаток
- Единый источник правды для всех значений

==============================================================================
"""
from enum import Enum
from typing import Optional


class Intent(str, Enum):
    """
    Типы намерений пользователя, извлекаемые NLP.

    Использование:
        intent = Intent.EVENT
        intent = Intent.from_string("event")
    """

    # Операции с событиями
    EVENT = "event"                     # Создание события
    UPDATE = "update"                   # Обновление события
    UPDATE_MANY = "update_many"         # Обновление нескольких событий
    DELETE = "delete"                   # Удаление события
    DELETE_ALL = "delete_all"           # Удаление всех событий
    DELETE_BY_PERIOD = "delete_by_period"  # Удаление за период
    DELETE_MANY = "delete_many"         # Удаление нескольких событий
    DELETE_BY_PATTERN = "delete_by_pattern"  # Удаление по паттерну
    CREATE_MANY = "create_many"         # Создание нескольких событий

    # Напоминания
    REMINDER = "reminder"               # Создание напоминания
    ADD_REMINDER = "add_reminder"       # Добавление напоминания к событию

    # Заметки
    NOTE = "note"                       # Создание заметки
    ADD_NOTE = "add_note"               # Добавление заметки
    LIST_NOTES = "list_notes"           # Список заметок
    DELETE_NOTE = "delete_note"         # Удаление заметки

    # Запросы
    LIST_EVENTS = "list_events"         # Список событий
    SEARCH = "search"                   # Поиск

    # Разговорные
    SMALL_TALK = "small_talk"           # Светская беседа
    QUESTION = "question"               # Вопрос
    GREETING = "greeting"               # Приветствие
    THANKS = "thanks"                   # Благодарность

    # Специальные
    UNKNOWN = "unknown"                 # Не распознано
    ERROR = "error"                     # Ошибка

    @classmethod
    def from_string(cls, value: str) -> 'Intent':
        """
        Безопасное преобразование строки в Intent.

        Args:
            value: строковое значение intent

        Returns:
            Intent enum или Intent.UNKNOWN если не найден
        """
        if not value:
            return cls.UNKNOWN
        try:
            return cls(value.lower().strip())
        except ValueError:
            return cls.UNKNOWN

    def is_event_operation(self) -> bool:
        """Проверка, является ли intent операцией с событием."""
        return self in {
            Intent.EVENT, Intent.UPDATE, Intent.UPDATE_MANY,
            Intent.DELETE, Intent.DELETE_ALL, Intent.DELETE_BY_PERIOD,
            Intent.DELETE_MANY, Intent.DELETE_BY_PATTERN, Intent.CREATE_MANY
        }

    def is_delete_operation(self) -> bool:
        """Проверка, является ли intent операцией удаления."""
        return self in {
            Intent.DELETE, Intent.DELETE_ALL, Intent.DELETE_BY_PERIOD,
            Intent.DELETE_MANY, Intent.DELETE_BY_PATTERN, Intent.DELETE_NOTE
        }

    def is_conversational(self) -> bool:
        """Проверка, является ли intent разговорным."""
        return self in {
            Intent.SMALL_TALK, Intent.QUESTION, Intent.GREETING, Intent.THANKS
        }


class ReminderType(str, Enum):
    """Типы напоминаний."""

    BEFORE = "before"       # За N минут до события
    START = "start"         # В момент начала события
    INTERVAL = "interval"   # Интервальное напоминание

    @classmethod
    def from_string(cls, value: str) -> 'ReminderType':
        """Безопасное преобразование строки."""
        if not value:
            return cls.BEFORE
        try:
            return cls(value.lower().strip())
        except ValueError:
            return cls.BEFORE


class EventStatus(str, Enum):
    """Статусы событий."""

    CONFIRMED = "confirmed"                 # Подтверждённое
    TENTATIVE = "tentative"                 # Предварительное
    CANCELLED = "cancelled"                 # Отменённое
    NEEDS_CONFIRMATION = "needs_confirmation"  # Требует подтверждения

    @classmethod
    def from_string(cls, value: str) -> 'EventStatus':
        """Безопасное преобразование строки."""
        if not value:
            return cls.CONFIRMED
        try:
            return cls(value.lower().strip())
        except ValueError:
            return cls.CONFIRMED


class CalendarProvider(str, Enum):
    """Провайдеры календарей."""

    GOOGLE = "google"
    ICLOUD = "icloud"
    LOCAL = "local"

    @classmethod
    def from_string(cls, value: str) -> 'CalendarProvider':
        """Безопасное преобразование строки."""
        if not value:
            return cls.LOCAL
        try:
            return cls(value.lower().strip())
        except ValueError:
            return cls.LOCAL


class AIMode(str, Enum):
    """Режимы интерпретации AI."""

    SOFT = "soft"       # Мягкий режим (AI дополняет информацию)
    STRICT = "strict"   # Строгий режим (только явная информация)

    @classmethod
    def from_string(cls, value: str) -> 'AIMode':
        """Безопасное преобразование строки."""
        if not value:
            return cls.SOFT
        try:
            return cls(value.lower().strip())
        except ValueError:
            return cls.SOFT


class FeedbackType(str, Enum):
    """Типы обратной связи."""

    BUG = "bug"                 # Баг
    SUGGESTION = "suggestion"  # Предложение
    OTHER = "other"            # Другое

    @classmethod
    def from_string(cls, value: str) -> 'FeedbackType':
        """Безопасное преобразование строки."""
        if not value:
            return cls.OTHER
        try:
            return cls(value.lower().strip())
        except ValueError:
            return cls.OTHER


class FeedbackStatus(str, Enum):
    """Статусы обратной связи."""

    NEW = "new"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"

    @classmethod
    def from_string(cls, value: str) -> 'FeedbackStatus':
        """Безопасное преобразование строки."""
        if not value:
            return cls.NEW
        try:
            return cls(value.lower().strip())
        except ValueError:
            return cls.NEW


class ConversationField(str, Enum):
    """Поля, которые могут запрашиваться в multi-turn диалоге."""

    TITLE = "title"
    START_TIME = "start_time"
    END_TIME = "end_time"
    DATE = "date"
    LOCATION = "location"
    DESCRIPTION = "description"
    REMINDER = "reminder"
    CONFIRMATION = "confirmation"

    @classmethod
    def from_string(cls, value: str) -> Optional['ConversationField']:
        """Безопасное преобразование строки."""
        if not value:
            return None
        try:
            return cls(value.lower().strip())
        except ValueError:
            return None


class ICloudStep(str, Enum):
    """Шаги подключения iCloud."""

    EMAIL = "email"
    PASSWORD = "password"
    CALENDAR_SELECT = "calendar_select"
    DONE = "done"

    @classmethod
    def from_string(cls, value: str) -> Optional['ICloudStep']:
        """Безопасное преобразование строки."""
        if not value:
            return None
        try:
            return cls(value.lower().strip())
        except ValueError:
            return None
