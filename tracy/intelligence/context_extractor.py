"""
==============================================================================
CONTEXT_EXTRACTOR.PY - ИЗВЛЕЧЕНИЕ КОНТЕКСТА ИЗ СООБЩЕНИЙ
==============================================================================

Извлекает контекст из:
- Reply сообщений (event_id, тип сообщения бота)
- Истории диалога
- Последних действий пользователя

==============================================================================
"""
import re
import logging
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from telegram import Update, Message
    from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


@dataclass
class MessageContext:
    """Контекст сообщения пользователя."""

    # Основная информация
    user_id: int
    text: str

    # Reply контекст
    is_reply: bool = False
    reply_to_bot: bool = False
    reply_message_text: Optional[str] = None

    # Извлечённые данные из reply
    event_id: Optional[int] = None
    event_title: Optional[str] = None
    event_date: Optional[datetime] = None

    # Тип сообщения бота на которое отвечают
    bot_message_type: Optional[str] = None  # 'event_created', 'event_confirmation', 'event_list', etc.

    # История диалога
    recent_events: List[Dict[str, Any]] = field(default_factory=list)
    last_action: Optional[str] = None

    # Дополнительные данные
    has_voice: bool = False
    has_photo: bool = False
    voice_text: Optional[str] = None


class ContextExtractor:
    """
    Извлекает контекст из сообщений для понимания намерения пользователя.
    """

    # Паттерны для извлечения event_id из сообщений бота
    EVENT_ID_PATTERNS = [
        r'event_id[=:]\s*(\d+)',
        r'#event(\d+)',
        r'ID:\s*(\d+)',
        r'data[=:].*?event[_-]?(\d+)',
    ]

    # Паттерны для определения типа сообщения бота
    BOT_MESSAGE_PATTERNS = {
        'event_created': [
            r'✅.*создан[оа]?',
            r'📅.*добавлен[оа]?',
            r'Событие.*создано',
            r'📝.*Обучение|Встреча|Событие',
        ],
        'event_confirmation': [
            r'Подтвердите',
            r'Создать событие\?',
            r'Сохранить\?',
        ],
        'event_list': [
            r'Ваши события',
            r'События на',
            r'📋.*список',
        ],
        'event_details': [
            r'· Дата:',
            r'· Время:',
            r'· Напоминание:',
        ],
        'delete_confirmation': [
            r'Удалить.*\?',
            r'Подтвердите удаление',
        ],
    }

    def __init__(self, db=None):
        """
        Args:
            db: Database instance для получения данных о событиях
        """
        self._db = db
        logger.info("ContextExtractor инициализирован")

    async def extract(
        self,
        update: 'Update',
        context: 'ContextTypes.DEFAULT_TYPE'
    ) -> MessageContext:
        """
        Извлечь полный контекст из сообщения.

        Args:
            update: Telegram Update
            context: Telegram Context

        Returns:
            MessageContext с извлечённой информацией
        """
        message = update.message
        if not message:
            return MessageContext(user_id=0, text="")

        user_id = message.from_user.id if message.from_user else 0
        text = message.text or message.caption or ""

        # Создаём базовый контекст
        msg_context = MessageContext(
            user_id=user_id,
            text=text,
            has_voice=bool(message.voice or message.audio),
            has_photo=bool(message.photo),
        )

        # Извлекаем контекст из reply
        if message.reply_to_message:
            await self._extract_reply_context(message.reply_to_message, msg_context)

        # Получаем последние события пользователя
        if self._db:
            msg_context.recent_events = await self._get_recent_events(user_id)

        # Получаем последнее действие из user_data
        if context and hasattr(context, 'user_data'):
            msg_context.last_action = context.user_data.get('last_action')

        logger.debug(
            f"Extracted context: reply={msg_context.is_reply}, "
            f"event_id={msg_context.event_id}, type={msg_context.bot_message_type}"
        )

        return msg_context

    async def _extract_reply_context(
        self,
        reply_message: 'Message',
        msg_context: MessageContext
    ) -> None:
        """Извлечь контекст из reply сообщения."""
        msg_context.is_reply = True
        msg_context.reply_message_text = reply_message.text or reply_message.caption or ""

        # Проверяем, отвечает ли на сообщение бота
        if reply_message.from_user and reply_message.from_user.is_bot:
            msg_context.reply_to_bot = True

            # Определяем тип сообщения бота
            msg_context.bot_message_type = self._detect_bot_message_type(
                msg_context.reply_message_text
            )

            # Извлекаем event_id
            msg_context.event_id = self._extract_event_id(reply_message)

            # Извлекаем название события
            msg_context.event_title = self._extract_event_title(
                msg_context.reply_message_text
            )

            # Извлекаем дату события
            msg_context.event_date = self._extract_event_date(
                msg_context.reply_message_text
            )

    def _detect_bot_message_type(self, text: str) -> Optional[str]:
        """Определить тип сообщения бота по тексту."""
        if not text:
            return None

        for msg_type, patterns in self.BOT_MESSAGE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return msg_type

        # Если есть структура события (дата, время) - это детали события
        if '· Дата:' in text or '· Время:' in text:
            return 'event_details'

        return None

    def _extract_event_id(self, message: 'Message') -> Optional[int]:
        """Извлечь event_id из сообщения бота."""
        # Проверяем inline keyboard
        if message.reply_markup and message.reply_markup.inline_keyboard:
            for row in message.reply_markup.inline_keyboard:
                for button in row:
                    if button.callback_data:
                        # Ищем паттерны типа confirm_123, delete_123, event_123
                        match = re.search(r'(?:confirm|delete|event|reschedule)[_-](\d+)', button.callback_data)
                        if match:
                            return int(match.group(1))

        # Ищем в тексте
        text = message.text or message.caption or ""
        for pattern in self.EVENT_ID_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return int(match.group(1))

        return None

    def _extract_event_title(self, text: str) -> Optional[str]:
        """Извлечь название события из текста сообщения бота."""
        if not text:
            return None

        # Паттерн: эмодзи + название (первая строка после эмодзи)
        # Например: "📝 Обучение" или "✅ Встреча с Катей создана"
        patterns = [
            r'^[📝📅✅🎯💼🏃‍♂️🎂🎉]\s*([^\n·]+?)(?:\s*создан[оа]?)?$',
            r'^[📝📅✅🎯💼🏃‍♂️🎂🎉]\s*(.+?)(?:\n|$)',
            r'Событие[:\s]+["\']?([^"\']+)["\']?',
            r'^(.+?)(?:\n\s*·\s*Дата:)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.MULTILINE)
            if match:
                title = match.group(1).strip()
                # Убираем лишние слова
                title = re.sub(r'\s*(создан[оа]?|добавлен[оа]?|сохранен[оа]?)\s*$', '', title, flags=re.IGNORECASE)
                if title and len(title) > 1:
                    return title

        return None

    def _extract_event_date(self, text: str) -> Optional[datetime]:
        """Извлечь дату события из текста сообщения бота."""
        if not text:
            return None

        # Ищем паттерн "· Дата: (Пн) 27 января" или "· Дата: 27.01.2026"
        date_pattern = r'·\s*Дата:\s*(?:\([А-Яа-я]{2}\)\s*)?(\d{1,2})[.\s](\d{1,2}|\w+)(?:[.\s](\d{4}))?'
        match = re.search(date_pattern, text)

        if match:
            day = int(match.group(1))
            month_str = match.group(2)
            year = int(match.group(3)) if match.group(3) else datetime.now().year

            # Преобразуем месяц
            months = {
                'январь': 1, 'января': 1, 'янв': 1,
                'февраль': 2, 'февраля': 2, 'фев': 2,
                'март': 3, 'марта': 3, 'мар': 3,
                'апрель': 4, 'апреля': 4, 'апр': 4,
                'май': 5, 'мая': 5,
                'июнь': 6, 'июня': 6, 'июн': 6,
                'июль': 7, 'июля': 7, 'июл': 7,
                'август': 8, 'августа': 8, 'авг': 8,
                'сентябрь': 9, 'сентября': 9, 'сен': 9,
                'октябрь': 10, 'октября': 10, 'окт': 10,
                'ноябрь': 11, 'ноября': 11, 'ноя': 11,
                'декабрь': 12, 'декабря': 12, 'дек': 12,
            }

            if month_str.isdigit():
                month = int(month_str)
            else:
                month = months.get(month_str.lower(), 1)

            try:
                return datetime(year, month, day)
            except ValueError:
                pass

        return None

    async def _get_recent_events(self, user_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """Получить последние события пользователя."""
        if not self._db:
            return []

        try:
            # Используем существующий метод базы данных
            events = self._db.get_upcoming_events(user_id, days=7)
            return events[:limit] if events else []
        except Exception as e:
            logger.error(f"Ошибка получения событий: {e}")
            return []

    def extract_event_id_from_callback(self, callback_data: str) -> Optional[int]:
        """Извлечь event_id из callback_data."""
        if not callback_data:
            return None

        patterns = [
            r'(?:confirm|delete|event|reschedule|edit)[_-](\d+)',
            r'^(\d+)$',
        ]

        for pattern in patterns:
            match = re.search(pattern, callback_data)
            if match:
                return int(match.group(1))

        return None
