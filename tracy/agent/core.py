"""
==============================================================================
CORE.PY - ЯДРО АГЕНТА
==============================================================================

Главный компонент который:
1. Получает сообщение пользователя
2. Передаёт его LLM вместе с доступными инструментами
3. LLM решает какие инструменты вызвать
4. Выполняет инструменты и возвращает результат LLM
5. Повторяет пока LLM не даст финальный ответ

Это реализация "самопрограммирующегося" подхода -
LLM сам решает что делать на основе запроса пользователя.

==============================================================================
"""
import logging
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from enum import Enum

from tracy.agent.tools import TOOLS_SCHEMA, ToolExecutor
from tracy.agent.memory import ConversationMemory, get_memory

if TYPE_CHECKING:
    from telegram import Update, InlineKeyboardMarkup
    from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """Ты - TRACY, умный календарный ассистент в Telegram.

ТВОЯ ЗАДАЧА: Понять что хочет пользователь и выполнить это с помощью доступных инструментов.

ПРАВИЛА:
1. Всегда используй get_current_datetime чтобы знать какой сегодня день
2. Для удаления/изменения события - сначала найди его через search_events
3. Если нужно уточнение - используй ask_user
4. После выполнения действия - используй send_response чтобы сообщить результат
5. Будь лаконичным и дружелюбным

КОНТЕКСТ REPLY:
Если пользователь отвечает на сообщение бота о событии - это указание на конкретное событие.
"Удали" в reply на событие = удалить это событие.
"Перенеси на 15:00" в reply на событие = изменить время этого события.

ПРИМЕРЫ:
- "Встреча завтра в 15:00" → create_event
- "Что у меня завтра?" → search_events + send_response
- "Удали" (reply на событие) → delete_event (если знаешь ID) или search_events
- "Удали встречу с Катей" → search_events("встреча с Катей") → delete_event
- "Перенеси на 16:00" → search_events (найти какое) → update_event

ПОМНИ:
- Ты не пишешь код - ты используешь готовые инструменты
- Каждый инструмент делает одно конкретное действие
- Можешь вызывать несколько инструментов подряд
- Всегда заканчивай send_response или ask_user"""


class AgentStatus(str, Enum):
    """Статус выполнения агента."""
    SUCCESS = "success"           # Успешно завершён
    WAITING = "waiting"           # Ожидает ответа пользователя
    ERROR = "error"               # Ошибка
    MAX_ITERATIONS = "max_iter"   # Превышен лимит итераций


@dataclass
class AgentResult:
    """Результат работы агента."""
    status: AgentStatus

    # Текст ответа для пользователя
    message: Optional[str] = None

    # Inline keyboard (если есть варианты)
    keyboard: Optional['InlineKeyboardMarkup'] = None

    # События для показа
    events: Optional[List[Dict]] = None

    # Ожидаем ответ
    waiting_for_response: bool = False
    pending_question: Optional[str] = None

    # Отладка
    tool_calls: List[str] = field(default_factory=list)
    iterations: int = 0


