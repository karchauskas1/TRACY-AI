"""
==============================================================================
INTENT_CLASSIFIER.PY - AI-КЛАССИФИКАЦИЯ НАМЕРЕНИЙ
==============================================================================

Использует LLM для точного определения что хочет пользователь.
Учитывает контекст reply, историю, и текст сообщения.

ИНТЕНТЫ:
    - CREATE: создать новое событие
    - DELETE: удалить существующее событие
    - UPDATE: изменить существующее событие
    - QUERY: найти/показать события
    - CONFIRM: подтвердить действие
    - CANCEL: отменить действие
    - CHAT: обычный разговор/вопрос

==============================================================================
"""
import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from tracy.intelligence.context_extractor import MessageContext

logger = logging.getLogger(__name__)


class IntentType(str, Enum):
    """Типы намерений пользователя."""
    CREATE = "create"          # Создать новое событие
    DELETE = "delete"          # Удалить событие
    UPDATE = "update"          # Изменить событие
    QUERY = "query"            # Найти/показать события
    CONFIRM = "confirm"        # Подтвердить действие
    CANCEL = "cancel"          # Отменить действие
    CHAT = "chat"              # Обычный разговор
    UNKNOWN = "unknown"        # Не удалось определить

    @classmethod
    def from_string(cls, value: str) -> 'IntentType':
        """Безопасное преобразование строки в IntentType."""
        if not value:
            return cls.UNKNOWN
        try:
            return cls(value.lower().strip())
        except ValueError:
            return cls.UNKNOWN


@dataclass
class TargetEvent:
    """Описание целевого события для действия."""
    # Как найти событие
    event_id: Optional[int] = None           # Конкретный ID (из reply)
    search_query: Optional[str] = None       # Поисковый запрос ("встреча с Катей")
    date_reference: Optional[str] = None     # Ссылка на дату ("завтра", "27 января")
    use_last_event: bool = False             # Использовать последнее созданное

    # Что изменить (для UPDATE)
    new_time: Optional[str] = None           # Новое время
    new_date: Optional[str] = None           # Новая дата
    new_title: Optional[str] = None          # Новое название


@dataclass
class UserIntent:
    """Результат классификации намерения пользователя."""
    intent_type: IntentType
    confidence: float = 1.0

    # Целевое событие (для DELETE, UPDATE, QUERY)
    target: Optional[TargetEvent] = None

    # Данные для создания (для CREATE)
    event_data: Optional[Dict[str, Any]] = None

    # Требуется ли подтверждение
    needs_confirmation: bool = False

    # Причина классификации (для отладки)
    reasoning: Optional[str] = None

    # Оригинальный ответ LLM
    raw_response: Optional[Dict[str, Any]] = None


