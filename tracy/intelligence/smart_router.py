"""
==============================================================================
SMART_ROUTER.PY - ГЛАВНЫЙ РОУТЕР ИНТЕЛЛЕКТУАЛЬНОЙ ОБРАБОТКИ
==============================================================================

Объединяет все компоненты intelligence модуля:
1. Извлекает контекст (reply, история)
2. Классифицирует намерение через AI
3. Находит целевые события
4. Выполняет действие
5. Формирует ответ

ИСПОЛЬЗОВАНИЕ:
    from tracy.intelligence import SmartRouter

    router = SmartRouter(db, llm_client)
    result = await router.process_message(update, context)

    if result.handled:
        await update.message.reply_text(result.response_text)

==============================================================================
"""
import logging
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Callable, TYPE_CHECKING

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from tracy.intelligence.context_extractor import ContextExtractor, MessageContext
from tracy.intelligence.intent_classifier import IntentClassifier, UserIntent, IntentType, TargetEvent
from tracy.intelligence.entity_resolver import EntityResolver, ResolvedEntity
from tracy.intelligence.action_executor import ActionExecutor, ActionResult, ActionStatus

if TYPE_CHECKING:
    from telegram import Update
    from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


@dataclass
class RouterResult:
    """Результат обработки сообщения роутером."""
    # Было ли сообщение обработано
    handled: bool = False

    # Текст ответа
    response_text: Optional[str] = None

    # Inline keyboard для ответа
    reply_markup: Optional[InlineKeyboardMarkup] = None

    # Нужно ли передать обработку дальше (существующей логике)
    pass_through: bool = False

    # Данные для передачи в существующую логику
    pass_through_data: Optional[Dict[str, Any]] = None

    # Intent который был определён
    intent: Optional[UserIntent] = None

    # Результат действия
    action_result: Optional[ActionResult] = None