class AgentCore:
    """
    Главное ядро агента.
    LLM сам решает какие инструменты использовать.
    """

    def __init__(
        self,
        db,
        llm_client,
        model: str = "gpt-4o-mini",
        max_iterations: int = 10
    ):
        """
        Args:
            db: Database instance
            llm_client: OpenAI-совместимый клиент
            model: Модель для использования
            max_iterations: Максимум итераций (защита от зацикливания)
        """
        self._db = db
        self._llm_client = llm_client
        self._model = model
        self._max_iterations = max_iterations

        self._tool_executor = ToolExecutor(db)
        self._memory = get_memory()

        logger.info(f"AgentCore инициализирован с моделью {model}")

    def set_llm_client(self, client) -> None:
        """Установить LLM клиент."""
        self._llm_client = client

    async def process(
        self,
        user_id: int,
        text: str,
        user_timezone: str = "Europe/Moscow",
        reply_event_id: Optional[int] = None,
        reply_event_title: Optional[str] = None
    ) -> AgentResult:
        """
        Обработать сообщение пользователя.

        Args:
            user_id: ID пользователя
            text: Текст сообщения
            user_timezone: Часовой пояс
            reply_event_id: ID события из reply (если есть)
            reply_event_title: Название события из reply

        Returns:
            AgentResult с ответом
        """
        logger.info(f"Agent processing: user={user_id}, text='{text[:50]}...'")

        # Настраиваем timezone для tool executor
        self._tool_executor.set_timezone(user_timezone)

        # Добавляем сообщение в память
        self._memory.add_user_message(
            user_id, text,
            event_id=reply_event_id,
            event_title=reply_event_title
        )

        # Формируем начальные сообщения
        messages = self._build_messages(user_id, text, reply_event_id, reply_event_title)

        # Запускаем цикл агента
        result = await self._agent_loop(user_id, messages)

        # Сохраняем ответ в память
        if result.message:
            self._memory.add_assistant_message(user_id, result.message)

        return result

    def _build_messages(
        self,
        user_id: int,
        text: str,
        reply_event_id: Optional[int],
        reply_event_title: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Построить сообщения для LLM."""
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

        # Добавляем историю
        history = self._memory.get_history(user_id)
        # Берём последние сообщения (не включая текущее, оно уже добавлено)
        for msg in history[:-1]:
            messages.append(msg)

        # Добавляем контекст
        context_parts = []

        # Контекст reply
        if reply_event_id:
            context_parts.append(f"[КОНТЕКСТ: Пользователь отвечает на сообщение о событии. ID события: {reply_event_id}")
            if reply_event_title:
                context_parts.append(f"Название: {reply_event_title}")
            context_parts.append("Если пользователь говорит 'удали', 'отмени', 'перенеси' - это про это событие.]")

        # Контекст ожидания
        ctx = self._memory.get_context(user_id)
        if ctx.waiting_for_response:
            context_parts.append(f"[КОНТЕКСТ: Ожидали ответ на вопрос: {ctx.pending_question}]")
            if ctx.pending_context:
                context_parts.append(f"[После ответа нужно: {ctx.pending_context}]")
            self._memory.clear_waiting(user_id)

        # Формируем сообщение пользователя
        user_content = text
        if context_parts:
            user_content = "\n".join(context_parts) + "\n\n" + text

        messages.append({"role": "user", "content": user_content})

        return messages

    async def _agent_loop(
        self,
        user_id: int,
        messages: List[Dict[str, Any]]
    ) -> AgentResult:
        """
        Главный цикл агента.
        Вызывает LLM, выполняет tools, повторяет пока не будет финальный ответ.
        """
        tool_calls_log = []
        iterations = 0

        while iterations < self._max_iterations:
            iterations += 1
            logger.debug(f"Agent iteration {iterations}")

            try:
                # Вызываем LLM
                response = await self._call_llm(messages)

                # Получаем message
                assistant_message = response.choices[0].message

                # Проверяем есть ли tool_calls
                if assistant_message.tool_calls:
                    # Добавляем ответ ассистента в messages
                    messages.append({
                        "role": "assistant",
                        "content": assistant_message.content or "",
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments
                                }
                            }
                            for tc in assistant_message.tool_calls
                        ]
                    })

                    # Выполняем каждый tool call
                    for tool_call in assistant_message.tool_calls:
                        tool_name = tool_call.function.name
                        tool_args = json.loads(tool_call.function.arguments)

                        tool_calls_log.append(f"{tool_name}({json.dumps(tool_args, ensure_ascii=False)})")
                        logger.info(f"Tool call: {tool_name} with {tool_args}")

                        # Выполняем
                        result = await self._tool_executor.execute(
                            tool_name, tool_args, user_id
                        )

                        # Добавляем результат в память
                        self._memory.add_tool_result(
                            user_id, tool_name, tool_call.id, result
                        )

                        # Добавляем результат в messages
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(result, ensure_ascii=False)
                        })

                        # Проверяем терминальные инструменты
                        if tool_name == "send_response":
                            return AgentResult(
                                status=AgentStatus.SUCCESS,
                                message=result.get("message", ""),
                                events=result.get("events"),
                                tool_calls=tool_calls_log,
                                iterations=iterations
                            )

                        if tool_name == "ask_user":
                            # Сохраняем ожидание
                            self._memory.set_waiting_for_response(
                                user_id,
                                result.get("question", ""),
                                result.get("context"),
                                result.get("options")
                            )

                            return AgentResult(
                                status=AgentStatus.WAITING,
                                message=result.get("question"),
                                waiting_for_response=True,
                                pending_question=result.get("question"),
                                keyboard=self._build_keyboard(result.get("options")),
                                tool_calls=tool_calls_log,
                                iterations=iterations
                            )

                else:
                    # Нет tool_calls - LLM дал текстовый ответ
                    content = assistant_message.content or ""

                    if content:
                        return AgentResult(
                            status=AgentStatus.SUCCESS,
                            message=content,
                            tool_calls=tool_calls_log,
                            iterations=iterations
                        )
                    else:
                        # Пустой ответ - продолжаем
                        logger.warning("Empty response from LLM, continuing...")

            except Exception as e:
                logger.error(f"Agent loop error: {e}", exc_info=True)
                return AgentResult(
                    status=AgentStatus.ERROR,
                    message=f"Произошла ошибка: {str(e)}",
                    tool_calls=tool_calls_log,
                    iterations=iterations
                )

        # Превышен лимит итераций
        logger.warning(f"Max iterations reached for user {user_id}")
        return AgentResult(
            status=AgentStatus.MAX_ITERATIONS,
            message="Извини, не удалось обработать запрос. Попробуй переформулировать.",
            tool_calls=tool_calls_log,
            iterations=iterations
        )

    async def _call_llm(self, messages: List[Dict[str, Any]]) -> Any:
        """Вызвать LLM с tools."""
        import asyncio

        if not self._llm_client:
            raise ValueError("LLM client не установлен")

        # OpenRouter клиент синхронный, запускаем в thread pool
        def sync_call():
            return self._llm_client.chat.completions.create(
                model=self._model,
                messages=messages,
                tools=TOOLS_SCHEMA,
                tool_choice="auto",
                temperature=0.1
            )

        response = await asyncio.to_thread(sync_call)
        return response

    def _build_keyboard(self, options: Optional[List[str]]) -> Optional['InlineKeyboardMarkup']:
        """Построить inline keyboard из опций."""
        if not options:
            return None

        from telegram import InlineKeyboardButton, InlineKeyboardMarkup

        buttons = []
        for i, option in enumerate(options):
            buttons.append([
                InlineKeyboardButton(
                    text=option,
                    callback_data=f"agent_option_{i}"
                )
            ])

        return InlineKeyboardMarkup(buttons)


# =============================================================================
# Глобальный instance
# =============================================================================

_agent: Optional[AgentCore] = None


def get_agent() -> Optional[AgentCore]:
    """Получить глобальный AgentCore."""
    return _agent


def set_agent(agent: AgentCore) -> None:
    """Установить глобальный AgentCore."""
    global _agent
    _agent = agent


def create_agent(
    db,
    llm_client=None,
    model: str = "gpt-4o-mini"
) -> AgentCore:
    """
    Создать и установить глобальный AgentCore.

    Args:
        db: Database instance
        llm_client: LLM клиент
        model: Модель

    Returns:
        Созданный AgentCore
    """
    global _agent
    _agent = AgentCore(
        db=db,
        llm_client=llm_client,
        model=model
    )
    return _agent
