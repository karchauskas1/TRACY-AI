"""
==============================================================================
ENTITY_RESOLVER.PY - ПОИСК И РАЗРЕШЕНИЕ СОБЫТИЙ
==============================================================================

Находит события по различным критериям:
- По ID (из reply контекста)
- По названию / ключевым словам
- По дате
- По близости текста (fuzzy matching)

==============================================================================
"""
import re
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, TYPE_CHECKING
import dateparser
import pytz

if TYPE_CHECKING:
    from tracy.intelligence.intent_classifier import TargetEvent

logger = logging.getLogger(__name__)


@dataclass
class ResolvedEntity:
    """Результат разрешения целевого события."""
    # Найденные события
    events: List[Dict[str, Any]]

    # Статус поиска
    found: bool = False
    single_match: bool = False
    multiple_matches: bool = False
    no_matches: bool = False

    # Причина (для отладки)
    search_method: Optional[str] = None
    search_query: Optional[str] = None

    @property
    def event(self) -> Optional[Dict[str, Any]]:
        """Вернуть единственное событие если найдено ровно одно."""
        if self.single_match and self.events:
            return self.events[0]
        return None


class EntityResolver:
    """
    Находит события по различным критериям.
    """

    def __init__(self, db, user_timezone: str = "Europe/Moscow"):
        """
        Args:
            db: Database instance
            user_timezone: Часовой пояс пользователя по умолчанию
        """
        self._db = db
        self._default_tz = user_timezone
        logger.info("EntityResolver инициализирован")

    async def resolve(
        self,
        user_id: int,
        target: 'TargetEvent',
        user_timezone: Optional[str] = None
    ) -> ResolvedEntity:
        """
        Найти событие по целевому описанию.

        Args:
            user_id: ID пользователя
            target: Описание целевого события
            user_timezone: Часовой пояс пользователя

        Returns:
            ResolvedEntity с найденными событиями
        """
        tz = user_timezone or self._default_tz

        # 1. Если есть конкретный event_id - ищем по нему
        if target.event_id:
            return await self._resolve_by_id(user_id, target.event_id)

        # 2. Если use_last_event - берём последнее созданное
        if target.use_last_event:
            return await self._resolve_last_event(user_id)

        # 3. Если есть search_query - ищем по названию
        if target.search_query:
            result = await self._resolve_by_query(user_id, target.search_query, tz)
            if result.found:
                return result

        # 4. Если есть date_reference - ищем по дате
        if target.date_reference:
            result = await self._resolve_by_date(user_id, target.date_reference, tz)
            if result.found:
                return result

        # 5. Ничего не нашли
        return ResolvedEntity(
            events=[],
            no_matches=True,
            search_method="all_methods_failed",
            search_query=target.search_query or target.date_reference
        )

    async def _resolve_by_id(self, user_id: int, event_id: int) -> ResolvedEntity:
        """Найти событие по ID."""
        try:
            event = self._db.get_event(event_id)

            if event and event.get('user_id') == user_id:
                return ResolvedEntity(
                    events=[event],
                    found=True,
                    single_match=True,
                    search_method="by_id",
                    search_query=str(event_id)
                )

            return ResolvedEntity(
                events=[],
                no_matches=True,
                search_method="by_id",
                search_query=str(event_id)
            )

        except Exception as e:
            logger.error(f"Ошибка поиска по ID {event_id}: {e}")
            return ResolvedEntity(events=[], no_matches=True)

    async def _resolve_last_event(self, user_id: int) -> ResolvedEntity:
        """Найти последнее созданное событие."""
        try:
            # Получаем события отсортированные по дате создания
            events = self._db.get_upcoming_events(user_id, days=30)

            if events:
                # Сортируем по ID (последний = самый большой ID)
                events.sort(key=lambda x: x.get('id', 0), reverse=True)
                return ResolvedEntity(
                    events=[events[0]],
                    found=True,
                    single_match=True,
                    search_method="last_event"
                )

            return ResolvedEntity(
                events=[],
                no_matches=True,
                search_method="last_event"
            )

        except Exception as e:
            logger.error(f"Ошибка получения последнего события: {e}")
            return ResolvedEntity(events=[], no_matches=True)

    async def _resolve_by_query(
        self,
        user_id: int,
        query: str,
        timezone: str
    ) -> ResolvedEntity:
        """Найти события по поисковому запросу (название/ключевые слова)."""
        try:
            # Получаем все предстоящие события
            all_events = self._db.get_upcoming_events(user_id, days=90)

            if not all_events:
                return ResolvedEntity(
                    events=[],
                    no_matches=True,
                    search_method="by_query",
                    search_query=query
                )

            # Ищем совпадения
            matching_events = self._fuzzy_search(all_events, query)

            if not matching_events:
                return ResolvedEntity(
                    events=[],
                    no_matches=True,
                    search_method="by_query",
                    search_query=query
                )

            if len(matching_events) == 1:
                return ResolvedEntity(
                    events=matching_events,
                    found=True,
                    single_match=True,
                    search_method="by_query",
                    search_query=query
                )

            return ResolvedEntity(
                events=matching_events,
                found=True,
                multiple_matches=True,
                search_method="by_query",
                search_query=query
            )

        except Exception as e:
            logger.error(f"Ошибка поиска по запросу '{query}': {e}")
            return ResolvedEntity(events=[], no_matches=True)

    async def _resolve_by_date(
        self,
        user_id: int,
        date_reference: str,
        timezone: str
    ) -> ResolvedEntity:
        """Найти события по ссылке на дату."""
        try:
            # Парсим дату
            tz = pytz.timezone(timezone)
            now = datetime.now(tz)

            parsed_date = dateparser.parse(
                date_reference,
                settings={
                    'TIMEZONE': timezone,
                    'RETURN_AS_TIMEZONE_AWARE': True,
                    'RELATIVE_BASE': now,
                    'PREFER_DATES_FROM': 'future'
                }
            )

            if not parsed_date:
                return ResolvedEntity(
                    events=[],
                    no_matches=True,
                    search_method="by_date",
                    search_query=date_reference
                )

            # Ищем события на эту дату
            target_date = parsed_date.date()
            all_events = self._db.get_upcoming_events(user_id, days=90)

            matching_events = []
            for event in all_events:
                event_date_str = event.get('start_time', '')
                if event_date_str:
                    try:
                        event_date = datetime.fromisoformat(
                            event_date_str.replace('Z', '+00:00')
                        ).date()
                        if event_date == target_date:
                            matching_events.append(event)
                    except (ValueError, AttributeError):
                        pass

            if not matching_events:
                return ResolvedEntity(
                    events=[],
                    no_matches=True,
                    search_method="by_date",
                    search_query=date_reference
                )

            if len(matching_events) == 1:
                return ResolvedEntity(
                    events=matching_events,
                    found=True,
                    single_match=True,
                    search_method="by_date",
                    search_query=date_reference
                )

            return ResolvedEntity(
                events=matching_events,
                found=True,
                multiple_matches=True,
                search_method="by_date",
                search_query=date_reference
            )

        except Exception as e:
            logger.error(f"Ошибка поиска по дате '{date_reference}': {e}")
            return ResolvedEntity(events=[], no_matches=True)

    def _fuzzy_search(
        self,
        events: List[Dict[str, Any]],
        query: str
    ) -> List[Dict[str, Any]]:
        """
        Fuzzy поиск событий по запросу.
        Использует несколько стратегий для максимальной гибкости.
        """
        query_lower = query.lower().strip()
        query_words = set(query_lower.split())

        results = []
        for event in events:
            title = (event.get('title') or '').lower()
            description = (event.get('description') or '').lower()
            full_text = f"{title} {description}"

            score = self._calculate_match_score(query_lower, query_words, title, full_text)

            if score > 0:
                results.append((score, event))

        # Сортируем по релевантности
        results.sort(key=lambda x: x[0], reverse=True)

        # Возвращаем события с достаточным score
        return [event for score, event in results if score >= 0.3]

    def _calculate_match_score(
        self,
        query: str,
        query_words: set,
        title: str,
        full_text: str
    ) -> float:
        """
        Рассчитать score совпадения.

        Returns:
            Score от 0.0 до 1.0
        """
        score = 0.0

        # 1. Точное совпадение с названием
        if query == title:
            return 1.0

        # 2. Название содержит запрос
        if query in title:
            score = max(score, 0.9)

        # 3. Запрос содержит название
        if title in query:
            score = max(score, 0.8)

        # 4. Все слова запроса есть в названии
        title_words = set(title.split())
        if query_words and query_words.issubset(title_words):
            score = max(score, 0.7)

        # 5. Большинство слов запроса есть в названии
        if query_words:
            matching_words = query_words.intersection(title_words)
            word_ratio = len(matching_words) / len(query_words)
            if word_ratio >= 0.5:
                score = max(score, 0.5 * word_ratio + 0.2)

        # 6. Частичное совпадение (начало слов)
        for q_word in query_words:
            for t_word in title_words:
                if t_word.startswith(q_word) or q_word.startswith(t_word):
                    if len(q_word) >= 3 and len(t_word) >= 3:
                        score = max(score, 0.4)

        # 7. Поиск в полном тексте (включая описание)
        if score < 0.3 and query in full_text:
            score = max(score, 0.3)

        return score

    async def search_events(
        self,
        user_id: int,
        query: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Универсальный поиск событий.

        Args:
            user_id: ID пользователя
            query: Поисковый запрос (опционально)
            date_from: Начало периода (опционально)
            date_to: Конец периода (опционально)
            limit: Максимальное количество результатов

        Returns:
            Список найденных событий
        """
        try:
            # Получаем все события
            days = 90
            if date_to:
                days = max(90, (date_to - datetime.now()).days + 7)

            events = self._db.get_upcoming_events(user_id, days=days)

            if not events:
                return []

            results = events

            # Фильтруем по дате
            if date_from or date_to:
                results = self._filter_by_date_range(results, date_from, date_to)

            # Фильтруем по запросу
            if query:
                results = self._fuzzy_search(results, query)

            return results[:limit]

        except Exception as e:
            logger.error(f"Ошибка поиска событий: {e}")
            return []

    def _filter_by_date_range(
        self,
        events: List[Dict[str, Any]],
        date_from: Optional[datetime],
        date_to: Optional[datetime]
    ) -> List[Dict[str, Any]]:
        """Фильтровать события по диапазону дат."""
        results = []

        for event in events:
            event_date_str = event.get('start_time', '')
            if not event_date_str:
                continue

            try:
                event_date = datetime.fromisoformat(
                    event_date_str.replace('Z', '+00:00')
                )

                if date_from and event_date < date_from:
                    continue
                if date_to and event_date > date_to:
                    continue

                results.append(event)

            except (ValueError, AttributeError):
                pass

        return results
