"""
==============================================================================
CONVERSATION_HANDLER.PY - MULTI-TURN ДИАЛОГИ (УТОЧНЯЮЩИЕ ВОПРОСЫ)
==============================================================================

ОПИСАНИЕ:
    Управляет многошаговыми диалогами, когда пользователь не указал все
    необходимые данные. Задаёт уточняющие вопросы и собирает информацию
    пошагово перед выполнением действия.

ЗАВИСИМОСТИ (импортирует):
    - (нет внешних зависимостей, использует переданные объекты)

ИСПОЛЬЗУЕТСЯ В (импортируется в):
    - bot.py → conversation_handler.process_message() для обработки сообщений

КЛЮЧЕВОЙ КЛАСС: ConversationHandler

FLOW ДИАЛОГА:
    1. process_message() → Проверка состояния
    2. Если есть pending_action → _handle_answer() (ответ на вопрос)
    3. Если нет pending_action → _handle_new_action() (новый запрос)
    4. _handle_new_action():
       a) nlp._detect_missing_fields() → определение недостающих полей
       b) Если есть недостающие → memory.set_state() + вопрос
       c) Если всё есть → engine.process_intent()
    5. _handle_answer():
       a) nlp.extract_from_answer() → извлечение значения
       b) Обновление partial_data
       c) Если ещё есть недостающие → следующий вопрос
       d) Если всё собрано → engine.process_intent()

СВЯЗЬ С ДРУГИМИ МОДУЛЯМИ:
    - conversation_memory.py → хранение состояния диалога (pending_action, partial_data)
    - nlp_extractor.py → _detect_missing_fields(), generate_clarification_question()
    - decision_engine.py → process_intent() для выполнения действия

ПРИМЕР ДИАЛОГА:
    User: "Встреча завтра"
    Bot:  "Во сколько встреча?"        ← missing: start_time
    User: "В 15:00"
    Bot:  "Отлично, создал событие..." ← engine.process_intent()

==============================================================================
"""
import json
import logging
from typing import Dict, Optional

from calendar_google import GoogleCalendar
from calendar_icloud import ICloudCalendar

logger = logging.getLogger(__name__)