class IntentClassifier:
    """
    AI-классификатор намерений пользователя.
    Использует LLM для точного понимания что хочет пользователь.
    """

    SYSTEM_PROMPT = '''Ты - анализатор намерений пользователя для календарного бота TRACY.
Твоя задача - точно определить что хочет сделать пользователь.

КОНТЕКСТ:
- Пользователь может отвечать (reply) на сообщение бота о событии
- Пользователь может ссылаться на события по названию ("встреча с Катей")
- Пользователь может использовать неявные указания ("удали это", "отмени")

ТИПЫ НАМЕРЕНИЙ:
1. CREATE - создать новое событие
   Примеры: "Встреча завтра в 15:00", "Добавь обед в пятницу", "Обучение понедельник 16-20"

2. DELETE - удалить существующее событие
   Примеры: "Удали", "Отмени", "Удали встречу с Катей", "Убери это событие"
   ВАЖНО: Если reply на сообщение о событии + "удали/отмени" = DELETE

3. UPDATE - изменить существующее событие
   Примеры: "Перенеси на 16:00", "Измени время на завтра", "Перенеси встречу с Катей на пятницу"

4. QUERY - найти или показать события
   Примеры: "Что у меня завтра?", "Когда встреча с Катей?", "Покажи события на неделю"

5. CONFIRM - подтвердить предыдущее действие
   Примеры: "Да", "Подтверждаю", "Ок", "Сохрани"

6. CANCEL - отменить предыдущее действие
   Примеры: "Нет", "Отмена", "Не надо"

7. CHAT - обычный разговор, не связанный с календарём
   Примеры: "Привет", "Как дела?", "Спасибо"

ПРАВИЛА ОПРЕДЕЛЕНИЯ:
1. Если есть reply на сообщение о событии:
   - "удали", "отмени", "убери" → DELETE с target.event_id из контекста
   - "перенеси", "измени время" → UPDATE с target.event_id из контекста
   - просто время/дата → UPDATE (изменение времени)

2. Если упоминается название события:
   - "удали встречу с Катей" → DELETE с target.search_query="встреча с Катей"
   - "перенеси обед на 14:00" → UPDATE с target.search_query="обед"

3. Если явно создаётся событие (есть название + время/дата):
   - → CREATE

4. Если вопрос о событиях:
   - → QUERY

ОТВЕТ в формате JSON:
{
    "intent": "delete|create|update|query|confirm|cancel|chat",
    "confidence": 0.0-1.0,
    "target": {
        "event_id": null или число (если известен из контекста),
        "search_query": "текст для поиска события" или null,
        "date_reference": "завтра" или "27 января" или null,
        "use_last_event": true/false,
        "new_time": "16:00" или null (для UPDATE),
        "new_date": "завтра" или "пятница" или null (для UPDATE),
        "new_title": "новое название" или null (для UPDATE)
    },
    "event_data": {
        "title": "название события" (для CREATE),
        "date": "дата" (для CREATE),
        "time": "время" (для CREATE),
        "end_time": "время окончания" (для CREATE)
    } или null,
    "needs_confirmation": true/false,
    "reasoning": "краткое объяснение почему такой intent"
}'''

    def __init__(self, llm_client=None, model: str = "gpt-4o-mini"):
        """
        Args:
            llm_client: OpenAI-совместимый клиент
            model: Название модели
        """
        self._client = llm_client
        self._model = model
        logger.info(f"IntentClassifier инициализирован с моделью {model}")

    def set_client(self, client) -> None:
        """Установить LLM клиент."""
        self._client = client

    async def classify(
        self,
        msg_context: 'MessageContext',
        user_timezone: str = "Europe/Moscow"
    ) -> UserIntent:
        """
        Классифицировать намерение пользователя.

        Args:
            msg_context: Контекст сообщения
            user_timezone: Часовой пояс пользователя

        Returns:
            UserIntent с определённым намерением
        """
        # Формируем промпт с контекстом
        user_prompt = self._build_user_prompt(msg_context)

        # Вызываем LLM
        try:
            result = await self._call_llm(user_prompt)
            intent = self._parse_response(result, msg_context)

            logger.info(
                f"Intent classified: {intent.intent_type.value} "
                f"(confidence={intent.confidence:.2f}, reason={intent.reasoning})"
            )

            return intent

        except Exception as e:
            logger.error(f"Ошибка классификации intent: {e}")
            # Fallback: пытаемся определить по ключевым словам
            return self._fallback_classify(msg_context)

    def _build_user_prompt(self, ctx: 'MessageContext') -> str:
        """Построить промпт для LLM с контекстом."""
        parts = []

        # Основной текст
        parts.append(f"СООБЩЕНИЕ ПОЛЬЗОВАТЕЛЯ: {ctx.text}")

        # Контекст reply
        if ctx.is_reply and ctx.reply_to_bot:
            parts.append("\n--- КОНТЕКСТ REPLY ---")
            parts.append(f"Пользователь отвечает на сообщение бота.")

            if ctx.event_id:
                parts.append(f"Event ID из контекста: {ctx.event_id}")

            if ctx.event_title:
                parts.append(f"Название события: {ctx.event_title}")

            if ctx.event_date:
                parts.append(f"Дата события: {ctx.event_date.strftime('%d.%m.%Y')}")

            if ctx.bot_message_type:
                parts.append(f"Тип сообщения бота: {ctx.bot_message_type}")

            if ctx.reply_message_text:
                # Ограничиваем длину текста
                reply_text = ctx.reply_message_text[:500]
                parts.append(f"Текст сообщения бота:\n{reply_text}")

        # Последние события
        if ctx.recent_events:
            parts.append("\n--- ПОСЛЕДНИЕ СОБЫТИЯ ПОЛЬЗОВАТЕЛЯ ---")
            for event in ctx.recent_events[:3]:
                title = event.get('title', 'Без названия')
                date = event.get('start_time', '')
                event_id = event.get('id', '')
                parts.append(f"- {title} ({date}) [ID: {event_id}]")

        parts.append("\nОпредели intent и верни JSON.")

        return "\n".join(parts)

    async def _call_llm(self, user_prompt: str) -> Dict[str, Any]:
        """Вызвать LLM и получить ответ."""
        if not self._client:
            raise ValueError("LLM client не установлен")

        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content
        return json.loads(content)

    def _parse_response(
        self,
        response: Dict[str, Any],
        ctx: 'MessageContext'
    ) -> UserIntent:
        """Парсить ответ LLM в UserIntent."""
        intent_type = IntentType.from_string(response.get("intent", "unknown"))
        confidence = float(response.get("confidence", 0.8))

        # Парсим target
        target = None
        target_data = response.get("target")
        if target_data:
            target = TargetEvent(
                event_id=target_data.get("event_id") or ctx.event_id,
                search_query=target_data.get("search_query"),
                date_reference=target_data.get("date_reference"),
                use_last_event=target_data.get("use_last_event", False),
                new_time=target_data.get("new_time"),
                new_date=target_data.get("new_date"),
                new_title=target_data.get("new_title"),
            )
        elif ctx.event_id:
            # Если LLM не вернул target, но есть event_id из контекста
            target = TargetEvent(event_id=ctx.event_id)

        return UserIntent(
            intent_type=intent_type,
            confidence=confidence,
            target=target,
            event_data=response.get("event_data"),
            needs_confirmation=response.get("needs_confirmation", False),
            reasoning=response.get("reasoning"),
            raw_response=response,
        )

    def _fallback_classify(self, ctx: 'MessageContext') -> UserIntent:
        """
        Fallback классификация по ключевым словам.
        Используется если LLM недоступен.
        """
        text = ctx.text.lower().strip()

        # DELETE паттерны
        delete_patterns = ['удали', 'отмени', 'убери', 'удалить', 'отменить']
        for pattern in delete_patterns:
            if pattern in text:
                target = TargetEvent()
                if ctx.event_id:
                    target.event_id = ctx.event_id
                else:
                    # Пытаемся извлечь search_query
                    for p in delete_patterns:
                        text = text.replace(p, '').strip()
                    if text:
                        target.search_query = text

                return UserIntent(
                    intent_type=IntentType.DELETE,
                    confidence=0.7,
                    target=target,
                    reasoning="Fallback: найдено ключевое слово удаления"
                )

        # UPDATE паттерны
        update_patterns = ['перенеси', 'измени', 'поменяй', 'сдвинь']
        for pattern in update_patterns:
            if pattern in text:
                target = TargetEvent()
                if ctx.event_id:
                    target.event_id = ctx.event_id
                return UserIntent(
                    intent_type=IntentType.UPDATE,
                    confidence=0.7,
                    target=target,
                    reasoning="Fallback: найдено ключевое слово изменения"
                )

        # QUERY паттерны
        query_patterns = ['что у меня', 'покажи', 'когда', 'какие события', 'список']
        for pattern in query_patterns:
            if pattern in text:
                return UserIntent(
                    intent_type=IntentType.QUERY,
                    confidence=0.7,
                    reasoning="Fallback: найдено ключевое слово запроса"
                )

        # CONFIRM/CANCEL
        if text in ['да', 'ок', 'подтверждаю', 'сохрани', 'yes']:
            return UserIntent(
                intent_type=IntentType.CONFIRM,
                confidence=0.9,
                reasoning="Fallback: подтверждение"
            )

        if text in ['нет', 'отмена', 'не надо', 'no', 'cancel']:
            return UserIntent(
                intent_type=IntentType.CANCEL,
                confidence=0.9,
                reasoning="Fallback: отмена"
            )

        # По умолчанию - CREATE (предполагаем создание события)
        return UserIntent(
            intent_type=IntentType.CREATE,
            confidence=0.5,
            reasoning="Fallback: по умолчанию CREATE"
        )


# Синхронная версия для обратной совместимости
class IntentClassifierSync:
    """Синхронная обёртка для IntentClassifier."""

    def __init__(self, llm_client=None, model: str = "gpt-4o-mini"):
        self._async_classifier = IntentClassifier(llm_client, model)

    def classify_sync(self, msg_context: 'MessageContext') -> UserIntent:
        """Синхронная классификация (использует fallback)."""
        return self._async_classifier._fallback_classify(msg_context)
