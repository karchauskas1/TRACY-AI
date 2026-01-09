"""Модуль логики принятия решений: создание/обновление событий, reminders, notes."""
import logging
import re
from typing import Dict, Optional, List, Tuple
from datetime import datetime, timedelta
from database import Database
from calendar_google import GoogleCalendar
from calendar_icloud import ICloudCalendar
from openai import OpenAI
import config

logger = logging.getLogger(__name__)


class DecisionEngine:
    """Движок принятия решений для действий с событиями."""
    
    def __init__(self, db: Database, reminder_scheduler=None, ai_client=None):
        self.db = db
        self.reminder_scheduler = reminder_scheduler
        # Используем переданный клиент или создаем новый
        if ai_client:
            self.ai_client = ai_client
        else:
            self.ai_client = OpenAI(
                api_key=config.OPENROUTER_API_KEY,
                base_url=config.OPENROUTER_BASE_URL
            )
    
    def _generate_smart_error_message(self, user_text: str, extracted_data: Dict, error_context: str = "") -> str:
        """
        Генерирует умное, контекстное сообщение об ошибке через AI.
        
        Args:
            user_text: Оригинальный текст пользователя
            extracted_data: Данные, извлеченные NLP
            error_context: Контекст ошибки (что именно не так)
        
        Returns:
            Понятное сообщение пользователю с объяснением проблемы
        """
        try:
            intent = extracted_data.get('intent', 'unknown')
            title = extracted_data.get('title', '')
            description = extracted_data.get('description', '')
            start_time = extracted_data.get('start_time')
            has_time = bool(start_time)
            
            # Анализируем, что именно не так
            analysis = ""
            if intent == 'unknown':
                analysis = "Не удалось понять, что вы хотите сделать."
            elif intent in ['add_reminder', 'reminder'] and not has_time and not title:
                analysis = "Вы указали время для напоминания, но не указали, о чем напомнить."
            elif intent == 'event' and not title and not description:
                analysis = "Вы указали время, но не указали, какое событие нужно создать."
            elif has_time and not title and not description:
                analysis = "Вы указали время, но не указали событие или действие."
            elif not has_time and title:
                analysis = "Вы указали событие, но не указали время."
            else:
                analysis = error_context or "Запрос неполный или неоднозначный."
            
            prompt = f"""Пользователь написал: "{user_text}"

Анализ проблемы: {analysis}

Извлеченные данные:
- Intent: {intent}
- Название: {title or 'не указано'}
- Описание: {description or 'не указано'}
- Время: {'указано' if has_time else 'не указано'}

Напиши короткое, дружелюбное сообщение пользователю на русском языке, которое:
1. Объясняет, что именно не так с его запросом
2. Дает конкретные рекомендации, как исправить запрос
3. Приводит пример правильного запроса
4. Пишется от первого лица ("Я не понял..." или "Мне нужно...")

Будь конкретным и полезным. Не используй технические термины. Максимум 3-4 предложения.

Примеры хороших ответов:
- "Я не понял, о чем нужно напомнить. Напиши, например: 'Напомни в 19:30 проветрить комнату' или 'Напомни завтра в 10 утра позвонить маме'."
- "Ты указал время (19:30), но не написал, что нужно сделать. Добавь действие, например: 'Напомни в 19:30 проветрить' или 'Напомни в 19:30 выключить свет'."
- "Я вижу событие, но не вижу времени. Укажи когда, например: 'Зарядка в 7 утра' или 'Встреча завтра в 15:00'."

Верни ТОЛЬКО текст сообщения, без дополнительных объяснений."""
            
            response = self.ai_client.chat.completions.create(
                model=config.OPENROUTER_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "Ты умный ассистент, который помогает пользователям правильно формулировать запросы. Отвечай дружелюбно и конкретно."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=200
            )
            
            message = response.choices[0].message.content.strip()
            return message
            
        except Exception as e:
            logger.error(f"Ошибка генерации умного сообщения об ошибке: {e}", exc_info=True)
            # Fallback на простое сообщение
            if not title and not description:
                return "Я не понял, что нужно сделать. Укажи событие и время, например: 'Напомни в 19:30 проветрить' или 'Зарядка завтра в 7 утра'."
            elif not has_time:
                return "Я вижу событие, но не вижу времени. Укажи когда, например: 'Зарядка в 7 утра' или 'Встреча завтра в 15:00'."
            else:
                return "Запрос неполный. Попробуй сформулировать его более подробно, указав событие и время."
    
    async def process_intent(self, user_id: int, extracted_data: Dict, last_event: Optional[Dict] = None, reply_to_event: Optional[Dict] = None) -> Dict:
        """
        Обработать intent и выполнить соответствующее действие.
        
        Args:
            user_id: ID пользователя
            extracted_data: Извлеченные данные из NLP
            last_event: Последнее событие пользователя (для контекста)
        
        Returns:
            Словарь с результатом:
            - action: 'created', 'updated', 'saved_note', 'found', etc.
            - message: сообщение для пользователя
            - event_id: ID созданного/обновленного события (если есть)
            - needs_confirmation: нужно ли подтверждение
        """
        intent = extracted_data.get('intent', 'unknown')
        original_intent = intent  # Сохраняем для логирования
        
        # КРИТИЧЕСКИ ВАЖНЫЙ FALLBACK: переопределяем intent если NLP неправильно распознал
        # Это нужно потому что NLP иногда возвращает "note" вместо правильного intent
        original_text = extracted_data.get('_original_text', '').lower().strip()
        
        # Если оригинальный текст не сохранен, используем title или description
        if not original_text:
            original_text = (extracted_data.get('title', '') or extracted_data.get('description', '')).lower().strip()
        
        # Убираем знаки препинания для более надежной проверки
        text_for_check = original_text.replace('.', '').replace(',', '').replace('!', '').replace('?', '').strip()
        
        if original_text:
            # Проверяем "удали все планы/события" - ВЫСШИЙ ПРИОРИТЕТ (переопределяем даже если NLP вернул другой intent)
            delete_all_patterns = [
                'удали все планы', 'удалить все планы', 'удали все события', 'удалить все события',
                'удали все мои события', 'удалить все мои события', 'удали все мои планы',
                'очистить все', 'удали все', 'удалить все'
            ]
            if any(phrase in text_for_check for phrase in delete_all_patterns):
                intent = 'delete_all'
                logger.warning(f"Fallback: переопределил intent '{original_intent}' → 'delete_all' из текста: '{original_text}'")
                extracted_data['intent'] = 'delete_all'
            
            # Проверяем "покажи все события/планы"
            elif any(phrase in text_for_check for phrase in [
                'покажи все события', 'покажи все мои события', 'покажи все планы',
                'покажи все дела', 'покажи все мои планы', 'покажи все мои дела'
            ]):
                intent = 'list_events'
                logger.warning(f"Fallback: переопределил intent '{original_intent}' → 'list_events' из текста: '{original_text}'")
                extracted_data['intent'] = 'list_events'
                extracted_data['time_period'] = 'all'
            
            # Проверяем "покажи события/планы" (без "все")
            elif any(phrase in text_for_check for phrase in [
                'покажи события', 'покажи планы', 'покажи дела', 'какие планы', 'что у меня', 'что запланировано'
            ]):
                intent = 'list_events'
                logger.info(f"Fallback: переопределил intent '{original_intent}' → 'list_events' из текста: '{original_text}'")
                extracted_data['intent'] = 'list_events'
                if not extracted_data.get('time_period'):
                    extracted_data['time_period'] = 'week'
            
            # Проверяем "удали все за период"
            elif any(phrase in text_for_check for phrase in ['удали все за', 'удали планы на', 'удали все на', 'удали за']):
                intent = 'delete_by_period'
                logger.warning(f"Fallback: переопределил intent '{original_intent}' → 'delete_by_period' из текста: '{original_text}'")
                extracted_data['intent'] = 'delete_by_period'
            
            # Проверяем показ заметок (не событий!)
            elif any(phrase in text_for_check for phrase in ['покажи заметки', 'покажи все заметки', 'что в заметках', 'список заметок']):
                intent = 'list_notes'
                logger.info(f"Fallback: переопределил intent '{original_intent}' → 'list_notes' из текста: '{original_text}'")
                extracted_data['intent'] = 'list_notes'
        
        # КРИТИЧЕСКИ ВАЖНЫЙ FALLBACK: Умная логика определения событий на основе контекста
        # Если AI не распознал событие, но есть признаки события - переопределяем intent
        
        start_time = extracted_data.get('start_time')
        title = extracted_data.get('title', '') or extracted_data.get('description', '')
        has_explicit_time = extracted_data.get('has_explicit_time', False)
        
        # Проверяем наличие времени в формате ЧЧ:ММ (например, "14:00", "в 14:00", "14.00", "в 14")
        time_pattern = r'\b(\d{1,2}[:.]\d{2}|\d{1,2}\s*(?:час|часа|часов|утра|дня|вечера|ночи)|в\s*\d{1,2})\b'
        has_time_format = bool(re.search(time_pattern, original_text, re.IGNORECASE)) if original_text else False
        
        # Проверяем наличие дат/времени в тексте (расширенный список)
        time_keywords = [
            'сегодня', 'завтра', 'послезавтра', 'вчера',
            'в', 'во', 'утра', 'дня', 'вечера', 'ночи', 'час', 'часа', 'часов', 
            'понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота', 'воскресенье',
            'января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 
            'октября', 'ноября', 'декабря'
        ]
        
        has_time_in_text = any(keyword in original_text for keyword in time_keywords) if original_text else False
        
        # Проверяем наличие слова "напомни" + время + действие
        has_remind_word = any(word in original_text for word in ['напомни', 'напомнить', 'напоминание', 'напоминать'])
        has_action = bool(title and len(title.strip()) > 0)
        
        # Объединяем все признаки времени
        has_any_time = start_time or has_time_in_text or has_time_format
        
        # ЛОГИКА: Если есть время + действие, или "напомни" + время + действие → это событие!
        should_be_event = False
        reason = ""
        
        if intent == 'note' and has_any_time:
            should_be_event = True
            reason = "intent='note' но есть дата/время"
        
        elif intent in ['reminder', 'add_reminder'] and has_any_time and has_action:
            # Если intent "reminder" или "add_reminder", но есть конкретное время события - это событие!
            should_be_event = True
            reason = f"intent='{intent}' но есть время + действие (создаем событие, а не добавляем напоминание к существующему)"
        
        elif has_remind_word and has_any_time and has_action:
            # Если есть "напомни" + время + действие - это событие!
            should_be_event = True
            reason = "найдено 'напомни' + время + действие"
        
        elif has_any_time and has_action and intent not in ['list_events', 'delete', 'update', 'search', 'delete_all', 'delete_by_period', 'delete_many', 'delete_by_pattern', 'update_many']:
            # Если есть время + действие, и это не команда управления - это событие!
            should_be_event = True
            reason = f"есть время + действие (логика AI, intent был '{intent}')"
        
        elif intent == 'unknown' and has_any_time and has_action:
            # Если intent unknown, но есть время + действие - это событие!
            should_be_event = True
            reason = "intent='unknown' но есть время + действие"
        
        if should_be_event:
            intent = 'event'
            extracted_data['intent'] = 'event'
            extracted_data['has_explicit_time'] = bool(start_time)
            # Если title пустой, но есть description - используем description как title
            if not extracted_data.get('title') and extracted_data.get('description'):
                extracted_data['title'] = extracted_data['description']
                extracted_data['description'] = None
            logger.warning(f"✅ Fallback: переопределил intent '{original_intent}' → 'event' ({reason}). Текст: '{original_text}'")
        
        # Если это reply к событию и intent="note" - переопределяем на "add_note"
        if reply_to_event and intent == 'note':
            intent = 'add_note'
            logger.info(f"Переопределил intent 'note' → 'add_note' (reply к событию)")
            extracted_data['intent'] = 'add_note'
            extracted_data['refers_to_last_event'] = True
        
        # Получить настройки пользователя
        user = self.db.get_or_create_user(user_id)
        timezone = user.get('timezone', 'Europe/Moscow')
        
        # Получить подключенные календари
        calendar_connections = self.db.get_calendar_connections(user_id)
        
        if intent == 'list_events':
            return await self._handle_list_events(user_id, extracted_data, calendar_connections, timezone)
        elif intent == 'delete_all':
            return await self._handle_delete_all(user_id, calendar_connections)
        elif intent == 'delete_by_period':
            return await self._handle_delete_by_period(user_id, extracted_data, calendar_connections, timezone)
        elif intent == 'delete_many':
            return await self._handle_delete_many(user_id, extracted_data, calendar_connections)
        elif intent == 'delete_by_pattern':
            return await self._handle_delete_by_pattern(user_id, extracted_data, calendar_connections)
        elif intent == 'add_reminder':
            return await self._handle_add_reminder(user_id, extracted_data, calendar_connections, timezone, last_event)
        elif intent == 'add_note':
            # Используем reply_to_event если есть, иначе last_event
            target_event_for_note = reply_to_event if reply_to_event else last_event
            return await self._handle_add_note(user_id, extracted_data, calendar_connections, timezone, target_event_for_note)
        elif intent == 'create_many':
            return await self._handle_create_many(user_id, extracted_data, calendar_connections, timezone)
        elif intent == 'event':
            return await self._handle_event(user_id, extracted_data, calendar_connections, timezone)
        elif intent == 'reminder':
            return await self._handle_reminder(user_id, extracted_data, calendar_connections, timezone)
        elif intent == 'note':
            return await self._handle_note(user_id, extracted_data)
        elif intent == 'update':
            return await self._handle_update(user_id, extracted_data, calendar_connections, timezone)
        elif intent == 'update_many':
            return await self._handle_update_many(user_id, extracted_data, calendar_connections, timezone)
        elif intent == 'delete':
            return await self._handle_delete(user_id, extracted_data, calendar_connections)
        elif intent == 'search':
            return await self._handle_search(user_id, extracted_data, calendar_connections)
        elif intent == 'list_notes':
            return await self._handle_list_notes(user_id)
        elif intent == 'delete_note':
            return await self._handle_delete_note(user_id, extracted_data)
        else:
            # Неизвестный intent - сохраняем как заметку
            return await self._handle_note(user_id, extracted_data)
    
    async def _handle_event(self, user_id: int, extracted_data: Dict,
                           calendar_connections: List[Dict], timezone: str) -> Dict:
        """Обработать создание/обновление события."""
        title = extracted_data.get('title', 'Без названия')
        start_time = extracted_data.get('start_time')
        has_explicit_time = extracted_data.get('has_explicit_time', False)
        
        # Дедупликация: проверяем похожие события
        similar_events = self.db.find_similar_events(
            user_id, title, start_time, days_window=7
        )
        
        # Если нашли похожее событие и есть время - обновляем
        if similar_events and start_time:
            best_match = similar_events[0]
            return await self._update_existing_event(
                user_id, best_match, extracted_data, calendar_connections, timezone
            )
        
        # Если нет времени или низкая уверенность - создаем draft
        if not has_explicit_time or extracted_data.get('confidence', 0) < 0.7:
            # Сохраняем как draft в БД
            event_id = self.db.save_event(
                user_id=user_id,
                title=title,
                description=extracted_data.get('description'),
                start_time=start_time,
                end_time=extracted_data.get('end_time'),
                location=extracted_data.get('location'),
                priority=extracted_data.get('priority', 0),
                status='needs_confirmation'
            )
            
            # Используем тот же формат, но с пометкой о черновике
            message = self._format_event_confirmation(
                title=title,
                start_time=start_time,
                location=extracted_data.get('location'),
                description=extracted_data.get('description'),
                timezone=timezone,
                is_reminder=False
            )
            message += "\n\n⚠️ Требуется подтверждение (время не указано явно)"
            
            return {
                'action': 'created_draft',
                'message': message,
                'event_id': event_id,
                'needs_confirmation': True
            }
        
        # Создаем событие в календарях
        created_in = []
        
        for conn in calendar_connections:
            provider = conn['provider']
            calendar_id = conn['calendar_id']
            
            try:
                if provider == 'google':
                    calendar = GoogleCalendar(user_id)
                    google_event = calendar.create_event(
                        title=title,
                        description=extracted_data.get('description'),
                        start_time=start_time,
                        end_time=extracted_data.get('end_time'),
                        location=extracted_data.get('location'),
                        timezone=timezone
                    )
                    
                    if google_event:
                        external_id = google_event.get('id')
                        # Сохраняем в БД
                        db_event_id = self.db.save_event(
                            user_id=user_id,
                            title=title,
                            description=extracted_data.get('description'),
                            start_time=start_time,
                            end_time=extracted_data.get('end_time'),
                            location=extracted_data.get('location'),
                            priority=extracted_data.get('priority', 0),
                            external_id=external_id,
                            provider='google',
                            status='confirmed'
                        )
                        created_in.append('Google Calendar')
                
                elif provider == 'icloud':
                    # Загружаем credentials из БД
                    import json
                    credentials = json.loads(conn['credentials'])
                    calendar = ICloudCalendar(
                        user_id=user_id,
                        caldav_url=credentials.get('caldav_url', 'https://caldav.icloud.com'),
                        username=credentials.get('username'),
                        password=credentials.get('password')
                    )
                    
                    event_uid = calendar.create_event(
                        title=title,
                        description=extracted_data.get('description'),
                        start_time=start_time,
                        end_time=extracted_data.get('end_time'),
                        location=extracted_data.get('location')
                    )
                    
                    if event_uid:
                        db_event_id = self.db.save_event(
                            user_id=user_id,
                            title=title,
                            description=extracted_data.get('description'),
                            start_time=start_time,
                            end_time=extracted_data.get('end_time'),
                            location=extracted_data.get('location'),
                            priority=extracted_data.get('priority', 0),
                            external_id=event_uid,
                            provider='icloud',
                            status='confirmed'
                        )
                        created_in.append('iCloud Calendar')
            
            except Exception as e:
                logger.error(f"Ошибка создания события в {provider}: {e}")
                continue
        
        if created_in:
            # Форматируем сообщение в новом стиле
            event_id = db_event_id if 'db_event_id' in locals() else None
            message = self._format_event_confirmation(
                title=title,
                start_time=start_time,
                location=extracted_data.get('location'),
                description=extracted_data.get('description'),
                timezone=timezone,
                is_reminder=False
            )
            
            # Сохраняем последнее событие в контекст
            if event_id:
                self.db.update_last_event_context(user_id, event_id)
                
                # Создаем напоминания для события (за 15 минут по умолчанию)
                if start_time and self.reminder_scheduler:
                    try:
                        import pytz
                        # Убеждаемся, что start_time в правильном часовом поясе
                        if start_time.tzinfo is None:
                            start_time_local = pytz.timezone(timezone).localize(start_time)
                        else:
                            start_time_local = start_time
                        
                        # Конвертируем в UTC для единообразия (create_reminders_for_event ожидает UTC)
                        start_time_utc = start_time_local.astimezone(pytz.UTC)
                        
                        # Создаем напоминания: за 15 минут и в момент начала
                        self.reminder_scheduler.create_reminders_for_event(
                            user_id=user_id,
                            event_id=event_id,
                            event_start_time=start_time_utc,
                            reminder_minutes=[15]  # По умолчанию за 15 минут
                        )
                        logger.info(f"✓ Созданы напоминания для события {event_id} (start_time: {start_time_utc.isoformat()})")
                    except Exception as e:
                        logger.error(f"❌ Ошибка создания напоминаний для события {event_id}: {e}", exc_info=True)
            
            return {
                'action': 'created',
                'message': message,
                'event_id': event_id,
                'needs_confirmation': False
            }
        else:
            # Если не удалось создать в календарях, сохраняем в БД
            event_id = self.db.save_event(
                user_id=user_id,
                title=title,
                description=extracted_data.get('description'),
                start_time=start_time,
                end_time=extracted_data.get('end_time'),
                location=extracted_data.get('location'),
                priority=extracted_data.get('priority', 0),
                status='draft'
            )
            
            return {
                'action': 'created_draft',
                'message': f"Событие сохранено локально (календари не подключены): {title}",
                'event_id': event_id,
                'needs_confirmation': True
            }
    
    async def _handle_reminder(self, user_id: int, extracted_data: Dict,
                              calendar_connections: List[Dict], timezone: str) -> Dict:
        """Обработать создание напоминания (аналогично событию, но с пометкой)."""
        # Напоминание обрабатываем как событие
        result = await self._handle_event(user_id, extracted_data, calendar_connections, timezone)
        
        # Если событие создано, обновляем формат сообщения для напоминания
        if result.get('action') == 'created' and result.get('message'):
            # Форматируем заново с is_reminder=True
            title = extracted_data.get('title', 'Напоминание')
            start_time = extracted_data.get('start_time')
            message = self._format_event_confirmation(
                title=title,
                start_time=start_time,
                location=extracted_data.get('location'),
                description=extracted_data.get('description'),
                timezone=timezone,
                is_reminder=True
            )
            result['message'] = message
        
        return result
    
    async def _handle_add_reminder(self, user_id: int, extracted_data: Dict,
                                   calendar_connections: List[Dict], timezone: str,
                                   last_event: Optional[Dict] = None) -> Dict:
        """Обработать добавление напоминаний к существующему событию."""
        # Определяем, к какому событию добавлять напоминания
        target_event = None
        
        # Если явно указано событие в тексте, ищем его
        title_hint = extracted_data.get('title')
        if title_hint and not extracted_data.get('refers_to_last_event', True):
            similar_events = self.db.find_similar_events(user_id, title_hint)
            if len(similar_events) > 1:
                # Несколько похожих событий - используем последнее из них по умолчанию
                # (можно в будущем добавить уточнение через кнопки)
                logger.info(f"Найдено несколько похожих событий, используем последнее: {similar_events[0]['title']}")
                target_event = similar_events[0]
            elif similar_events:
                target_event = similar_events[0]
        
        # Если не нашли и есть последнее событие, используем его
        if not target_event and last_event:
            target_event = last_event
        elif not target_event:
            # Ищем последнее событие пользователя
            events = self.db.get_events(user_id, limit=1)
            if events:
                target_event = events[0]
        
        if not target_event:
            original_text = extracted_data.get('_original_text', '')
            error_message = self._generate_smart_error_message(
                original_text, extracted_data,
                "Попытка добавить напоминание к событию, но событие не найдено. Нужно сначала создать событие."
            )
            return {
                'action': 'error',
                'message': error_message,
                'needs_confirmation': False
            }
        
        # Получаем интервалы напоминаний
        reminder_intervals = extracted_data.get('reminder_intervals', [])
        if not reminder_intervals or (isinstance(reminder_intervals, list) and len(reminder_intervals) == 0):
            # Парсим из текста - ищем все упоминания интервалов
            description = extracted_data.get('description', '') or extracted_data.get('title', '')
            import re
            # Ищем паттерны типа "за 2 часа", "за час", "за 30 минут", "за 15 минут", "за день", "за 12 часов"
            intervals = re.findall(r'за\s+(\d+)?\s*(час|часа|часов|мин|минут|минуты|день|дня|дней|часа?)?', description.lower())
            reminder_intervals = []
            for match in intervals:
                num_str, unit = match
                # Если число не указано, предполагаем 1 (например, "за час" = 1 час)
                num = int(num_str) if num_str else 1
                
                # Определяем единицу измерения
                if not unit or unit.startswith('час'):
                    reminder_intervals.append(f"{num} hours")
                elif unit.startswith('мин'):
                    reminder_intervals.append(f"{num} minutes")
                elif unit.startswith('день'):
                    reminder_intervals.append(f"{num} days")
                else:
                    # По умолчанию считаем часами
                    reminder_intervals.append(f"{num} hours")
            
            # Если все еще не нашли интервалы, пробуем другой паттерн
            if not reminder_intervals:
                # Ищем паттерны типа "2 часа", "30 минут", "1 день" (без "за")
                intervals = re.findall(r'(\d+)\s*(час|часа|часов|мин|минут|минуты|день|дня|дней)', description.lower())
                for num_str, unit in intervals:
                    num = int(num_str)
                    if unit.startswith('час'):
                        reminder_intervals.append(f"{num} hours")
                    elif unit.startswith('мин'):
                        reminder_intervals.append(f"{num} minutes")
                    elif unit.startswith('день'):
                        reminder_intervals.append(f"{num} days")
        
        # Добавляем напоминания к событию в календаре
        event_id = target_event['id']
        external_id = target_event.get('external_id')
        provider = target_event.get('provider')
        
        added_reminders = []
        if external_id and provider and reminder_intervals:
            try:
                if provider == 'google':
                    calendar = GoogleCalendar(user_id)
                    # Получаем существующее событие, чтобы сохранить текущие напоминания
                    service = calendar.get_service()
                    existing_event = service.events().get(
                        calendarId='primary',
                        eventId=external_id
                    ).execute()
                    
                    # Получаем существующие напоминания
                    existing_reminders = existing_event.get('reminders', {}).get('overrides', [])
                    if not existing_reminders:
                        existing_reminders = []
                    
                    # Добавляем новые напоминания
                    new_reminders = existing_reminders.copy() if existing_reminders else []
                    for interval in reminder_intervals:
                        # Парсим интервал (например, "2 hours" -> 120 минут)
                        import re
                        match = re.match(r'(\d+)\s*(hour|hours|minute|minutes|day|days)', interval.lower())
                        if match:
                            num = int(match.group(1))
                            unit = match.group(2)
                            if unit.startswith('hour'):
                                minutes = num * 60
                                unit_display = f"{num} час" + ("а" if num == 2 or num == 3 or num == 4 else "" if num == 1 else "ов")
                            elif unit.startswith('minute'):
                                minutes = num
                                unit_display = f"{num} минут" + ("" if num == 1 else ("а" if num == 2 or num == 3 or num == 4 else ""))
                            elif unit.startswith('day'):
                                minutes = num * 24 * 60
                                unit_display = f"{num} день" + ("я" if num == 2 or num == 3 or num == 4 else "" if num == 1 else "ей")
                            else:
                                minutes = 15  # по умолчанию
                                unit_display = "15 минут"
                            
                            # Проверяем, нет ли уже такого напоминания
                            if not any(r.get('minutes') == minutes for r in new_reminders):
                                new_reminders.append({'method': 'popup', 'minutes': minutes})
                                added_reminders.append(unit_display)
                    
                    # Обновляем событие с объединенными напоминаниями
                    if new_reminders:
                        calendar.update_event(external_id, reminders=new_reminders)
                
                elif provider == 'icloud':
                    # iCloud через CalDAV поддерживает несколько напоминаний
                    conn = next((c for c in calendar_connections if c['provider'] == 'icloud'), None)
                    if conn:
                        import json
                        credentials = json.loads(conn['credentials'])
                        calendar = ICloudCalendar(
                            user_id=user_id,
                            caldav_url=credentials.get('caldav_url'),
                            username=credentials.get('username'),
                            password=credentials.get('password')
                        )
                        
                        # Формируем список для отображения пользователю
                        for interval in reminder_intervals:
                            import re
                            match = re.match(r'(\d+)\s*(hour|hours|minute|minutes|day|days)', interval.lower())
                            if match:
                                num = int(match.group(1))
                                unit = match.group(2)
                                if unit.startswith('hour'):
                                    unit_display = f"{num} час" + ("а" if 2 <= num <= 4 else "" if num == 1 else "ов")
                                elif unit.startswith('minute'):
                                    unit_display = f"{num} минут" + ("" if num == 1 else ("а" if 2 <= num <= 4 else ""))
                                elif unit.startswith('day'):
                                    unit_display = f"{num} день" + ("я" if 2 <= num <= 4 else "" if num == 1 else "ей")
                                else:
                                    unit_display = f"{num} {unit}"
                                added_reminders.append(unit_display)
                        
                        # Добавляем напоминания через обновление события
                        calendar.add_reminders_to_event(external_id, reminder_intervals)
            except Exception as e:
                logger.error(f"Ошибка добавления напоминаний: {e}")
        
        # Создаем напоминания в БД через scheduler, если он доступен
        if self.reminder_scheduler and target_event.get('start_time'):
            try:
                import pytz
                event_start_str = target_event.get('start_time')
                if isinstance(event_start_str, str):
                    event_start_time = datetime.fromisoformat(event_start_str.replace('Z', '+00:00'))
                else:
                    event_start_time = event_start_str
                
                # Конвертируем reminder_intervals в минуты
                reminder_minutes = []
                import re
                for interval in reminder_intervals:
                    match = re.match(r'(\d+)\s*(hour|hours|minute|minutes|day|days)', interval.lower())
                    if match:
                        num = int(match.group(1))
                        unit = match.group(2)
                        if unit.startswith('hour'):
                            reminder_minutes.append(num * 60)
                        elif unit.startswith('minute'):
                            reminder_minutes.append(num)
                        elif unit.startswith('day'):
                            reminder_minutes.append(num * 24 * 60)
                
                # Создаем напоминания в БД
                if reminder_minutes:
                    import pytz
                    # Убеждаемся, что event_start_time в правильном часовом поясе и конвертируем в UTC
                    if event_start_time.tzinfo is None:
                        event_start_time = pytz.timezone(timezone).localize(event_start_time)
                    # Конвертируем в UTC для единообразия
                    event_start_time_utc = event_start_time.astimezone(pytz.UTC)
                    
                    self.reminder_scheduler.create_reminders_for_event(
                        user_id=user_id,
                        event_id=event_id,
                        event_start_time=event_start_time_utc,
                        reminder_minutes=reminder_minutes
                    )
                    logger.info(f"Созданы напоминания в БД для события {event_id}: {reminder_minutes} минут")
            except Exception as e:
                logger.error(f"Ошибка создания напоминаний в БД: {e}", exc_info=True)
        
        # Обновляем последнее событие в контексте
        self.db.update_last_event_context(user_id, event_id)
        
        # Форматируем ответ в новом стиле
        event_title = target_event.get('title', 'Событие')
        event_start = target_event.get('start_time')
        
        if added_reminders:
            message = f"🔔 Напоминания добавлены\n"
            message += f"📅 {event_title}\n"
            
            if event_start:
                try:
                    from datetime import datetime
                    if isinstance(event_start, str):
                        start_dt = datetime.fromisoformat(event_start.replace('Z', '+00:00'))
                    else:
                        start_dt = event_start
                    import pytz
                    tz = pytz.timezone(timezone)
                    if start_dt.tzinfo is None:
                        start_dt = tz.localize(start_dt)
                    else:
                        start_dt = start_dt.astimezone(tz)
                    
                    weekdays_short = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
                    weekday = weekdays_short[start_dt.weekday()]
                    months = ['январь', 'февраль', 'март', 'апрель', 'май', 'июнь',
                             'июль', 'август', 'сентябрь', 'октябрь', 'ноябрь', 'декабрь']
                    month = months[start_dt.month - 1]
                    message += f" · Дата: ({weekday}) {start_dt.day} {month}\n"
                    message += f" · Время: {start_dt.strftime('%H:%M')}\n"
                except Exception:
                    pass
            
            message += " · Напоминания:\n"
            for reminder in added_reminders:
                message += f"   - За {reminder}\n"
        else:
            message = f"✓ Напоминание добавлено к событию «{event_title}»"
        
        return {
            'action': 'reminder_added',
            'message': message,
            'event_id': event_id,
            'needs_confirmation': False
        }
    
    async def _handle_add_note(self, user_id: int, extracted_data: Dict,
                               calendar_connections: List[Dict], timezone: str,
                               last_event: Optional[Dict] = None) -> Dict:
        """Обработать добавление заметки к существующему событию."""
        # Определяем событие (аналогично _handle_add_reminder)
        target_event = None
        
        title_hint = extracted_data.get('title')
        if title_hint and not extracted_data.get('refers_to_last_event', True):
            similar_events = self.db.find_similar_events(user_id, title_hint)
            if len(similar_events) > 1:
                # Несколько похожих событий - используем последнее
                logger.info(f"Найдено несколько похожих событий, используем последнее: {similar_events[0]['title']}")
                target_event = similar_events[0]
            elif similar_events:
                target_event = similar_events[0]
        
        if not target_event and last_event:
            target_event = last_event
        elif not target_event:
            events = self.db.get_events(user_id, limit=1)
            if events:
                target_event = events[0]
        
        if not target_event:
            original_text = extracted_data.get('_original_text', '')
            error_message = self._generate_smart_error_message(
                original_text, extracted_data,
                "Попытка добавить заметку к событию, но событие не найдено. Нужно сначала создать событие или указать конкретное событие."
            )
            return {
                'action': 'error',
                'message': error_message,
                'needs_confirmation': False
            }
        
        # Получаем текст заметки
        note_text = extracted_data.get('note_text') or extracted_data.get('description', '') or extracted_data.get('_original_text', '')
        
        # Если текст заметки все еще пустой, используем title
        if not note_text or not note_text.strip():
            note_text = extracted_data.get('title', '')
        
        if not note_text or not note_text.strip():
            original_text = extracted_data.get('_original_text', '')
            error_message = self._generate_smart_error_message(
                original_text, extracted_data,
                "Попытка добавить заметку, но текст заметки не указан."
            )
            return {
                'action': 'error',
                'message': error_message,
                'needs_confirmation': False
            }
        
        # Обновляем описание события
        event_id = target_event['id']
        current_description = target_event.get('description') or ''
        new_description = f"{current_description}\n\n{note_text}".strip() if current_description else note_text
        
        # Обновляем в БД
        self.db.update_event(event_id, description=new_description)
        
        # Обновляем в календаре
        external_id = target_event.get('external_id')
        provider = target_event.get('provider')
        if external_id and provider:
            try:
                if provider == 'google':
                    calendar = GoogleCalendar(user_id)
                    calendar.update_event(external_id, description=new_description)
                elif provider == 'icloud':
                    conn = next((c for c in calendar_connections if c['provider'] == 'icloud'), None)
                    if conn:
                        import json
                        credentials = json.loads(conn['credentials'])
                        calendar = ICloudCalendar(
                            user_id=user_id,
                            caldav_url=credentials.get('caldav_url'),
                            username=credentials.get('username'),
                            password=credentials.get('password')
                        )
                        calendar.update_event(external_id, description=new_description)
            except Exception as e:
                logger.error(f"Ошибка обновления заметки в календаре: {e}")
        
        # Обновляем контекст
        self.db.update_last_event_context(user_id, event_id)
        
        return {
            'action': 'note_added',
            'message': f"✓ Заметка добавлена к событию «{target_event['title']}»:\n{note_text[:100]}{'...' if len(note_text) > 100 else ''}",
            'event_id': event_id,
            'needs_confirmation': False
        }
    
    async def _handle_note(self, user_id: int, extracted_data: Dict) -> Dict:
        """Обработать сохранение заметки."""
        content = extracted_data.get('description') or extracted_data.get('title', '')
        
        note_id = self.db.save_note(user_id, content, extracted_data)
        
        return {
            'action': 'saved_note',
            'message': f"✓ Сохранена заметка: {content[:50]}...",
            'note_id': note_id,
            'needs_confirmation': False
        }
    
    async def _handle_update(self, user_id: int, extracted_data: Dict,
                            calendar_connections: List[Dict], timezone: str) -> Dict:
        """Обработать обновление существующего события."""
        # Ищем событие для обновления
        title = extracted_data.get('title', '')
        similar_events = self.db.find_similar_events(user_id, title)
        
        if not similar_events:
            return {
                'action': 'not_found',
                'message': f"Событие '{title}' не найдено для обновления.",
                'needs_confirmation': False
            }
        
        return await self._update_existing_event(
            user_id, similar_events[0], extracted_data, calendar_connections, timezone
        )
    
    async def _update_existing_event(self, user_id: int, event: Dict, extracted_data: Dict,
                                    calendar_connections: List[Dict], timezone: str) -> Dict:
        """Обновить существующее событие."""
        event_id = event['id']
        external_id = event.get('external_id')
        provider = event.get('provider')
        
        # Обновляем в БД
        updates = {}
        if 'title' in extracted_data:
            updates['title'] = extracted_data['title']
        if 'description' in extracted_data:
            updates['description'] = extracted_data['description']
        if 'start_time' in extracted_data:
            updates['start_time'] = extracted_data['start_time']
        if 'end_time' in extracted_data:
            updates['end_time'] = extracted_data['end_time']
        if 'location' in extracted_data:
            updates['location'] = extracted_data['location']
        
        self.db.update_event(event_id, **updates)
        
        # Обновляем в календаре
        if external_id and provider:
            try:
                if provider == 'google':
                    calendar = GoogleCalendar(user_id)
                    calendar.update_event(external_id, **updates, timezone=timezone)
                elif provider == 'icloud':
                    conn = next((c for c in calendar_connections if c['provider'] == 'icloud'), None)
                    if conn:
                        import json
                        credentials = json.loads(conn['credentials'])
                        calendar = ICloudCalendar(
                            user_id=user_id,
                            caldav_url=credentials.get('caldav_url'),
                            username=credentials.get('username'),
                            password=credentials.get('password')
                        )
                        calendar.update_event(external_id, **updates)
            except Exception as e:
                logger.error(f"Ошибка обновления события в календаре: {e}")
        
        # Форматируем сообщение в новом стиле
        updated_title = updates.get('title', event.get('title', 'Событие'))
        updated_start_time = updates.get('start_time')
        if updated_start_time and isinstance(updated_start_time, str):
            from datetime import datetime
            updated_start_time = datetime.fromisoformat(updated_start_time)
        elif not updated_start_time:
            # Берем из события
            if event.get('start_time'):
                from datetime import datetime
                updated_start_time = datetime.fromisoformat(event['start_time'])
        
        message = self._format_event_confirmation(
            title=updated_title,
            start_time=updated_start_time,
            location=updates.get('location') or event.get('location'),
            description=updates.get('description') or event.get('description'),
            timezone=timezone,
            is_reminder='🔔' in updated_title or '🔔' in str(event.get('title', ''))
        )
        # Заменяем "Добавлен" на "Обновлен" если нужно (но нового формата это уже не требуется)
        # Убираем старый формат, так как теперь используем новый
        
        # Обновляем контекст последнего события
        self.db.update_last_event_context(user_id, event_id)
        
        return {
            'action': 'updated',
            'message': message,
            'event_id': event_id,
            'needs_confirmation': False
        }
    
    async def _handle_delete_all(self, user_id: int, calendar_connections: List[Dict]) -> Dict:
        """Обработать удаление всех событий."""
        # Сначала получаем список событий БЕЗ удаления из БД
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, external_id, provider FROM events WHERE user_id = ?", (user_id,))
        events = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        # Удаляем из календарей ПЕРЕД удалением из БД
        deleted_from_calendars = 0
        for event in events:
            external_id = event.get('external_id')
            provider = event.get('provider')
            event_id = event.get('id')
            
            # Удаляем напоминания для события
            if event_id:
                try:
                    self.db.delete_reminders_for_event(event_id)
                except Exception as e:
                    logger.error(f"Ошибка удаления напоминаний для события {event_id}: {e}")
            
            # Удаляем из календарей
            if external_id and provider:
                try:
                    if provider == 'google':
                        calendar = GoogleCalendar(user_id)
                        if calendar.delete_event(external_id):
                            deleted_from_calendars += 1
                            logger.info(f"Удалено событие {external_id} из Google Calendar")
                    elif provider == 'icloud':
                        conn = next((c for c in calendar_connections if c['provider'] == 'icloud'), None)
                        if conn:
                            import json
                            credentials = json.loads(conn['credentials'])
                            calendar = ICloudCalendar(
                                user_id=user_id,
                                caldav_url=credentials.get('caldav_url'),
                                username=credentials.get('username'),
                                password=credentials.get('password')
                            )
                            if calendar.delete_event(external_id):
                                deleted_from_calendars += 1
                                logger.info(f"Удалено событие {external_id} из iCloud Calendar")
                except Exception as e:
                    logger.error(f"Ошибка удаления события {external_id} из календаря {provider}: {e}", exc_info=True)
        
        # Теперь удаляем из БД
        deleted_count, _ = self.db.delete_all_events(user_id)
        
        return {
            'action': 'deleted_all',
            'message': f"✓ Удалено всех событий: {deleted_count} (из календарей: {deleted_from_calendars})",
            'needs_confirmation': False
        }
    
    async def _handle_delete_by_period(self, user_id: int, extracted_data: Dict,
                                      calendar_connections: List[Dict], timezone: str) -> Dict:
        """Обработать удаление событий за период."""
        from datetime import timedelta
        import pytz
        
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)
        
        time_period = extracted_data.get('time_period', 'week')
        
        # Вычисляем диапазон дат
        if time_period == 'today':
            start_from = now.replace(hour=0, minute=0, second=0, microsecond=0)
            start_to = now.replace(hour=23, minute=59, second=59, microsecond=999999)
            period_name = "сегодня"
        elif time_period == 'tomorrow':
            start_from = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            start_to = (now + timedelta(days=1)).replace(hour=23, minute=59, second=59, microsecond=999999)
            period_name = "завтра"
        elif time_period == 'week':
            start_from = now.replace(hour=0, minute=0, second=0, microsecond=0)
            start_to = now + timedelta(days=7)
            period_name = "неделю"
        elif time_period == 'month':
            start_from = now.replace(hour=0, minute=0, second=0, microsecond=0)
            start_to = now + timedelta(days=30)
            period_name = "месяц"
        else:
            start_from = now.replace(hour=0, minute=0, second=0, microsecond=0)
            start_to = now + timedelta(days=7)
            period_name = "неделю"
        
        # Сначала получаем список событий БЕЗ удаления из БД
        events = self.db.get_events(user_id, start_from=start_from, start_to=start_to)
        
        # Удаляем из календарей ПЕРЕД удалением из БД
        deleted_from_calendars = 0
        for event in events:
            external_id = event.get('external_id')
            provider = event.get('provider')
            event_id = event.get('id')
            
            # Удаляем напоминания для события
            if event_id:
                try:
                    self.db.delete_reminders_for_event(event_id)
                except Exception as e:
                    logger.error(f"Ошибка удаления напоминаний для события {event_id}: {e}")
            
            # Удаляем из календарей
            if external_id and provider:
                try:
                    if provider == 'google':
                        calendar = GoogleCalendar(user_id)
                        if calendar.delete_event(external_id):
                            deleted_from_calendars += 1
                            logger.info(f"Удалено событие {external_id} из Google Calendar")
                    elif provider == 'icloud':
                        conn = next((c for c in calendar_connections if c['provider'] == 'icloud'), None)
                        if conn:
                            import json
                            credentials = json.loads(conn['credentials'])
                            calendar = ICloudCalendar(
                                user_id=user_id,
                                caldav_url=credentials.get('caldav_url'),
                                username=credentials.get('username'),
                                password=credentials.get('password')
                            )
                            if calendar.delete_event(external_id):
                                deleted_from_calendars += 1
                                logger.info(f"Удалено событие {external_id} из iCloud Calendar")
                except Exception as e:
                    logger.error(f"Ошибка удаления события {external_id} из календаря {provider}: {e}", exc_info=True)
        
        # Теперь удаляем из БД по конкретным ID
        event_ids = [e['id'] for e in events]
        if event_ids:
            deleted_count, _ = self.db.delete_events_by_ids(user_id, event_ids)
        else:
            deleted_count = 0
        
        if deleted_count == 0:
            return {
                'action': 'nothing_to_delete',
                'message': f"На {period_name} нет событий для удаления.",
                'needs_confirmation': False
            }
        
        return {
            'action': 'deleted_by_period',
            'message': f"✓ Удалено событий за {period_name}: {deleted_count} (из календарей: {deleted_from_calendars})",
            'needs_confirmation': False
        }
    
    async def _handle_delete_many(self, user_id: int, extracted_data: Dict,
                                  calendar_connections: List[Dict]) -> Dict:
        """Обработать удаление нескольких событий."""
        titles = extracted_data.get('titles', [])
        if not titles:
            # Пытаемся извлечь из title, если это строка с несколькими названиями
            title_str = extracted_data.get('title', '')
            if title_str:
                # Простой парсинг: "встреча и презентация" -> ["встреча", "презентация"]
                import re
                titles = [t.strip() for t in re.split(r'[и,]', title_str) if t.strip()]
        
        if not titles:
            original_text = extracted_data.get('_original_text', '')
            error_message = self._generate_smart_error_message(
                original_text, extracted_data,
                "Попытка удалить несколько событий, но события не указаны."
            )
            return {
                'action': 'error',
                'message': error_message,
                'needs_confirmation': False
            }
        
        # Находим все события по названиям
        all_events_to_delete = []
        for title in titles:
            similar_events = self.db.find_similar_events(user_id, title)
            all_events_to_delete.extend(similar_events)
        
        if not all_events_to_delete:
            return {
                'action': 'not_found',
                'message': f"Не найдено событий для удаления: {', '.join(titles)}",
                'needs_confirmation': False
            }
        
        # Удаляем из календарей ПЕРЕД удалением из БД
        deleted_from_calendars = 0
        for event in all_events_to_delete:
            external_id = event.get('external_id')
            provider = event.get('provider')
            event_id = event.get('id')
            
            # Удаляем напоминания для события
            if event_id:
                try:
                    self.db.delete_reminders_for_event(event_id)
                except Exception as e:
                    logger.error(f"Ошибка удаления напоминаний для события {event_id}: {e}")
            
            # Удаляем из календарей
            if external_id and provider:
                try:
                    if provider == 'google':
                        calendar = GoogleCalendar(user_id)
                        if calendar.delete_event(external_id):
                            deleted_from_calendars += 1
                            logger.info(f"Удалено событие {external_id} из Google Calendar")
                    elif provider == 'icloud':
                        conn = next((c for c in calendar_connections if c['provider'] == 'icloud'), None)
                        if conn:
                            import json
                            credentials = json.loads(conn['credentials'])
                            calendar = ICloudCalendar(
                                user_id=user_id,
                                caldav_url=credentials.get('caldav_url'),
                                username=credentials.get('username'),
                                password=credentials.get('password')
                            )
                            if calendar.delete_event(external_id):
                                deleted_from_calendars += 1
                                logger.info(f"Удалено событие {external_id} из iCloud Calendar")
                except Exception as e:
                    logger.error(f"Ошибка удаления события {external_id} из календаря {provider}: {e}", exc_info=True)
        
        # Теперь удаляем из БД
        event_ids = [e['id'] for e in all_events_to_delete]
        deleted_count, _ = self.db.delete_events_by_ids(user_id, event_ids)
        
        event_titles = [e['title'] for e in all_events_to_delete[:5]]
        message = f"✓ Удалено событий: {deleted_count}\n"
        for title in event_titles:
            message += f"  • {title}\n"
        if deleted_count > 5:
            message += f"  ... и еще {deleted_count - 5}"
        
        return {
            'action': 'deleted_many',
            'message': message,
            'needs_confirmation': False
        }
    
    async def _handle_delete_by_pattern(self, user_id: int, extracted_data: Dict,
                                       calendar_connections: List[Dict]) -> Dict:
        """Обработать удаление событий по паттерну."""
        pattern = extracted_data.get('pattern') or extracted_data.get('title', '')
        if not pattern:
            original_text = extracted_data.get('_original_text', '')
            error_message = self._generate_smart_error_message(
                original_text, extracted_data,
                "Попытка удалить события по паттерну, но паттерн не указан."
            )
            return {
                'action': 'error',
                'message': error_message,
                'needs_confirmation': False
            }
        
        # Сначала находим события БЕЗ удаления из БД
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, external_id, provider, title FROM events 
            WHERE user_id = ? AND (title LIKE ? OR description LIKE ?)
        """, (user_id, f"%{pattern}%", f"%{pattern}%"))
        events = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        if not events:
            return {
                'action': 'not_found',
                'message': f"Не найдено событий с паттерном '{pattern}'.",
                'needs_confirmation': False
            }
        
        # Удаляем из календарей ПЕРЕД удалением из БД
        deleted_from_calendars = 0
        for event in events:
            external_id = event.get('external_id')
            provider = event.get('provider')
            event_id = event.get('id')
            
            # Удаляем напоминания для события
            if event_id:
                try:
                    self.db.delete_reminders_for_event(event_id)
                except Exception as e:
                    logger.error(f"Ошибка удаления напоминаний для события {event_id}: {e}")
            
            # Удаляем из календарей
            if external_id and provider:
                try:
                    if provider == 'google':
                        calendar = GoogleCalendar(user_id)
                        if calendar.delete_event(external_id):
                            deleted_from_calendars += 1
                            logger.info(f"Удалено событие {external_id} из Google Calendar")
                    elif provider == 'icloud':
                        conn = next((c for c in calendar_connections if c['provider'] == 'icloud'), None)
                        if conn:
                            import json
                            credentials = json.loads(conn['credentials'])
                            calendar = ICloudCalendar(
                                user_id=user_id,
                                caldav_url=credentials.get('caldav_url'),
                                username=credentials.get('username'),
                                password=credentials.get('password')
                            )
                            if calendar.delete_event(external_id):
                                deleted_from_calendars += 1
                                logger.info(f"Удалено событие {external_id} из iCloud Calendar")
                except Exception as e:
                    logger.error(f"Ошибка удаления события {external_id} из календаря {provider}: {e}", exc_info=True)
        
        # Теперь удаляем из БД по конкретным ID
        event_ids = [e['id'] for e in events]
        if event_ids:
            deleted_count, _ = self.db.delete_events_by_ids(user_id, event_ids)
        else:
            deleted_count = 0
        
        return {
            'action': 'deleted_by_pattern',
            'message': f"✓ Удалено событий с паттерном '{pattern}': {deleted_count} (из календарей: {deleted_from_calendars})",
            'needs_confirmation': False
        }
    
    async def _handle_delete(self, user_id: int, extracted_data: Dict,
                            calendar_connections: List[Dict]) -> Dict:
        """Обработать удаление одного события."""
        title = extracted_data.get('title', '')
        similar_events = self.db.find_similar_events(user_id, title)
        
        if not similar_events:
            return {
                'action': 'not_found',
                'message': f"Событие '{title}' не найдено для удаления.",
                'needs_confirmation': False
            }
        
        event = similar_events[0]
        event_id = event.get('id')
        external_id = event.get('external_id')
        provider = event.get('provider')
        
        # Удаляем напоминания для события
        if event_id:
            try:
                self.db.delete_reminders_for_event(event_id)
                logger.info(f"Удалены напоминания для события {event_id}")
            except Exception as e:
                logger.error(f"Ошибка удаления напоминаний для события {event_id}: {e}")
        
        # Удаляем из календаря ПЕРЕД удалением из БД
        deleted_from_calendar = False
        if external_id and provider:
            try:
                if provider == 'google':
                    calendar = GoogleCalendar(user_id)
                    if calendar.delete_event(external_id):
                        deleted_from_calendar = True
                        logger.info(f"Удалено событие {external_id} из Google Calendar")
                elif provider == 'icloud':
                    conn = next((c for c in calendar_connections if c['provider'] == 'icloud'), None)
                    if conn:
                        import json
                        credentials = json.loads(conn['credentials'])
                        calendar = ICloudCalendar(
                            user_id=user_id,
                            caldav_url=credentials.get('caldav_url'),
                            username=credentials.get('username'),
                            password=credentials.get('password')
                        )
                        if calendar.delete_event(external_id):
                            deleted_from_calendar = True
                            logger.info(f"Удалено событие {external_id} из iCloud Calendar")
            except Exception as e:
                logger.error(f"Ошибка удаления события {external_id} из календаря {provider}: {e}", exc_info=True)
        
        # Удаляем из БД
        self.db.delete_event(event_id, user_id)
        
        return {
            'action': 'deleted',
            'message': f"✓ Удалено событие: {event['title']}",
            'needs_confirmation': False
        }
    
    async def _handle_list_events(self, user_id: int, extracted_data: Dict,
                                  calendar_connections: List[Dict], timezone: str) -> Dict:
        """Обработать запрос на просмотр списка событий."""
        from datetime import timedelta
        import pytz
        
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)
        
        # Определяем период времени
        time_period = extracted_data.get('time_period', 'week')
        
        # Если период не указан явно, пытаемся определить из текста запроса
        if not time_period or time_period == 'null':
            query_text = (extracted_data.get('title', '') or extracted_data.get('description', '') or '').lower()
            if any(word in query_text for word in ['сегодня', 'today', 'на сегодня']):
                time_period = 'today'
            elif any(word in query_text for word in ['завтра', 'tomorrow', 'на завтра']):
                time_period = 'tomorrow'
            elif any(word in query_text for word in ['месяц', 'month', 'на месяц', 'в месяц']):
                time_period = 'month'
            elif any(word in query_text for word in ['все', 'all', 'все события', 'все дела']):
                time_period = 'all'
            else:
                time_period = 'week'  # По умолчанию неделя
        
        # Вычисляем диапазон дат
        if time_period == 'today':
            start_from = now.replace(hour=0, minute=0, second=0, microsecond=0)
            start_to = now.replace(hour=23, minute=59, second=59, microsecond=999999)
            period_name = "сегодня"
        elif time_period == 'tomorrow':
            start_from = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            start_to = (now + timedelta(days=1)).replace(hour=23, minute=59, second=59, microsecond=999999)
            period_name = "завтра"
        elif time_period == 'week':
            start_from = now.replace(hour=0, minute=0, second=0, microsecond=0)
            start_to = now + timedelta(days=7)
            period_name = "ближайшую неделю"
        elif time_period == 'month':
            start_from = now.replace(hour=0, minute=0, second=0, microsecond=0)
            start_to = now + timedelta(days=30)
            period_name = "месяц"
        elif time_period == 'all':
            start_from = None
            start_to = None
            period_name = "все"
        else:
            # По умолчанию неделя
            start_from = now.replace(hour=0, minute=0, second=0, microsecond=0)
            start_to = now + timedelta(days=7)
            period_name = "ближайшую неделю"
        
        # Получаем события из БД
        db_events = self.db.get_events(user_id, limit=100, start_from=start_from, start_to=start_to)
        
        # Используем множество для отслеживания уже добавленных событий (по external_id)
        seen_event_ids = set()
        all_events = []
        
        # Добавляем события из БД
        for event in db_events:
            # Нормализуем start_time если это строка
            if event.get('start_time'):
                if isinstance(event['start_time'], str):
                    try:
                        event['start_time'] = datetime.fromisoformat(event['start_time'].replace('Z', '+00:00'))
                    except:
                        continue
                if event['start_time'].tzinfo is None:
                    event['start_time'] = tz.localize(event['start_time'])
                else:
                    event['start_time'] = event['start_time'].astimezone(tz)
            
            # Проверяем диапазон дат
            if start_from and event.get('start_time') and event['start_time'] < start_from:
                continue
            if start_to and event.get('start_time') and event['start_time'] > start_to:
                continue
            
            event_id = event.get('external_id') or f"db_{event.get('id')}"
            if event_id not in seen_event_ids:
                seen_event_ids.add(event_id)
                all_events.append(event)
        
        # Добавляем события из подключенных календарей
        for conn in calendar_connections:
            try:
                if conn['provider'] == 'google':
                    calendar = GoogleCalendar(user_id)
                    google_events = calendar.search_events(
                        query='',
                        time_min=start_from,
                        time_max=start_to,
                        max_results=50
                    )
                    for gevent in google_events:
                        event_id = gevent.get('id')
                        if event_id in seen_event_ids:
                            continue  # Уже есть в списке из БД
                        
                        start = gevent.get('start', {}).get('dateTime') or gevent.get('start', {}).get('date')
                        if start:
                            try:
                                start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                                if start_dt.tzinfo is None:
                                    start_dt = tz.localize(start_dt)
                                else:
                                    start_dt = start_dt.astimezone(tz)
                                
                                # Проверяем диапазон дат
                                if start_from and start_dt < start_from:
                                    continue
                                if start_to and start_dt > start_to:
                                    continue
                                
                                seen_event_ids.add(event_id)
                                all_events.append({
                                    'title': gevent.get('summary', 'Без названия'),
                                    'description': gevent.get('description'),
                                    'start_time': start_dt,
                                    'location': gevent.get('location'),
                                    'external_id': event_id,
                                    'provider': 'google'
                                })
                            except Exception as e:
                                logger.debug(f"Ошибка парсинга даты Google события: {e}")
                                continue
                
                elif conn['provider'] == 'icloud':
                    # Для iCloud нужно реализовать поиск через CalDAV
                    # Пока используем только события из БД
                    pass
            except Exception as e:
                logger.error(f"Ошибка получения событий из {conn['provider']}: {e}")
                continue
        
        # Сортируем события по времени начала
        all_events.sort(key=lambda e: e.get('start_time') or datetime.min.replace(tzinfo=tz))
        
        # Форматируем список событий
        if not all_events:
            return {
                'action': 'list_empty',
                'message': f"На {period_name} у тебя нет запланированных событий.",
                'needs_confirmation': False
            }
        
        # Формируем красивое сообщение
        message = f"📅 События на {period_name} ({len(all_events)}):\n\n"
        
        current_date = None
        for event in all_events:
            start_time = event.get('start_time')
            
            if start_time:
                # Форматируем дату для группировки
                if start_time.tzinfo is None:
                    start_time = tz.localize(start_time)
                else:
                    start_time = start_time.astimezone(tz)
                
                event_date = start_time.date()
                
                # Добавляем заголовок дня, если он изменился
                if current_date != event_date:
                    current_date = event_date
                    weekdays = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
                    months = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
                             'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']
                    
                    weekday = weekdays[start_time.weekday()]
                    day = start_time.day
                    month = months[start_time.month - 1]
                    
                    # Если это сегодня или завтра, показываем это
                    today = now.date()
                    if event_date == today:
                        date_header = f"\n📆 Сегодня ({weekday}, {day} {month})"
                    elif event_date == (now + timedelta(days=1)).date():
                        date_header = f"\n📆 Завтра ({weekday}, {day} {month})"
                    else:
                        date_header = f"\n📆 {weekday}, {day} {month}"
                    
                    message += date_header + "\n"
                
                # Добавляем событие
                time_str = start_time.strftime("%H:%M")
                title = event.get('title', 'Без названия')
                location = event.get('location')
                description = event.get('description')
                
                message += f"  ⏰ {time_str} — {title}\n"
                
                if location:
                    message += f"     📍 {location}\n"
                
                if description and len(description.strip()) > 0:
                    desc_preview = description[:50] + "..." if len(description) > 50 else description
                    message += f"     📝 {desc_preview}\n"
            else:
                # Событие без времени
                title = event.get('title', 'Без названия')
                message += f"  • {title}\n"
        
        return {
            'action': 'list_shown',
            'message': message,
            'events': all_events,
            'needs_confirmation': False
        }
    
    async def _handle_create_many(self, user_id: int, extracted_data: Dict,
                                  calendar_connections: List[Dict], timezone: str) -> Dict:
        """Обработать создание нескольких событий."""
        titles = extracted_data.get('titles', [])
        if not titles:
            # Пытаемся извлечь из текста описания
            description = extracted_data.get('description', '')
            if description:
                # Простой парсинг для нескольких событий
                import re
                # Ищем паттерны типа "встреча в понедельник и презентация во вторник"
                titles = [t.strip() for t in re.split(r'[и,]', description) if t.strip() and len(t.strip()) > 3]
        
        if not titles:
            return {
                'action': 'error',
                'message': 'Не указаны события для создания.',
                'needs_confirmation': False
            }
        
        created_count = 0
        created_titles = []
        
        # Создаем каждое событие отдельно
        for title in titles:
            # Создаем событие с базовыми данными
            event_data = extracted_data.copy()
            event_data['title'] = title
            event_data['intent'] = 'event'
            
            result = await self._handle_event(user_id, event_data, calendar_connections, timezone)
            if result.get('action') == 'created':
                created_count += 1
                created_titles.append(title)
        
        if created_count == 0:
            return {
                'action': 'error',
                'message': 'Не удалось создать события.',
                'needs_confirmation': False
            }
        
        message = f"✓ Создано событий: {created_count}\n"
        for title in created_titles[:5]:
            message += f"  • {title}\n"
        if created_count > 5:
            message += f"  ... и еще {created_count - 5}"
        
        return {
            'action': 'created_many',
            'message': message,
            'needs_confirmation': False
        }
    
    async def _handle_update_many(self, user_id: int, extracted_data: Dict,
                                  calendar_connections: List[Dict], timezone: str) -> Dict:
        """Обработать обновление нескольких событий."""
        pattern = extracted_data.get('pattern') or extracted_data.get('title', '')
        update_fields = extracted_data.get('update_fields', {})
        
        if not pattern:
            return {
                'action': 'error',
                'message': 'Не указан паттерн для поиска событий для обновления.',
                'needs_confirmation': False
            }
        
        # Находим события по паттерну
        similar_events = self.db.find_similar_events(user_id, pattern, days_window=365)
        
        if not similar_events:
            return {
                'action': 'not_found',
                'message': f"Не найдено событий для обновления: '{pattern}'",
                'needs_confirmation': False
            }
        
        updated_count = 0
        updated_titles = []
        
        for event in similar_events:
            # Обновляем каждое событие
            event_update_data = extracted_data.copy()
            event_update_data['title'] = event['title']  # Сохраняем название для поиска
            
            result = await self._update_existing_event(
                user_id, event, event_update_data, calendar_connections, timezone
            )
            if result.get('action') == 'updated':
                updated_count += 1
                updated_titles.append(event['title'])
        
        if updated_count == 0:
            return {
                'action': 'error',
                'message': 'Не удалось обновить события.',
                'needs_confirmation': False
            }
        
        message = f"✓ Обновлено событий: {updated_count}\n"
        for title in updated_titles[:5]:
            message += f"  • {title}\n"
        if updated_count > 5:
            message += f"  ... и еще {updated_count - 5}"
        
        return {
            'action': 'updated_many',
            'message': message,
            'needs_confirmation': False
        }
    
    async def _handle_list_notes(self, user_id: int) -> Dict:
        """Обработать запрос на просмотр заметок."""
        notes = self.db.get_notes(user_id, limit=50)
        
        if not notes:
            return {
                'action': 'list_empty',
                'message': 'У тебя нет сохраненных заметок.',
                'needs_confirmation': False
            }
        
        message = f"📝 Заметки ({len(notes)}):\n\n"
        for i, note in enumerate(notes[:20], 1):  # Показываем первые 20
            content = note.get('content', '')
            preview = content[:100] + "..." if len(content) > 100 else content
            created = note.get('created_at', '')
            if isinstance(created, str):
                try:
                    created_dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
                    created_str = created_dt.strftime("%d.%m.%Y")
                except:
                    created_str = created[:10] if len(created) >= 10 else created
            else:
                created_str = str(created)[:10]
            
            message += f"{i}. {preview}\n   ({created_str})\n\n"
        
        if len(notes) > 20:
            message += f"... и еще {len(notes) - 20} заметок"
        
        return {
            'action': 'list_shown',
            'message': message,
            'needs_confirmation': False
        }
    
    async def _handle_delete_note(self, user_id: int, extracted_data: Dict) -> Dict:
        """Обработать удаление заметки."""
        # Ищем заметку по содержимому или индексу
        notes = self.db.get_notes(user_id, limit=100)
        
        query = extracted_data.get('title') or extracted_data.get('description', '')
        if not query:
            return {
                'action': 'error',
                'message': 'Не указана заметка для удаления.',
                'needs_confirmation': False
            }
        
        # Пытаемся найти по номеру (если это число)
        try:
            note_index = int(query) - 1
            if 0 <= note_index < len(notes):
                note = notes[note_index]
                # Удаляем заметку
                deleted = self.db.delete_note(note['id'], user_id)
                
                if deleted:
                    return {
                        'action': 'deleted',
                        'message': f"✓ Удалена заметка: {note.get('content', '')[:50]}...",
                        'needs_confirmation': False
                    }
        except ValueError:
            pass
        
        # Ищем по содержимому
        matching_notes = [
            n for n in notes
            if query.lower() in n.get('content', '').lower()
        ]
        
        if not matching_notes:
            return {
                'action': 'not_found',
                'message': f"Заметка '{query}' не найдена.",
                'needs_confirmation': False
            }
        
        # Удаляем первую найденную
        note = matching_notes[0]
        deleted = self.db.delete_note(note['id'], user_id)
        
        if deleted:
            return {
                'action': 'deleted',
                'message': f"✓ Удалена заметка: {note.get('content', '')[:50]}...",
                'needs_confirmation': False
            }
        
        return {
            'action': 'error',
            'message': 'Не удалось удалить заметку.',
            'needs_confirmation': False
        }
    
    async def _handle_search(self, user_id: int, extracted_data: Dict,
                            calendar_connections: List[Dict]) -> Dict:
        """Обработать поиск событий."""
        query = extracted_data.get('title', '') or extracted_data.get('description', '')
        
        # Поиск в БД
        events = self.db.get_events(user_id, limit=10)
        matching_events = [
            e for e in events
            if query.lower() in e['title'].lower() or (e['description'] and query.lower() in e['description'].lower())
        ]
        
        if not matching_events:
            return {
                'action': 'not_found',
                'message': f"По запросу '{query}' ничего не найдено.",
                'needs_confirmation': False
            }
        
        message = f"Найдено событий: {len(matching_events)}\n\n"
        for event in matching_events[:5]:
            message += f"• {event['title']}\n"
            if event.get('start_time'):
                message += f"  {event['start_time']}\n"
        
        return {
            'action': 'found',
            'message': message,
            'events': matching_events,
            'needs_confirmation': False
        }
    
    def _format_datetime(self, dt: Optional[datetime], timezone: str) -> str:
        """Форматировать datetime для пользователя."""
        if not dt:
            return "не указано"
        
        import pytz
        tz = pytz.timezone(timezone)
        if dt.tzinfo is None:
            dt = tz.localize(dt)
        else:
            dt = dt.astimezone(tz)
        
        return dt.strftime("%d.%m.%Y %H:%M")
    
    def _format_event_confirmation(self, title: str, start_time: Optional[datetime] = None,
                                  location: Optional[str] = None, description: Optional[str] = None,
                                  timezone: str = "Europe/Moscow", is_reminder: bool = False) -> str:
        """
        Форматировать подтверждение события в заданном формате.
        
        Формат:
        📅 (эмодзи по контексту) Название события
         · Дата: (Вт) 13 январь
         · Время: 12:00
         · Напоминание: За 15 минут до события
         · Заметки: если есть
        """
        import pytz
        
        # Подбираем эмодзи с помощью AI на основе контекста события
        # Используем синхронную версию, так как OpenAI клиент поддерживает синхронные вызовы
        try:
            emoji = self._get_emoji_for_event_sync(title, description, location, start_time, is_reminder)
        except Exception as e:
            logger.warning(f"Не удалось подобрать эмодзи через AI, используем дефолт: {e}")
            emoji = "🔔" if is_reminder else "📅"
        
        # Начинаем формировать сообщение (БЕЗ "[Событие] Добавлен" и "@")
        message = f"{emoji} {title}\n"
        
        if start_time:
            tz = pytz.timezone(timezone)
            if start_time.tzinfo is None:
                dt = tz.localize(start_time)
            else:
                dt = start_time.astimezone(tz)
            
            # День недели (краткий формат)
            weekdays_short = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
            weekday = weekdays_short[dt.weekday()]
            
            # Месяц на русском
            months = ['январь', 'февраль', 'март', 'апрель', 'май', 'июнь',
                     'июль', 'август', 'сентябрь', 'октябрь', 'ноябрь', 'декабрь']
            month = months[dt.month - 1]
            
            # Дата
            message += f" · Дата: ({weekday}) {dt.day} {month}\n"
            
            # Время
            message += f" · Время: {dt.strftime('%H:%M')}\n"
        
        # Напоминание (всегда по умолчанию за 15 минут)
        message += " · Напоминание: За 15 минут до события\n"
        
        # Заметки (description)
        if description:
            message += f" · Заметки: {description[:100]}{'...' if len(description) > 100 else ''}\n"
        
        # Место
        if location:
            message += f" · Место: {location}\n"
        
        return message.strip()
    
    async def _get_emoji_for_event(self, title: str, description: Optional[str] = None, 
                             location: Optional[str] = None, start_time: Optional[datetime] = None,
                             is_reminder: bool = False) -> str:
        """
        Подобрать подходящее эмодзи для события с помощью AI.
        
        Args:
            title: Название события
            description: Описание события
            location: Место проведения
            start_time: Время начала
            is_reminder: Является ли это напоминанием
        
        Returns:
            Эмодзи (одно или несколько)
        """
        try:
            # Формируем контекст для AI
            context_parts = [f"Название: {title}"]
            if description:
                context_parts.append(f"Описание: {description[:200]}")
            if location:
                context_parts.append(f"Место: {location}")
            if start_time:
                hour = start_time.hour
                if 5 <= hour < 12:
                    context_parts.append("Время: утро")
                elif 12 <= hour < 17:
                    context_parts.append("Время: день")
                elif 17 <= hour < 22:
                    context_parts.append("Время: вечер")
                else:
                    context_parts.append("Время: ночь")
            
            context = "\n".join(context_parts)
            
            prompt = f"""Подбери ОДНО самое подходящее эмодзи для этого события. Верни ТОЛЬКО эмодзи, без текста.

