"""Модуль для извлечения intent и контекста из текста через OpenRouter."""
import json
import logging
from typing import Dict, Optional, List, Any
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

    def _format_chat_history(self, chat_history: Optional[List[Dict[str, Any]]], current_text: str) -> str:
        """
        Formats recent chat history into a short string for LLM context.
        Expects items like: { role: 'user'|'assistant', content: '...', ... }.
        """
        if not chat_history:
            return ""

        # Use only a short tail to keep prompt compact.
        tail = chat_history[-12:]

        lines: List[str] = []
        for msg in tail:
            role = (msg.get("role") or "").strip().lower()
            if role not in ("user", "assistant"):
                continue
            content = (msg.get("content") or "").strip()
            if not content:
                continue

            # Avoid duplicating the current user message if it's already in history.
            if role == "user" and content == current_text.strip():
                continue

            # Trim long messages to avoid prompt bloat.
            if len(content) > 200:
                content = content[:200] + "…"

            prefix = "USER" if role == "user" else "ASSISTANT"
            lines.append(f"{prefix}: {content}")

        if not lines:
            return ""

        return "\n\nКонтекст диалога (последние сообщения):\n" + "\n".join(lines)
    
    async def extract_intent_and_context(
        self,
        text: str,
        user_timezone: str = "Europe/Moscow",
        user_locale: str = "ru_RU",
        last_event: Optional[Dict] = None,
        is_reply: bool = False,
        interpretation_mode: str = "soft",
        chat_history: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict:
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

            chat_history_info = self._format_chat_history(chat_history, text)
            
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
            
            # Добавляем информацию о режиме интерпретации в промпт
            interpretation_note = ""
            if interpretation_mode == "strict":
                interpretation_note = "\n\n⚠️ РЕЖИМ: СТРОГИЙ - Точно следуй инструкциям, не делай предположений. Если информация неоднозначна, верни 'unknown' intent."
            else:
                interpretation_note = "\n\n⚠️ РЕЖИМ: МЯГКИЙ - Используй гибкую интерпретацию, делай разумные предположения на основе контекста."
            
            # Компактный промпт для извлечения структурированных данных
            system_prompt = """Ты ассистент для управления календарем. Извлеки структурированную информацию из сообщения.

⚠️ КРИТИЧЕСКИ ВАЖНО - ПРАВИЛА ПРИОРИТЕТА:

1. СОБЫТИЕ (высший приоритет) - если есть:
   - Дата/время (сегодня, завтра, в 11:00, 14:00, 15 января, 19-го января, 3-е февраля и т.д.) И действие/дело
   - Слово "напомни" + время + действие = СОБЫТИЕ (например: "напомни в 14:00 проветрить", "напомни завтра в 10 утра позвонить")
   - Примеры: "завтра в 11 утра зарядка", "сегодня в 15:00 встреча", "фотосессия в 17:00 19-го января", "встреча 3-е февраля в 14:00"
   - ВАЖНО: Распознавай даты в формате "19-го января", "3-е февраля", "1-го марта" как полноценные даты!
   - → intent: "event" (НЕ "note", НЕ "reminder", НЕ "add_reminder"!)

2. ЗАМЕТКА К СОБЫТИЮ - только если:
   - Явно сказано "заметка" ИЛИ "примечание" И упоминается существующее событие
   - Или это reply к сообщению о событии
   - → intent: "add_note"

3. ЗАМЕТКА (самый низкий приоритет) - ТОЛЬКО если:
   - НЕТ даты/времени И явно сказано "заметка"/"записать"
   - Просто текст без дат и действий

ПОНИМАНИЕ КОНТЕКСТА И МЕСТОИМЕНИЙ:
- "это", "его", "её", "то", "тот", "эту", "тому" → refers_to_last_event: true
- Примеры:
  * "удали это" → intent="delete", refers_to_last_event: true
  * "перенеси его на завтра" → intent="update", refers_to_last_event: true, new_date="завтра"
  * "добавь напоминание к нему" → intent="add_reminder", refers_to_last_event: true
  * "измени это событие" → intent="update", refers_to_last_event: true

ОПЕРАЦИИ ПО ГЛАГОЛАМ (высокий приоритет):
- "удали/удалить/стереть/убрать + [название/местоимение]" → intent="delete", operation_verb="удали"
- "перенеси/перенести/сдвинь/передвинь + [название/местоимение]" → intent="update", operation_verb="перенеси"
- "измени/изменить/поменяй + [название/местоимение]" → intent="update", operation_verb="измени"
- "покажи/показать/найди/найти + [название]" → intent="search" или "list_events"
- "напомни/напоминание + [к чему]" → intent="add_reminder" (если есть событие) или "event" (если новое)

ОТНОСИТЕЛЬНЫЕ МОДИФИКАТОРЫ ВРЕМЕНИ:
- "на час позже" / "+1 час" → relative_time_modification: "+1 hour"
- "на 30 минут раньше" / "-30 минут" → relative_time_modification: "-30 minutes"
- "сдвинь на завтра" → intent="update", new_date="завтра"
- "перенеси на час" → intent="update", relative_time_modification: "+1 hour"
- "раньше на 30 минут" → relative_time_modification: "-30 minutes"

Intent (проверяй в порядке):
1. "small_talk" - приветствия, вопросы о делах, благодарности:
   - Примеры: "привет", "здравствуй", "как дела", "как у тебя дела", "что нового", "спасибо", "пока", "до свидания"
   - → intent: "small_talk", message_type: "greeting" | "how_are_you" | "thanks" | "goodbye"
2. "delete_all" - "удали все планы/события"
3. "list_events" - "покажи события/планы" (time_period: today/tomorrow/week/month/all)
4. "delete_by_period" - "удали все за сегодня/неделю"
5. "delete_many" - "удали X и Y" (titles: ["X", "Y"])
6. "delete_by_pattern" - "удали все встречи" (pattern: "встреча")
7. "add_reminder" - "напомни за 2 часа" БЕЗ указания времени события (reminder_intervals: ["2 hours"]) - только для существующих событий!
8. "add_note" - "добавь заметку к событию X" или reply к событию (note_text)
9. "create_many" - "добавь X и Y" (titles: ["X", "Y"])
10. "event" - если есть дата/время + действие (ПО УМОЛЧАНИЮ для действий с датой!)
   - ВАЖНО: "напомни в [время] [действие]" = "event" с start_time = [время]
   - ВАЖНО: "напомни [действие] в [время]" = "event" с start_time = [время]
   - ВАЖНО: "напомни завтра/сегодня [действие]" = "event" с start_time = завтра/сегодня
   Примеры:
   - "встреча завтра в 15:00" → intent="event", title="встреча", start_time="завтра 15:00"
   - "19-го января фотосессия в 17:00" → intent="event", title="фотосессия", start_time="2026-01-19T17:00:00"
   - "позвонить Маше в среду" → intent="event", title="позвонить Маше", start_time="ближайшая среда"
   - "напомни в 14:00 проветрить" → intent="event", title="проветрить", start_time="сегодня 14:00"
   - "зарядка каждый день в 7 утра" → intent="event", is_recurring: true, recurrence_type="daily", title="зарядка", start_time="07:00"
   - ВАЖНО: Если указан диапазон времени (например, "с 11 утра до 15 часов", "с 10:00 до 14:00", "11:00-15:00", "зарядка с 11 утра до 15 часов дня", "с 14 до 18", "с 14 часов до 18"), то:
     * start_time = время начала (11:00, 10:00, 14:00 и т.д.)
     * end_time = время окончания (15:00, 14:00, 18:00 и т.д.)
     * Если дата указана только для начала, используй ту же дату для end_time
     * Если указано только время без даты (например, "с 14 до 18"), используй сегодняшнюю дату
     * Примеры: "зарядка с 11 утра до 15 часов" → start_time="11:00", end_time="15:00" на ту же дату
               "встреча завтра с 10:00 до 12:00" → start_time="завтра 10:00", end_time="завтра 12:00"
               "работа с 9 до 18 часов" → start_time="09:00", end_time="18:00" на сегодня
               "с 14 до 18" → start_time="14:00", end_time="18:00" на сегодня
               "с 14 часов до 18" → start_time="14:00", end_time="18:00" на сегодня
               "завтра с 14 до 18" → start_time="завтра 14:00", end_time="завтра 18:00"
11. "update" - "измени/перенеси событие X"
    Примеры:
    - "перенеси встречу на завтра" → intent="update", title="встреча", new_date="завтра"
    - "сдвинь на час позже" → intent="update", refers_to_last_event: true, relative_time_modification: "+1 hour"
    - "измени время на 15:00" → intent="update", refers_to_last_event: true, new_time="15:00"
    - "перенеси его на среду" → intent="update", refers_to_last_event: true, new_date="среда"
    - "раньше на 30 минут" → intent="update", refers_to_last_event: true, relative_time_modification: "-30 minutes"
12. "update_many" - "перенеси все X"
13. "delete" - "удали событие X"
    Примеры:
    - "удали встречу с Настей" → intent="delete", title="встреча с Настей"
    - "удали это" → intent="delete", refers_to_last_event: true
    - "удали то что на вторник" → intent="delete", time_period="вторник"
    - "стереть последнее" → intent="delete", refers_to_last_event: true
    - "убрать событие" → intent="delete", refers_to_last_event: true
14. "search" - поиск
15. "list_notes" - "покажи заметки"
16. "delete_note" - "удали заметку"
17. "note" - ТОЛЬКО если НЕТ даты/времени и явно сказано "заметка"

Поля JSON:
- intent, title/titles, description
- start_time, end_time, location, priority (0-5)
- time_period, pattern, reminder_intervals, note_text, update_fields
- refers_to_last_event: bool (true если "это", "его", "её" и т.д.)
- message_type (для small_talk: "greeting"|"how_are_you"|"thanks"|"goodbye"|"general")
- relative_time_modification: str | null ("+1 hour", "-30 minutes", "+1 day")
- new_date: str | null (для update: "завтра", "среда", "2026-01-20")
- new_time: str | null (для update: "15:00", "10:30")
- operation_verb: str | null ("удали", "перенеси", "измени" - для приоритизации)
- is_recurring: bool (для повторяющихся событий)
- recurrence_type: 'daily' | 'weekly' | 'monthly' | null
- interval: int (для recurring, по умолчанию 1)
- days_of_week: List[str] | null (например ['MO', 'WE', 'FR'])
- day_of_month: int | null (1-31).

ПРАВИЛО: Дата/время + действие = СОБЫТИЕ, не заметка!
ПРАВИЛО: "напомни" + время + действие = СОБЫТИЕ с этим временем!
ПРАВИЛО: Если указан диапазон времени ("с X до Y", "X-Y", "X до Y часов"), извлекай оба времени: start_time и end_time!
ПРАВИЛО: Если при создании события указано несколько напоминаний (например, "за час, за полтора часа, за два часа напомни", "за час, за полтора, за два часа предупреди"), извлекай их все в reminder_intervals как массив строк.
ПРАВИЛО: reminder_intervals может быть указан для intent="event", если в тексте есть несколько напоминаний: "за час", "за полтора часа" (1.5 hours), "за два часа" (2 hours), "за 30 минут" (30 minutes), "за день" (1 day) и т.д.
ПРАВИЛО: Формат reminder_intervals: массив строк в формате ["1 hour", "1.5 hours", "2 hours", "30 minutes", "1 day"] или ["60 minutes", "90 minutes", "120 minutes"].
ПРИМЕР: "за час, за полтора часа, за два часа напомни" → reminder_intervals: ["1 hour", "1.5 hours", "2 hours"]

RECURRING PATTERNS (повторяющиеся события):
- "каждый день" / "ежедневно" / "daily" → is_recurring: true, recurrence_type: 'daily', interval: 1
- "каждые 2 дня" → is_recurring: true, recurrence_type: 'daily', interval: 2
- "каждую неделю" / "еженедельно" / "weekly" → is_recurring: true, recurrence_type: 'weekly', interval: 1
- "по понедельникам" → is_recurring: true, recurrence_type: 'weekly', days_of_week: ['MO']
- "по понедельникам и средам" → is_recurring: true, recurrence_type: 'weekly', days_of_week: ['MO', 'WE']
- "по вторникам и четвергам" → is_recurring: true, recurrence_type: 'weekly', days_of_week: ['TU', 'TH']
- "по пятницам" → is_recurring: true, recurrence_type: 'weekly', days_of_week: ['FR']
- "по выходным" → is_recurring: true, recurrence_type: 'weekly', days_of_week: ['SA', 'SU']
- "каждый месяц" / "ежемесячно" / "monthly" → is_recurring: true, recurrence_type: 'monthly', interval: 1
- "каждое 15 число" → is_recurring: true, recurrence_type: 'monthly', day_of_month: 15

ВАЖНО: Если есть слова "каждый/каждая/каждые/ежедневно/еженедельно/ежемесячно/по [дням недели]" - это RECURRING событие!

Отвечай только JSON.

Текущая дата и время: {current_time}
Часовой пояс: {timezone}{chat_history_info}{last_event_info}{interpretation_note}""".format(
                current_time=now.strftime("%Y-%m-%d %H:%M:%S %Z"),
                timezone=user_timezone,
                chat_history_info=chat_history_info,
                last_event_info=last_event_info,
                interpretation_note=interpretation_note
            )
            
            user_prompt = f"""Извлеки информацию из сообщения: "{text}"

ВАЖНО для дат и времени:
- Распознавай даты в формате "N-го месяца": "19-го января", "3-е февраля", "1-го марта" и т.д.
- Примеры событий с датами:
  * "фотосессия в 17:00 19-го января" → intent="event", title="Фотосессия", start_time="2026-01-19T17:00:00"
  * "встреча с Настей 3-е февраля в 14:00" → intent="event", title="Встреча с Настей", start_time="2026-02-03T14:00:00"
  * "зарядка 15 января в 7 утра" → intent="event", title="Зарядка", start_time="2026-01-15T07:00:00"

ВАЖНО для диапазонов времени:
- Если есть "с X до Y" / "X-Y" / "X до Y часов" / "от X до Y" / "с X часов до Y" → извлекай оба: start_time (начало) и end_time (окончание)
- Если указано только время без даты (например, "с 14 до 18"), используй сегодняшнюю дату для обоих времен
- Если указано только число (например, "14", "18"), интерпретируй как часы (14:00, 18:00)
- Примеры: "зарядка с 11 утра до 15 часов" → start_time="11:00", end_time="15:00" (на ту же дату)
          "встреча завтра с 10:00 до 12:00" → start_time="завтра 10:00", end_time="завтра 12:00"
          "работа с 9 до 18" → start_time="09:00", end_time="18:00" (на сегодня)
          "с 14 до 18" → start_time="14:00", end_time="18:00" (на сегодня)
          "с 14 часов до 18" → start_time="14:00", end_time="18:00" (на сегодня)
          "завтра с 14 до 18" → start_time="завтра 14:00", end_time="завтра 18:00"

ВАЖНО для контекста:
- Если в сообщении есть "это", "его", "её", "то" → refers_to_last_event: true
- Если есть глагол операции ("удали", "перенеси", "измени") → извлекай operation_verb
- Если есть относительный модификатор ("на час позже", "+30 минут") → извлекай relative_time_modification
- Примеры:
  * "удали это" → intent="delete", refers_to_last_event: true, operation_verb: "удали"
  * "перенеси на час позже" → intent="update", refers_to_last_event: true, relative_time_modification: "+1 hour", operation_verb: "перенеси"
  * "измени время на 15:00" → intent="update", refers_to_last_event: true, new_time: "15:00", operation_verb: "измени"
  * "сдвинь на завтра" → intent="update", refers_to_last_event: true, new_date: "завтра", operation_verb: "сдвинь"

Верни JSON:
{{
    "intent": "event|reminder|note|list_events|delete_all|delete_by_period|delete_many|delete_by_pattern|add_reminder|add_note|create_many|update|update_many|delete|search|list_notes|delete_note|unknown",
    "title": "краткое название или null",
    "titles": ["название1", "название2"] или null (для delete_many, create_many),
    "description": "полное описание или null",
    "start_time": "YYYY-MM-DDTHH:MM:SS или null (время начала события, если указан диапазон - это начало)",
    "end_time": "YYYY-MM-DDTHH:MM:SS или null (время окончания события, если указан диапазон - это окончание)",
    "location": "место или null",
    "priority": 0-5,
    "has_explicit_time": true/false,
    "confidence": 0.0-1.0,
    "time_period": "today|tomorrow|week|month|all" или null (для list_events, delete_by_period),
    "pattern": "паттерн поиска" или null (для delete_by_pattern),
    "reminder_intervals": ["2 hours", "1 hour", "1.5 hours", "30 minutes"] или null (для add_reminder И для event, когда указаны несколько напоминаний),
    "note_text": "текст заметки" или null (только для add_note),
    "update_fields": {{"time": "16:00", "location": "новый офис"}} или null (для update),
    "refers_to_last_event": true/false (относится ли запрос к последнему событию),
    "is_recurring": true/false (повторяющееся ли событие, default false),
    "recurrence_type": "daily|weekly|monthly" или null (тип повторения),
    "interval": число (каждые N дней/недель/месяцев, default 1) или null,
    "days_of_week": ["MO", "TU", "WE", "TH", "FR", "SA", "SU"] или null (дни недели для weekly),
    "day_of_month": число 1-31 или null (число месяца для monthly),
    "recurrence_end_date": "YYYY-MM-DDTHH:MM:SS" или null (дата окончания повторений),
    "recurrence_count": число или null (количество повторений)
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
            
            # Обработка диапазонов времени
            start_time = result.get("start_time")
            end_time = result.get("end_time")
            
            if start_time and end_time:
                # Если оба времени указаны, убеждаемся, что end_time >= start_time
                # Если end_time раньше start_time (например, разница в дате не учтена), корректируем
                if end_time < start_time:
                    # Предполагаем, что end_time должен быть в тот же день, что и start_time
                    # Используем ту же дату что и start_time, но с временем из end_time
                    end_time = start_time.replace(hour=end_time.hour, minute=end_time.minute, second=end_time.second, microsecond=end_time.microsecond)
                    # Если все равно меньше (например, 02:00 < 23:00 предыдущего дня), добавляем день
                    if end_time < start_time:
                        end_time = end_time + timedelta(days=1)
                    result["end_time"] = end_time
                    logger.info(f"Скорректирован end_time для диапазона: start={start_time}, end={end_time}")
                else:
                    # Если end_time >= start_time, но даты разные, убеждаемся что end_time в правильном формате
                    # Если end_time имеет только время без даты (сегодняшняя дата), используем дату start_time
                    if end_time.date() == now.date() and start_time.date() != now.date():
                        # end_time имеет сегодняшнюю дату, но start_time - другую, переносим end_time на дату start_time
                        end_time = start_time.replace(hour=end_time.hour, minute=end_time.minute, second=end_time.second, microsecond=end_time.microsecond)
                        result["end_time"] = end_time
                        logger.info(f"Скорректирована дата end_time для диапазона: start={start_time}, end={end_time}")
            elif start_time and not end_time:
                # Если есть start_time но нет end_time, добавляем час по умолчанию
                result["end_time"] = start_time + timedelta(hours=1)
                logger.info(f"Добавлен end_time по умолчанию (1 час после start_time): {result['end_time']}")
            
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
        result = {
            "intent": "note",
            "title": text[:50],
            "description": text,
            "start_time": None,
            "end_time": None,
            "location": None,
            "priority": 0,
            "has_explicit_time": False,
            "confidence": 0.3,
            "_original_text": text  # Сохраняем оригинальный текст для fallback логики
        }
        return result
    
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

    def _detect_missing_fields(self, extracted_data: Dict) -> List[str]:
        """
        Определить какие поля отсутствуют для выполнения действия.

        Args:
            extracted_data: Извлеченные данные из NLP

        Returns:
            Список названий недостающих полей в порядке приоритета
        """
        missing = []
        intent = extracted_data.get('intent', 'unknown')

        # Для создания событий и напоминаний
        if intent in ['event', 'reminder']:
            # Время - критично
            if not extracted_data.get('start_time'):
                missing.append('time')

            # Название - желательно
            if not extracted_data.get('title'):
                missing.append('title')

        # Для удаления
        elif intent == 'delete':
            if not extracted_data.get('title') and not extracted_data.get('event_id'):
                missing.append('title')

        # Для обновления
        elif intent == 'update':
            if not extracted_data.get('title') and not extracted_data.get('event_id'):
                missing.append('title')

        return missing

    def generate_clarification_question(self, missing_field: str, context: Dict) -> str:
        """
        Сгенерировать естественный вопрос для уточнения.

        Args:
            missing_field: Название недостающего поля ('time', 'title', etc.)
            context: Контекст с частично собранными данными

        Returns:
            Текст вопроса для пользователя
        """
        import random

        questions = {
            'time': [
                "Во сколько? 🕐",
                "В какое время это должно быть?",
                "Когда планируешь?",
                "На какое время запланируем?"
            ],
            'title': [
                "О чём событие? 📝",
                "Как назовём это событие?",
                "Что именно планируешь?",
                "Что это за событие?"
            ],
            'location': [
                "Где это будет? 📍",
                "Какое место?",
                "Где планируется?"
            ],
            'confirmation': [
                "Всё верно? Создать событие? ✅",
                "Подтверждаешь? ✅",
                "Создать это событие? ✅"
            ],
            'selection': [
                "Какой вариант?",
                "Выбери номер или название"
            ]
        }

        question_list = questions.get(missing_field, ["Уточни, пожалуйста"])
        return random.choice(question_list)

    async def extract_from_answer(
        self,
        text: str,
        awaiting_field: str,
        partial_data: Dict,
        user_timezone: str = "Europe/Moscow"
    ) -> Dict:
        """
        Извлечь значение поля из ответа пользователя на уточняющий вопрос.

        Args:
            text: Ответ пользователя
            awaiting_field: Поле, которое ожидалось ('time', 'title', etc.)
            partial_data: Частично собранные данные
            user_timezone: Часовой пояс пользователя

        Returns:
            Словарь с извлеченным полем
        """
        if awaiting_field == 'time':
            # Парсим время из ответа
            return await self._parse_time_answer(text, partial_data, user_timezone)

        elif awaiting_field == 'title':
            # Просто берем текст как название
            return {'title': text.strip()}

        elif awaiting_field == 'location':
            # Берем текст как место
            return {'location': text.strip()}

        elif awaiting_field == 'confirmation':
            # Да/нет ответ
            return {'confirmed': self._parse_yes_no(text)}

        elif awaiting_field == 'selection':
            # Пользователь выбрал номер или название
            # Пытаемся распарсить как число
            text_stripped = text.strip()
            if text_stripped.isdigit():
                return {'selected_index': int(text_stripped) - 1}  # -1 для 0-based индекса
            else:
                return {'selected_text': text_stripped}

        else:
            # Неизвестное поле - возвращаем как есть
            return {awaiting_field: text.strip()}

    async def _parse_time_answer(self, text: str, partial_data: Dict, user_timezone: str) -> Dict:
        """
        Парсить время из ответа пользователя.

        Args:
            text: Ответ пользователя (например, "15:00", "завтра в 10")
            partial_data: Частично собранные данные (может содержать дату)
            user_timezone: Часовой пояс

        Returns:
            Словарь с полем start_time
        """
        # Используем существующий парсер времени
        tz = pytz.timezone(user_timezone)
        now = datetime.now(tz)

        # Проверяем есть ли уже дата в partial_data
        existing_date = partial_data.get('start_time')

        # Если есть дата но без времени, комбинируем с новым временем
        if existing_date:
            try:
                # Пытаемся распарсить только время из ответа
                parsed_time = dateparser.parse(
                    text,
                    languages=['ru'],
                    settings={
                        'RELATIVE_BASE': now,
                        'TIMEZONE': user_timezone,
                        'RETURN_AS_TIMEZONE_AWARE': True
                    }
                )

                if parsed_time:
                    # Если распарсили - берем время от parsed, дату от existing
                    if isinstance(existing_date, str):
                        existing_dt = datetime.fromisoformat(existing_date.replace('Z', '+00:00'))
                    else:
                        existing_dt = existing_date

                    combined = existing_dt.replace(
                        hour=parsed_time.hour,
                        minute=parsed_time.minute,
                        second=0,
                        microsecond=0
                    )

                    return {
                        'start_time': combined,
                        'has_explicit_time': True
                    }
            except:
                pass

        # Парсим текст как полную дату-время
        parsed = dateparser.parse(
            text,
            languages=['ru'],
            settings={
                'RELATIVE_BASE': now,
                'TIMEZONE': user_timezone,
                'RETURN_AS_TIMEZONE_AWARE': True
            }
        )

        if parsed:
            return {
                'start_time': parsed,
                'has_explicit_time': True
            }
        else:
            # Не смогли распарсить - возвращаем как есть для дальнейшей обработки
            return {'time_text': text}

    def _parse_yes_no(self, text: str) -> bool:
        """
        Распарсить да/нет ответ.

        Args:
            text: Ответ пользователя

        Returns:
            True если да, False если нет
        """
        text_lower = text.lower().strip()

        yes_words = ['да', 'yes', 'y', 'ок', 'ok', 'окей', 'ага', 'угу', 'конечно', 'верно', 'подтверждаю', '+', '✅']
        no_words = ['нет', 'no', 'n', 'не', 'отмена', 'cancel', 'неа', 'нope', '-', '❌']

        for word in yes_words:
            if word in text_lower:
                return True

        for word in no_words:
            if word in text_lower:
                return False

        # По умолчанию считаем "да" если не распознали
        return True

