"""
==============================================================================
AGENT MODULE - САМОПРОГРАММИРУЮЩЕЕСЯ ЯДРО
==============================================================================

Реализация agent-based архитектуры где LLM сам решает что делать.

Вместо жёсткого кода "if user said X then do Y" -
LLM анализирует запрос и выбирает какие инструменты использовать.

КОМПОНЕНТЫ:
    - AgentCore: главный цикл агента
    - ToolExecutor: выполнение инструментов
    - ConversationMemory: память разговора
    - TOOLS_SCHEMA: описание инструментов для LLM

ИСПОЛЬЗОВАНИЕ:
    from tracy.agent import AgentCore, create_agent

    agent = create_agent(db=db, llm_client=client)
    result = await agent.process(user_id, "встреча завтра в 15:00")

    if result.message:
        await send_message(result.message)

КАК ЭТО РАБОТАЕТ:
    1. Пользователь пишет "удали встречу с Катей"
    2. AgentCore передаёт это LLM с описанием доступных tools
    3. LLM решает: "нужно найти событие" → вызывает search_events("встреча с Катей")
    4. Получает результат: [{id: 123, title: "Встреча с Катей", ...}]
    5. LLM решает: "нужно удалить" → вызывает delete_event(123)
    6. Получает результат: {success: true}
    7. LLM решает: "нужно сообщить" → вызывает send_response("Событие удалено")
    8. AgentCore возвращает ответ пользователю

==============================================================================
"""

from tracy.agent.core import (
    AgentCore,
    AgentResult,
    AgentStatus,
    get_agent,
    set_agent,
    create_agent
)

from tracy.agent.tools import (
    TOOLS_SCHEMA,
    ToolExecutor
)

from tracy.agent.memory import (
    ConversationMemory,
    ConversationContext,
    Message,
    get_memory,
    set_memory
)

__all__ = [
    # Core
    'AgentCore',
    'AgentResult',
    'AgentStatus',
    'get_agent',
    'set_agent',
    'create_agent',

    # Tools
    'TOOLS_SCHEMA',
    'ToolExecutor',

    # Memory
    'ConversationMemory',
    'ConversationContext',
    'Message',
    'get_memory',
    'set_memory',
]