Событие:
{context}

Верни только одно эмодзи, которое лучше всего отражает суть события. Например:
- Для встреч/звонков: 📞 📱 💬
- Для спорта/зарядки: 💪 🏃 ⚽
- Для еды: 🍽️ 🍕 🍔
- Для сна: 😴 🌙 🛏️
- Для работы: 💼 📊 📝
- Для развлечений: 🎬 🎮 🎭
- Для покупок: 🛒 🏪 💰
- Для учебы: 📚 ✏️ 🎓
- Для путешествий: ✈️ 🚗 🏖️
- Для здоровья: 🏥 💊 🩺

Верни ТОЛЬКО эмодзи, без объяснений."""
            
            response = self.ai_client.chat.completions.create(
                model=config.OPENROUTER_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "Ты помощник для подбора эмодзи. Отвечай ТОЛЬКО одним эмодзи, без текста."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=10
            )
            
            emoji = response.choices[0].message.content.strip()
            
            # Очищаем от лишних символов (оставляем только эмодзи)
            import re
            # Извлекаем только эмодзи (Unicode эмодзи символы)
            emoji_match = re.search(r'[\U0001F300-\U0001F9FF\U00002600-\U000027BF\U0001F600-\U0001F64F\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]+', emoji)
            if emoji_match:
                emoji = emoji_match.group(0)
            else:
                # Если не нашли эмодзи, используем первое слово/символ
                emoji = emoji.split()[0] if emoji.split() else "📅"
            
            # Если результат пустой или невалидный, используем дефолт
            if not emoji or len(emoji.strip()) == 0:
                emoji = "🔔" if is_reminder else "📅"
            
            logger.debug(f"AI подобрал эмодзи '{emoji}' для события '{title}'")
            return emoji
        
        except Exception as e:
            logger.error(f"Ошибка подбора эмодзи через AI: {e}", exc_info=True)
            # Fallback на простую логику
            title_lower = title.lower()
            if is_reminder:
                return "🔔"
            elif any(word in title_lower for word in ['встреча', 'meeting', 'созвон', 'звонок']):
                return "📞"
            elif any(word in title_lower for word in ['зарядка', 'спорт', 'тренировка']):
                return "💪"
            elif any(word in title_lower for word in ['сон', 'спать', 'ложиться']):
                return "😴"
            else:
                return "📅"
    
    def _get_emoji_for_event_sync(self, title: str, description: Optional[str] = None, 
                                  location: Optional[str] = None, start_time: Optional[datetime] = None,
                                  is_reminder: bool = False) -> str:
        """
        Синхронная версия подбора эмодзи (для использования когда event loop уже запущен).
        """
        try:
            # Формируем контекст для AI
            context_parts = [f"Название: {title}"]
            if description:
                context_parts.append(f"Описание: {description[:200]}")
            if location:
                context_parts.append(f"Место: {location}")
            if start_time:
                hour = start_time.hour
                if 5 <= hour < 12:
                    context_parts.append("Время: утро")
                elif 12 <= hour < 17:
                    context_parts.append("Время: день")
                elif 17 <= hour < 22:
                    context_parts.append("Время: вечер")
                else:
                    context_parts.append("Время: ночь")
            
            context = "\n".join(context_parts)
            
            prompt = f"""Подбери ОДНО самое подходящее эмодзи для этого события. Верни ТОЛЬКО эмодзи, без текста.