class ConversationHandler:
    """
    Управление многошаговыми диалогами и сбором информации.
    
    Координирует работу между NLP (определение недостающих полей),
    ConversationMemory (хранение состояния) и DecisionEngine (выполнение).
    
    Attributes:
        db: Database - инстанс базы данных
        nlp: NLPExtractor - для извлечения данных и генерации вопросов
        engine: DecisionEngine - для выполнения действий
        memory: ConversationMemory - для хранения состояния диалога
    """

    def __init__(self, db, nlp_extractor, decision_engine, conv_memory):
        """
        Инициализация обработчика диалогов.

        Args:
            db: Экземпляр Database
            nlp_extractor: Экземпляр NLPExtractor
            decision_engine: Экземпляр DecisionEngine
            conv_memory: Экземпляр ConversationMemory
        """
        self.db = db
        self.nlp = nlp_extractor
        self.engine = decision_engine
        self.memory = conv_memory

    async def process_message(
        self,
        user_id: int,
        text: str,
        extracted_data: Dict,
        last_event: Optional[Dict] = None,
        reply_to_event: Optional[Dict] = None
    ) -> Dict:
        """
        Основная точка входа для обработки сообщения с учетом контекста диалога.

        Args:
            user_id: ID пользователя
            text: Текст сообщения пользователя
            extracted_data: Данные извлеченные NLP
            last_event: Последнее событие пользователя
            reply_to_event: Событие из reply (если пользователь ответил на сообщение о событии)

        Returns:
            Словарь с результатом:
            - action: тип действия
            - message: сообщение для пользователя
            - needs_confirmation: требуется ли подтверждение
        """
        # 1. Проверяем есть ли активное состояние (ожидание ответа)
        state = self.memory.get_state(user_id)

        if state and state.get('pending_action'):
            # Это ответ на наш вопрос
            logger.info(f"💬 Обрабатываем ответ на вопрос: pending={state['pending_action']}, awaiting={state['awaiting_field']}")
            return await self._handle_answer(user_id, text, state, extracted_data, last_event, reply_to_event)
        else:
            # Новое действие
            logger.info(f"🆕 Обрабатываем новое действие: intent={extracted_data.get('intent')}, reply_to_event={reply_to_event is not None}")
            return await self._handle_new_action(user_id, extracted_data, last_event, reply_to_event)

    async def _handle_new_action(
        self,
        user_id: int,
        extracted_data: Dict,
        last_event: Optional[Dict],
        reply_to_event: Optional[Dict] = None
    ) -> Dict:
        """
        Обработка нового действия пользователя.

        Args:
            user_id: ID пользователя
            extracted_data: Извлеченные данные
            last_event: Последнее событие
            reply_to_event: Событие из reply (для операций удаления/обновления)

        Returns:
            Результат обработки
        """
        # Проверяем полноту данных
        missing_fields = self.nlp._detect_missing_fields(extracted_data)

        if missing_fields:
            # Недостающие поля - начинаем диалог уточнения
            first_missing = missing_fields[0]
            question = self.nlp.generate_clarification_question(first_missing, extracted_data)

            logger.info(f"❓ Запрашиваем недостающее поле: {first_missing}")

            # Сохраняем состояние (включая reply_to_event ID для использования позже)
            self.memory.set_state(
                user_id,
                pending_action=extracted_data['intent'],
                partial_data=extracted_data,
                awaiting_field=first_missing,
                context_event_id=reply_to_event['id'] if reply_to_event else (last_event['id'] if last_event else None)
            )

            return {
                'action': 'awaiting_input',
                'message': question,
                'needs_confirmation': False
            }
        else:
            # Все данные есть - выполняем действие
            logger.info(f"✅ Все данные собраны, выполняем действие (reply_to_event={reply_to_event is not None})")
            return await self.engine.process_intent(user_id, extracted_data, last_event=last_event, reply_to_event=reply_to_event)

    async def _handle_answer(
        self,
        user_id: int,
        text: str,
        state: Dict,
        extracted_data: Dict,
        last_event: Optional[Dict],
        reply_to_event: Optional[Dict] = None
    ) -> Dict:
        """
        Обработка ответа пользователя на уточняющий вопрос.

        Args:
            user_id: ID пользователя
            text: Ответ пользователя
            state: Текущее состояние диалога
            extracted_data: Данные из NLP (могут содержать дополнительную информацию)
            last_event: Последнее событие
            reply_to_event: Событие из reply (для операций удаления/обновления)

        Returns:
            Результат обработки
        """
        awaiting_field = state['awaiting_field']
        partial_data = state['partial_data']
        pending_action = state['pending_action']

        logger.info(f"📥 Получен ответ на поле: {awaiting_field}")

        # Извлекаем значение поля из ответа
        try:
            field_value = await self.nlp.extract_from_answer(
                text,
                awaiting_field,
                partial_data,
                user_timezone=self.db.get_user_settings(user_id).get('timezone', 'Europe/Moscow')
            )

            # Обновляем частичные данные
            partial_data.update(field_value)
            logger.info(f"✅ Извлечено значение: {field_value}")
        except Exception as e:
            logger.error(f"❌ Ошибка извлечения значения поля: {e}", exc_info=True)
            # Возвращаем ошибку с просьбой уточнить
            return {
                'action': 'error',
                'message': f"Не понял ответ. {self.nlp.generate_clarification_question(awaiting_field, partial_data)}",
                'needs_confirmation': False
            }

        # Проверяем остались ли недостающие поля
        missing_fields = self.nlp._detect_missing_fields(partial_data)

        if missing_fields:
            # Еще есть недостающие поля - спрашиваем дальше
            next_field = missing_fields[0]
            next_question = self.nlp.generate_clarification_question(next_field, partial_data)

            logger.info(f"❓ Запрашиваем следующее поле: {next_field}")

            self.memory.set_state(
                user_id,
                pending_action=pending_action,
                partial_data=partial_data,
                awaiting_field=next_field,
                context_event_id=state.get('context_event_id')
            )

            return {
                'action': 'awaiting_input',
                'message': next_question,
                'needs_confirmation': False
            }
        else:
            # Все поля собраны - выполняем действие
            logger.info(f"✅ Все поля собраны, выполняем действие: {pending_action}")

            # Очищаем состояние
            self.memory.clear_state(user_id)

            # Выполняем действие через decision_engine (передаём reply_to_event для операций с событием)
            return await self.engine.process_intent(user_id, partial_data, last_event=last_event, reply_to_event=reply_to_event)

    async def handle_delete_confirmation(
        self,
        user_id: int,
        text: str,
        candidates: list
    ) -> Dict:
        """
        Обработка подтверждения удаления при множественных совпадениях.

        Args:
            user_id: ID пользователя
            text: Ответ пользователя (номер или название)
            candidates: Список ID кандидатов на удаление

        Returns:
            Результат удаления
        """
        # Извлекаем выбор пользователя
        selection = await self.nlp.extract_from_answer(
            text, 'selection', {}, ''
        )

        selected_index = selection.get('selected_index')
        selected_text = selection.get('selected_text')

        # Определяем какое событие удалять
        if selected_index is not None and 0 <= selected_index < len(candidates):
            event_id = candidates[selected_index]
        elif selected_text:
            # Ищем по названию
            events = [self.db.get_event_by_id(eid, user_id) for eid in candidates]
            matched = [e for e in events if e and selected_text.lower() in e['title'].lower()]
            if matched:
                event_id = matched[0]['id']
            else:
                return {
                    'action': 'error',
                    'message': '❌ Не нашел совпадений. Попробуй указать номер (1, 2, 3...)'
                }
        else:
            return {
                'action': 'error',
                'message': '❌ Не понял. Укажи номер события (1, 2, 3...) или его название'
            }

        # Удаляем событие
        event = self.db.get_event_by_id(event_id, user_id)
        if not event:
            return {
                'action': 'error',
                'message': '❌ Событие не найдено'
            }

        # Удаляем из внешних календарей
        if event.get('external_id') and event.get('provider'):
            try:
                if event['provider'] == 'google':
                    calendar = GoogleCalendar(user_id)
                    calendar.delete_event(event['external_id'])
                    logger.info(f"✓ Событие удалено из Google Calendar: {event['external_id']}")
                elif event['provider'] == 'icloud':
                    # Получаем подключения календарей пользователя
                    calendar_connections = self.db.get_calendar_connections(user_id)
                    conn = next((c for c in calendar_connections if c['provider'] == 'icloud'), None)
                    if conn:
                        # Загружаем credentials из БД
                        credentials = json.loads(conn['credentials'])
                        calendar = ICloudCalendar(
                            user_id=user_id,
                            caldav_url=credentials.get('caldav_url', 'https://caldav.icloud.com'),
                            username=credentials.get('username'),
                            password=credentials.get('password')
                        )

                        calendar.delete_event(event['external_id'])
                        logger.info(f"✓ Событие удалено из iCloud Calendar: {event['external_id']}")
            except Exception as e:
                logger.error(f"Ошибка удаления из внешнего календаря: {e}")

        # Удаляем напоминания
        self.db.delete_reminders_for_event(event_id)

        # Удаляем из БД
        self.db.delete_event(event_id, user_id)

        # Очищаем состояние
        self.memory.clear_state(user_id)

        return {
            'action': 'deleted',
            'message': f"✅ Удалено: {event['title']}",
            'event_id': event_id
        }