class SmartRouter:
    """
    Главный роутер для интеллектуальной обработки сообщений.
    """

    def __init__(
        self,
        db,
        llm_client=None,
        nlp_extractor=None,
        decision_engine=None,
        model: str = "gpt-4o-mini"
    ):
        """
        Args:
            db: Database instance
            llm_client: OpenAI-совместимый клиент для AI классификации
            nlp_extractor: NLPExtractor для создания событий
            decision_engine: DecisionEngine для существующей логики
            model: Модель для intent classification
        """
        self._db = db
        self._llm_client = llm_client
        self._nlp_extractor = nlp_extractor
        self._decision_engine = decision_engine

        # Инициализируем компоненты
        self._context_extractor = ContextExtractor(db)
        self._intent_classifier = IntentClassifier(llm_client, model)
        self._entity_resolver = EntityResolver(db)
        self._action_executor = ActionExecutor(db)

        logger.info("SmartRouter инициализирован")

    def set_llm_client(self, client) -> None:
        """Установить LLM клиент."""
        self._llm_client = client
        self._intent_classifier.set_client(client)

    def set_bot(self, bot) -> None:
        """Установить Telegram Bot."""
        self._action_executor.set_bot(bot)

    def set_decision_engine(self, engine) -> None:
        """Установить DecisionEngine для создания событий."""
        self._decision_engine = engine

    def set_nlp_extractor(self, extractor) -> None:
        """Установить NLPExtractor."""
        self._nlp_extractor = extractor

    async def process_message(
        self,
        update: 'Update',
        context: 'ContextTypes.DEFAULT_TYPE',
        user_timezone: str = "Europe/Moscow"
    ) -> RouterResult:
        """
        Обработать входящее сообщение.

        Args:
            update: Telegram Update
            context: Telegram Context
            user_timezone: Часовой пояс пользователя

        Returns:
            RouterResult с результатом обработки
        """
        if not update.message:
            return RouterResult(handled=False, pass_through=True)

        user_id = update.message.from_user.id if update.message.from_user else 0
        text = update.message.text or ""

        logger.info(f"SmartRouter: обработка сообщения от {user_id}: {text[:50]}...")

        try:
            # 1. Извлекаем контекст
            msg_context = await self._context_extractor.extract(update, context)

            # 2. Классифицируем намерение
            intent = await self._intent_classifier.classify(msg_context, user_timezone)

            logger.info(
                f"SmartRouter: intent={intent.intent_type.value}, "
                f"confidence={intent.confidence:.2f}"
            )

            # 3. Обрабатываем в зависимости от intent
            result = await self._route_by_intent(
                intent, msg_context, user_id, user_timezone
            )

            result.intent = intent
            return result

        except Exception as e:
            logger.error(f"SmartRouter: ошибка обработки: {e}", exc_info=True)
            # При ошибке передаём обработку существующей логике
            return RouterResult(handled=False, pass_through=True)

    async def _route_by_intent(
        self,
        intent: UserIntent,
        msg_context: MessageContext,
        user_id: int,
        user_timezone: str
    ) -> RouterResult:
        """Маршрутизация по типу намерения."""

        handlers = {
            IntentType.DELETE: self._handle_delete,
            IntentType.UPDATE: self._handle_update,
            IntentType.QUERY: self._handle_query,
            IntentType.CONFIRM: self._handle_confirm,
            IntentType.CANCEL: self._handle_cancel,
            IntentType.CREATE: self._handle_create,
            IntentType.CHAT: self._handle_chat,
        }

        handler = handlers.get(intent.intent_type, self._handle_unknown)
        return await handler(intent, msg_context, user_id, user_timezone)

    async def _handle_delete(
        self,
        intent: UserIntent,
        msg_context: MessageContext,
        user_id: int,
        user_timezone: str
    ) -> RouterResult:
        """Обработка намерения DELETE."""
        # Если нет target - пытаемся использовать последнее событие
        if not intent.target:
            intent.target = TargetEvent(use_last_event=True)

        # Находим событие
        resolved = await self._entity_resolver.resolve(
            user_id, intent.target, user_timezone
        )

        # Выполняем удаление
        action_result = await self._action_executor.execute_delete(
            user_id, resolved, force=False
        )

        return self._create_response(action_result)

    async def _handle_update(
        self,
        intent: UserIntent,
        msg_context: MessageContext,
        user_id: int,
        user_timezone: str
    ) -> RouterResult:
        """Обработка намерения UPDATE."""
        if not intent.target:
            return RouterResult(
                handled=True,
                response_text="❌ Не указано какое событие изменить"
            )

        # Находим событие
        resolved = await self._entity_resolver.resolve(
            user_id, intent.target, user_timezone
        )

        # Выполняем изменение
        action_result = await self._action_executor.execute_update(
            user_id, resolved, intent.target, user_timezone
        )

        return self._create_response(action_result)

    async def _handle_query(
        self,
        intent: UserIntent,
        msg_context: MessageContext,
        user_id: int,
        user_timezone: str
    ) -> RouterResult:
        """Обработка намерения QUERY."""
        # Если есть target - ищем конкретное событие
        if intent.target and (intent.target.search_query or intent.target.date_reference):
            resolved = await self._entity_resolver.resolve(
                user_id, intent.target, user_timezone
            )
        else:
            # Показываем ближайшие события
            events = await self._entity_resolver.search_events(
                user_id, limit=10
            )
            resolved = ResolvedEntity(
                events=events,
                found=bool(events),
                multiple_matches=len(events) > 1,
                single_match=len(events) == 1,
                no_matches=not events
            )

        action_result = await self._action_executor.execute_query(user_id, resolved)
        return self._create_response(action_result)

    async def _handle_confirm(
        self,
        intent: UserIntent,
        msg_context: MessageContext,
        user_id: int,
        user_timezone: str
    ) -> RouterResult:
        """Обработка подтверждения."""
        # Передаём существующей логике для обработки подтверждений
        return RouterResult(
            handled=False,
            pass_through=True,
            pass_through_data={"intent": "confirm"}
        )

    async def _handle_cancel(
        self,
        intent: UserIntent,
        msg_context: MessageContext,
        user_id: int,
        user_timezone: str
    ) -> RouterResult:
        """Обработка отмены."""
        return RouterResult(
            handled=True,
            response_text="✅ Действие отменено"
        )

    async def _handle_create(
        self,
        intent: UserIntent,
        msg_context: MessageContext,
        user_id: int,
        user_timezone: str
    ) -> RouterResult:
        """Обработка создания события - передаём существующей логике."""
        # CREATE обрабатывается существующим decision_engine
        return RouterResult(
            handled=False,
            pass_through=True,
            pass_through_data={
                "intent": "create",
                "event_data": intent.event_data
            }
        )

    async def _handle_chat(
        self,
        intent: UserIntent,
        msg_context: MessageContext,
        user_id: int,
        user_timezone: str
    ) -> RouterResult:
        """Обработка обычного разговора - передаём существующей логике."""
        return RouterResult(
            handled=False,
            pass_through=True,
            pass_through_data={"intent": "chat"}
        )

    async def _handle_unknown(
        self,
        intent: UserIntent,
        msg_context: MessageContext,
        user_id: int,
        user_timezone: str
    ) -> RouterResult:
        """Обработка неизвестного intent."""
        return RouterResult(
            handled=False,
            pass_through=True
        )

    def _create_response(self, action_result: ActionResult) -> RouterResult:
        """Создать RouterResult из ActionResult."""
        result = RouterResult(
            handled=True,
            response_text=action_result.message,
            action_result=action_result
        )

        # Создаём keyboard если есть опции
        if action_result.keyboard_options:
            buttons = []
            for opt in action_result.keyboard_options:
                buttons.append([
                    InlineKeyboardButton(
                        text=opt["text"],
                        callback_data=opt["callback_data"]
                    )
                ])
            result.reply_markup = InlineKeyboardMarkup(buttons)

        return result

    async def handle_callback(
        self,
        callback_data: str,
        user_id: int,
        user_timezone: str = "Europe/Moscow"
    ) -> RouterResult:
        """
        Обработать callback от inline keyboard.

        Args:
            callback_data: Данные из callback
            user_id: ID пользователя
            user_timezone: Часовой пояс

        Returns:
            RouterResult
        """
        logger.info(f"SmartRouter: callback {callback_data} от {user_id}")

        # Парсим callback
        if callback_data.startswith("smart_delete_confirm_"):
            event_id = int(callback_data.replace("smart_delete_confirm_", ""))
            return await self._confirm_delete(user_id, event_id)

        elif callback_data.startswith("smart_delete_"):
            if callback_data == "smart_delete_cancel":
                return RouterResult(
                    handled=True,
                    response_text="✅ Удаление отменено"
                )
            # Выбор события для удаления
            event_id = int(callback_data.replace("smart_delete_", ""))
            return await self._confirm_delete(user_id, event_id)

        elif callback_data.startswith("smart_update_"):
            if callback_data == "smart_update_cancel":
                return RouterResult(
                    handled=True,
                    response_text="✅ Изменение отменено"
                )
            # Выбор события для изменения
            event_id = int(callback_data.replace("smart_update_", ""))
            # TODO: реализовать выбор что изменить
            return RouterResult(handled=False, pass_through=True)

        return RouterResult(handled=False, pass_through=True)

    async def _confirm_delete(self, user_id: int, event_id: int) -> RouterResult:
        """Подтвердить и выполнить удаление."""
        target = TargetEvent(event_id=event_id)
        resolved = await self._entity_resolver.resolve(user_id, target)

        action_result = await self._action_executor.execute_delete(
            user_id, resolved, force=True
        )

        return self._create_response(action_result)


# =============================================================================
# Глобальный instance для удобного доступа
# =============================================================================

_smart_router: Optional[SmartRouter] = None


def get_smart_router() -> Optional[SmartRouter]:
    """Получить глобальный SmartRouter."""
    return _smart_router


def set_smart_router(router: SmartRouter) -> None:
    """Установить глобальный SmartRouter."""
    global _smart_router
    _smart_router = router


def create_smart_router(
    db,
    llm_client=None,
    nlp_extractor=None,
    decision_engine=None,
    model: str = "gpt-4o-mini"
) -> SmartRouter:
    """
    Создать и установить глобальный SmartRouter.

    Args:
        db: Database instance
        llm_client: LLM клиент
        nlp_extractor: NLP extractor
        decision_engine: Decision engine
        model: Модель для классификации

    Returns:
        Созданный SmartRouter
    """
    global _smart_router
    _smart_router = SmartRouter(
        db=db,
        llm_client=llm_client,
        nlp_extractor=nlp_extractor,
        decision_engine=decision_engine,
        model=model
    )
    return _smart_router