Событие:
{context}

Верни только одно эмодзи, которое лучше всего отражает суть события. Например:
- Для встреч/звонков: 📞 📱 💬
- Для спорта/зарядки: 💪 🏃 ⚽
- Для еды: 🍽️ 🍕 🍔
- Для сна: 😴 🌙 🛏️
- Для работы: 💼 📊 📝
- Для развлечений: 🎬 🎮 🎭
- Для покупок: 🛒 🏪 💰
- Для учебы: 📚 ✏️ 🎓
- Для путешествий: ✈️ 🚗 🏖️
- Для здоровья: 🏥 💊 🩺

Верни ТОЛЬКО эмодзи, без объяснений."""
            
            # Синхронный вызов API
            response = self.ai_client.chat.completions.create(
                model=config.OPENROUTER_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "Ты помощник для подбора эмодзи. Отвечай ТОЛЬКО одним эмодзи, без текста."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=10
            )
            
            emoji = response.choices[0].message.content.strip()
            
            # Очищаем от лишних символов (оставляем только эмодзи)
            import re
            # Извлекаем только эмодзи (Unicode эмодзи символы)
            emoji_match = re.search(r'[\U0001F300-\U0001F9FF\U00002600-\U000027BF\U0001F600-\U0001F64F\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]+', emoji)
            if emoji_match:
                emoji = emoji_match.group(0)
            else:
                # Если не нашли эмодзи, используем первое слово/символ
                emoji = emoji.split()[0] if emoji.split() else "📅"
            
            # Если результат пустой или невалидный, используем дефолт
            if not emoji or len(emoji.strip()) == 0:
                emoji = "🔔" if is_reminder else "📅"
            
            logger.debug(f"AI подобрал эмодзи '{emoji}' для события '{title}'")
            return emoji
        
        except Exception as e:
            logger.error(f"Ошибка подбора эмодзи через AI (sync): {e}", exc_info=True)
            # Fallback на простую логику
            title_lower = title.lower()
            if is_reminder:
                return "🔔"
            elif any(word in title_lower for word in ['встреча', 'meeting', 'созвон', 'звонок']):
                return "📞"
            elif any(word in title_lower for word in ['зарядка', 'спорт', 'тренировка']):
                return "💪"
            elif any(word in title_lower for word in ['сон', 'спать', 'ложиться']):
                return "😴"
            else:
                return "📅"

