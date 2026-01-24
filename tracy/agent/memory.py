"""
==============================================================================
MEMORY.PY - ПАМЯТЬ РАЗГОВОРА
==============================================================================

Хранит историю диалога с пользователем для контекста.
LLM использует эту историю чтобы понимать:
- О чём шла речь раньше
- Какие события обсуждались
- Что пользователь уже подтвердил/отменил

==============================================================================
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from collections import defaultdict
import json

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """Одно сообщение в истории."""
    role: str  # "user", "assistant", "tool"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)

    # Для tool messages
    tool_name: Optional[str] = None
    tool_call_id: Optional[str] = None

    # Метаданные
    event_id: Optional[int] = None  # ID события из контекста
    event_title: Optional[str] = None  # Название события

    def to_openai_format(self) -> Dict[str, Any]:
        """Конвертировать в формат OpenAI API."""
        if self.role == "tool":
            return {
                "role": "tool",
                "tool_call_id": self.tool_call_id,
                "content": self.content
            }
        return {
            "role": self.role,
            "content": self.content
        }


@dataclass
class ConversationContext:
    """Контекст текущего разговора."""
    # Ожидаем ответ на вопрос
    waiting_for_response: bool = False
    pending_question: Optional[str] = None
    pending_context: Optional[str] = None  # Что делать после ответа
    pending_options: Optional[List[str]] = None

    # Событие из reply
    reply_event_id: Optional[int] = None
    reply_event_title: Optional[str] = None

    # Последнее действие
    last_action: Optional[str] = None
    last_event_id: Optional[int] = None


class ConversationMemory:
    """
    Память разговоров для каждого пользователя.
    """

    def __init__(self, max_messages: int = 20, ttl_minutes: int = 30):
        """
        Args:
            max_messages: Максимум сообщений в истории на пользователя
            ttl_minutes: Время жизни истории в минутах
        """
        self._max_messages = max_messages
        self._ttl = timedelta(minutes=ttl_minutes)

        # История сообщений по user_id
        self._messages: Dict[int, List[Message]] = defaultdict(list)

        # Контекст по user_id
        self._context: Dict[int, ConversationContext] = defaultdict(ConversationContext)

        # Последняя активность
        self._last_activity: Dict[int, datetime] = {}

        logger.info(f"ConversationMemory инициализирована (max={max_messages}, ttl={ttl_minutes}min)")

    def add_user_message(
        self,
        user_id: int,
        text: str,
        event_id: Optional[int] = None,
        event_title: Optional[str] = None
    ) -> None:
        """Добавить сообщение пользователя."""
        self._cleanup_old(user_id)

        message = Message(
            role="user",
            content=text,
            event_id=event_id,
            event_title=event_title
        )

        self._messages[user_id].append(message)
        self._last_activity[user_id] = datetime.now()

        # Обновляем контекст если есть event_id
        if event_id:
            ctx = self._context[user_id]
            ctx.reply_event_id = event_id
            ctx.reply_event_title = event_title

        self._trim_history(user_id)

        logger.debug(f"Added user message for {user_id}: {text[:50]}...")

    def add_assistant_message(
        self,
        user_id: int,
        text: str
    ) -> None:
        """Добавить ответ ассистента."""
        message = Message(
            role="assistant",
            content=text
        )

        self._messages[user_id].append(message)
        self._last_activity[user_id] = datetime.now()
        self._trim_history(user_id)

    def add_tool_result(
        self,
        user_id: int,
        tool_name: str,
        tool_call_id: str,
        result: Dict[str, Any]
    ) -> None:
        """Добавить результат выполнения инструмента."""
        message = Message(
            role="tool",
            content=json.dumps(result, ensure_ascii=False),
            tool_name=tool_name,
            tool_call_id=tool_call_id
        )

        self._messages[user_id].append(message)
        self._last_activity[user_id] = datetime.now()

    def get_history(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Получить историю в формате OpenAI API.

        Returns:
            Список сообщений для messages параметра
        """
        self._cleanup_old(user_id)

        messages = self._messages.get(user_id, [])
        return [msg.to_openai_format() for msg in messages]

    def get_context(self, user_id: int) -> ConversationContext:
        """Получить контекст разговора."""
        return self._context[user_id]

    def set_waiting_for_response(
        self,
        user_id: int,
        question: str,
        context: Optional[str] = None,
        options: Optional[List[str]] = None
    ) -> None:
        """Установить ожидание ответа."""
        ctx = self._context[user_id]
        ctx.waiting_for_response = True
        ctx.pending_question = question
        ctx.pending_context = context
        ctx.pending_options = options

    def clear_waiting(self, user_id: int) -> None:
        """Очистить ожидание ответа."""
        ctx = self._context[user_id]
        ctx.waiting_for_response = False
        ctx.pending_question = None
        ctx.pending_context = None
        ctx.pending_options = None

    def set_last_action(
        self,
        user_id: int,
        action: str,
        event_id: Optional[int] = None
    ) -> None:
        """Сохранить последнее действие."""
        ctx = self._context[user_id]
        ctx.last_action = action
        ctx.last_event_id = event_id

    def clear_history(self, user_id: int) -> None:
        """Очистить историю пользователя."""
        self._messages[user_id] = []
        self._context[user_id] = ConversationContext()
        logger.debug(f"Cleared history for {user_id}")

    def get_context_summary(self, user_id: int) -> str:
        """
        Получить краткое описание контекста для LLM.

        Returns:
            Текст с описанием текущего контекста
        """
        ctx = self._context[user_id]
        parts = []

        if ctx.reply_event_id:
            parts.append(f"Пользователь отвечает на сообщение о событии ID={ctx.reply_event_id}")
            if ctx.reply_event_title:
                parts.append(f"Название события: {ctx.reply_event_title}")

        if ctx.waiting_for_response:
            parts.append(f"Ожидаем ответ на вопрос: {ctx.pending_question}")
            if ctx.pending_context:
                parts.append(f"После ответа: {ctx.pending_context}")

        if ctx.last_action:
            parts.append(f"Последнее действие: {ctx.last_action}")
            if ctx.last_event_id:
                parts.append(f"Над событием ID={ctx.last_event_id}")

        return "\n".join(parts) if parts else ""

    def _cleanup_old(self, user_id: int) -> None:
        """Удалить устаревшую историю."""
        last = self._last_activity.get(user_id)
        if last and datetime.now() - last > self._ttl:
            self.clear_history(user_id)
            logger.debug(f"Cleaned up old history for {user_id}")

    def _trim_history(self, user_id: int) -> None:
        """Обрезать историю до max_messages."""
        messages = self._messages[user_id]
        if len(messages) > self._max_messages:
            # Оставляем последние max_messages
            self._messages[user_id] = messages[-self._max_messages:]


# Глобальный instance
_memory: Optional[ConversationMemory] = None


def get_memory() -> ConversationMemory:
    """Получить глобальную память."""
    global _memory
    if _memory is None:
        _memory = ConversationMemory()
    return _memory


def set_memory(memory: ConversationMemory) -> None:
    """Установить глобальную память."""
    global _memory
    _memory = memory
