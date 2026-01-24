"""
==============================================================================
INTELLIGENCE MODULE - УМНАЯ ОБРАБОТКА СООБЩЕНИЙ
==============================================================================

Модуль для интеллектуальной обработки сообщений пользователя с использованием AI.
Определяет намерения, находит события, выполняет действия.

КОМПОНЕНТЫ:
    - ContextExtractor: извлечение контекста из reply сообщений и истории
    - IntentClassifier: AI-классификация намерений пользователя
    - EntityResolver: поиск событий по названию/дате/ключевым словам
    - ActionExecutor: выполнение действий над событиями
    - SmartRouter: главный роутер, объединяющий все компоненты

ИСПОЛЬЗОВАНИЕ:
    from tracy.intelligence import SmartRouter

    router = SmartRouter(db, nlp_extractor)
    result = await router.process_message(update, context)

==============================================================================
"""

from tracy.intelligence.context_extractor import ContextExtractor, MessageContext
from tracy.intelligence.intent_classifier import IntentClassifier, UserIntent, IntentType
from tracy.intelligence.entity_resolver import EntityResolver, ResolvedEntity
from tracy.intelligence.action_executor import ActionExecutor, ActionResult
from tracy.intelligence.smart_router import SmartRouter, create_smart_router, get_smart_router, set_smart_router

__all__ = [
    'ContextExtractor',
    'MessageContext',
    'IntentClassifier',
    'UserIntent',
    'IntentType',
    'EntityResolver',
    'ResolvedEntity',
    'ActionExecutor',
    'ActionResult',
    'SmartRouter',
    'create_smart_router',
    'get_smart_router',
    'set_smart_router',
]
