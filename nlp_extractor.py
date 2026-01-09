"""Модуль для извлечения intent и контекста из текста через OpenRouter."""
import json
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
import dateparser
import pytz
from openai import OpenAI
import config

logger = logging.getLogger(__name__)


class NLPExtractor:
    """Класс для NLP обработки и извлечения intent и контекста."""
    
    def __init__(self):
        self.client = OpenAI(
            api_key=config.OPENROUTER_API_KEY,
            base_url=config.OPENROUTER_BASE_URL
        )
        self.model = config.OPENROUTER_MODEL
    
    async def extract_intent_and_context(self, text: str, user_timezone: str = "Europe/Moscow",
                                        user_locale: str = "ru_RU", last_event: Optional[Dict] = None,
                                        is_reply: bool = False) -> Dict:
        """
        Извлечь intent и контекст из текста пользователя.
        
        Returns:
            Словарь с полями:
            - intent: 'event', 'reminder', 'note', 'update', 'delete', 'search', 'unknown'
            - title: название события/напоминания
            - description: описание
            - start_time: datetime начала (если определено)
            - end_time: datetime конца (если определено)
            - location: место
            - priority: приоритет (0-5)
            - has_explicit_time: bool - есть ли явное время
            - confidence: уверенность в извлечении
        """
        try:
            tz = pytz.timezone(user_timezone)
            now = datetime.now(tz)
            
            # Формируем информацию о последнем событии для контекста
            last_event_info = ""
            if last_event:
                event_title = last_event.get('title', 'Событие')
                event_start = last_event.get('start_time')
                if event_start:
                    try:
                        if isinstance(event_start, str):
                            event_start_dt = datetime.fromisoformat(event_start.replace('Z', '+00:00'))
                        else:
                            event_start_dt = event_start
                        event_start_str = event_start_dt.strftime("%Y-%m-%d %H:%M")
                        last_event_info = f"\n\nПоследнее созданное/измененное событие пользователя:\n- Название: {event_title}\n- Дата/время: {event_start_str}"
                    except:
                        last_event_info = f"\n\nПоследнее созданное/измененное событие пользователя:\n- Название: {event_title}"
            
            # Если это reply, добавляем информацию об этом
            if is_reply:
                last_event_info += "\n\n⚠️ Это reply к сообщению. Если это заметка/примечание без даты - это intent 'add_note' к последнему событию."
            
            # Компактный промпт для извлечения структурированных данных
            system_prompt = """Ты ассистент для управления календарем. Извлеки структурированную информацию из сообщения.

⚠️ КРИТИЧЕСКИ ВАЖНО - ПРАВИЛА ПРИОРИТЕТА:

1. СОБЫТИЕ (высший приоритет) - если есть:
   - Дата/время (сегодня, завтра, в 11:00, 14:00, 15 января и т.д.) И действие/дело
   - Слово "напомни" + время + действие = СОБЫТИЕ (например: "напомни в 14:00 проветрить", "напомни завтра в 10 утра позвонить")
   - Примеры: "завтра в 11 утра зарядка", "сегодня в 15:00 встреча", "напомни сделать зарядку в 11 утра", "напомни в 14:00 проветрить"
   - → intent: "event" (НЕ "note", НЕ "reminder", НЕ "add_reminder"!)

2. ЗАМЕТКА К СОБЫТИЮ - только если:
   - Явно сказано "заметка" ИЛИ "примечание" И упоминается существующее событие
   - Или это reply к сообщению о событии
   - → intent: "add_note"

3. ЗАМЕТКА (самый низкий приоритет) - ТОЛЬКО если:
   - НЕТ даты/времени И явно сказано "заметка"/"записать"
   - Просто текст без дат и действий

Intent (проверяй в порядке):
1. "delete_all" - "удали все планы/события"
2. "list_events" - "покажи события/планы" (time_period: today/tomorrow/week/month/all)
3. "delete_by_period" - "удали все за сегодня/неделю"
4. "delete_many" - "удали X и Y" (titles: ["X", "Y"])
5. "delete_by_pattern" - "удали все встречи" (pattern: "встреча")
6. "add_reminder" - "напомни за 2 часа" БЕЗ указания времени события (reminder_intervals: ["2 hours"]) - только для существующих событий!
7. "add_note" - "добавь заметку к событию X" или reply к событию (note_text)
8. "create_many" - "добавь X и Y" (titles: ["X", "Y"])
9. "event" - если есть дата/время + действие (ПО УМОЛЧАНИЮ для действий с датой!)
   - ВАЖНО: "напомни в [время] [действие]" = "event" с start_time = [время]
   - ВАЖНО: "напомни [действие] в [время]" = "event" с start_time = [время]
   - ВАЖНО: "напомни завтра/сегодня [действие]" = "event" с start_time = завтра/сегодня
10. "update" - "измени/перенеси событие X" (update_fields)
11. "update_many" - "перенеси все X"
12. "delete" - "удали событие X"
13. "search" - поиск
14. "list_notes" - "покажи заметки"
15. "delete_note" - "удали заметку"
16. "note" - ТОЛЬКО если НЕТ даты/времени и явно сказано "заметка"

Поля JSON: intent, title/titles, description, start_time, end_time, location, priority (0-5), time_period, pattern, reminder_intervals, note_text, update_fields, refers_to_last_event.

ПРАВИЛО: Дата/время + действие = СОБЫТИЕ, не заметка!
ПРАВИЛО: "напомни" + время + действие = СОБЫТИЕ с этим временем!
Отвечай только JSON.

Текущая дата и время: {current_time}
Часовой пояс: {timezone}{last_event_info}""".format(
                current_time=now.strftime("%Y-%m-%d %H:%M:%S %Z"),
                timezone=user_timezone,
                last_event_info=last_event_info
            )
            
            user_prompt = f"""Извлеки информацию из сообщения: "{text}"

Верни JSON:
{{
    "intent": "event|reminder|note|list_events|delete_all|delete_by_period|delete_many|delete_by_pattern|add_reminder|add_note|create_many|update|update_many|delete|search|list_notes|delete_note|unknown",
    "title": "краткое название или null",
    "titles": ["название1", "название2"] или null (для delete_many, create_many),
    "description": "полное описание или null",
    "start_time": "YYYY-MM-DDTHH:MM:SS или null",
    "end_time": "YYYY-MM-DDTHH:MM:SS или null",
    "location": "место или null",
    "priority": 0-5,
    "has_explicit_time": true/false,
    "confidence": 0.0-1.0,
    "time_period": "today|tomorrow|week|month|all" или null (для list_events, delete_by_period),
    "pattern": "паттерн поиска" или null (для delete_by_pattern),
    "reminder_intervals": ["2 hours", "1 hour"] или null (только для add_reminder),
    "note_text": "текст заметки" или null (только для add_note),
    "update_fields": {{"time": "16:00", "location": "новый офис"}} или null (для update),
    "refers_to_last_event": true/false (относится ли запрос к последнему событию)
}}"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Сохраняем оригинальный текст для fallback проверок
            result['_original_text'] = text
            
            # Парсинг дат и нормализация
            if result.get("start_time"):
                try:
                    # Парсим дату из строки
                    parsed_date = dateparser.parse(
                        result["start_time"],
                        settings={
                            'TIMEZONE': user_timezone,
                            'RETURN_AS_TIMEZONE_AWARE': True,
                            'RELATIVE_BASE': now
                        }
                    )
                    if parsed_date:
                        # Если время 00:00:00 (только дата без времени), устанавливаем 12:00
                        if parsed_date.hour == 0 and parsed_date.minute == 0 and parsed_date.second == 0:
                            parsed_date = parsed_date.replace(hour=12, minute=0, second=0)
                        result["start_time"] = parsed_date.astimezone(tz)
                    else:
                        result["start_time"] = None
                except Exception as e:
                    logger.warning(f"Ошибка парсинга start_time: {e}")
                    result["start_time"] = None
            else:
                result["start_time"] = None
            
            if result.get("end_time"):
                try:
                    parsed_date = dateparser.parse(
                        result["end_time"],
                        settings={
                            'TIMEZONE': user_timezone,
                            'RETURN_AS_TIMEZONE_AWARE': True,
                            'RELATIVE_BASE': now
                        }
                    )
                    if parsed_date:
                        result["end_time"] = parsed_date.astimezone(tz)
                    else:
                        result["end_time"] = None
                except Exception as e:
                    logger.warning(f"Ошибка парсинга end_time: {e}")
                    result["end_time"] = None
            else:
                result["end_time"] = None
            
            # Капитализируем первую букву названия
            if result.get("title"):
                title = result["title"]
                if title:
                    result["title"] = title[0].upper() + title[1:] if len(title) > 1 else title.upper()
            
            # Если есть start_time но нет end_time, добавляем час по умолчанию
            if result.get("start_time") and not result.get("end_time"):
                result["end_time"] = result["start_time"] + timedelta(hours=1)
            
            logger.info(f"Извлечено: intent={result.get('intent')}, title={result.get('title')}")
            
            return result
        
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON от LLM: {e}")
            return self._fallback_extraction(text, user_timezone)
        except Exception as e:
            logger.error(f"Ошибка извлечения intent: {e}")
            return self._fallback_extraction(text, user_timezone)
    
    def _fallback_extraction(self, text: str, user_timezone: str) -> Dict:
        """Резервный метод извлечения при ошибке LLM."""
        return {
            "intent": "note",
            "title": text[:50],
            "description": text,
            "start_time": None,
            "end_time": None,
            "location": None,
            "priority": 0,
            "has_explicit_time": False,
            "confidence": 0.3
        }
    
    def is_command(self, text: str) -> Optional[str]:
        """Проверить, является ли текст командой."""
        text_lower = text.lower().strip()
        
        commands = {
            "/search": "search",
            "/edit": "edit",
            "/delete": "delete",
            "/share": "share",
            "/settings": "settings",
            "/start": "start",
            "/help": "help"
        }
        
        for cmd, action in commands.items():
            if text_lower.startswith(cmd):
                return action
        
        return None

