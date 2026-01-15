"""Движок повторяющихся событий."""
import logging
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional
import pytz


logger = logging.getLogger(__name__)


class RecurringEventsEngine:
    """Управление повторяющимися событиями."""

    def __init__(self, db):
        """
        Инициализация движка повторяющихся событий.

        Args:
            db: Экземпляр Database
        """
        self.db = db

    def create_recurring_event(
        self,
        user_id: int,
        event_template: Dict,
        recurrence_type: str,  # 'daily', 'weekly', 'monthly'
        interval: int = 1,
        days_of_week: Optional[List[str]] = None,  # ['MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU']
        day_of_month: Optional[int] = None,
        end_date: Optional[date] = None,
        count: Optional[int] = None  # количество повторений
    ) -> int:
        """
        Создать повторяющееся событие.

        Args:
            user_id: ID пользователя
            event_template: Шаблон события (title, description, start_time, end_time, location)
            recurrence_type: Тип повторения ('daily', 'weekly', 'monthly')
            interval: Интервал повторения (каждые N дней/недель/месяцев)
            days_of_week: Дни недели для weekly (например ['MO', 'WE', 'FR'])
            day_of_month: День месяца для monthly (1-31)
            end_date: Дата окончания повторений (опционально)
            count: Количество повторений (опционально)

        Returns:
            ID созданного паттерна повторения
        """
        logger.info(f"📅 Создание повторяющегося события: type={recurrence_type}, interval={interval}")

        # 1. Создаём базовое событие-шаблон (status='template')
        # Временно сохраняем событие как обычное, чтобы получить ID
        template_id = self.db.save_event(
            user_id=user_id,
            title=event_template.get('title', 'Повторяющееся событие'),
            description=event_template.get('description'),
            start_time=event_template.get('start_time'),
            end_time=event_template.get('end_time'),
            location=event_template.get('location'),
            all_day=event_template.get('all_day', False),
            priority=event_template.get('priority', 3)
        )

        logger.info(f"✅ Создан шаблон события с ID: {template_id}")

        # 2. Сохраняем паттерн повторения в БД
        # TODO: Добавить метод save_recurring_pattern в database.py
        # pattern_id = self.db.save_recurring_pattern(
        #     user_id=user_id,
        #     event_template_id=template_id,
        #     recurrence_type=recurrence_type,
        #     interval=interval,
        #     days_of_week=days_of_week,
        #     day_of_month=day_of_month,
        #     start_date=event_template.get('start_time').date() if event_template.get('start_time') else date.today(),
        #     end_date=end_date
        # )

        # 3. Генерируем экземпляры событий (первые 90 дней)
        # instances = self._generate_instances(pattern_id, days=90)

        # 4. Создаём события в БД
        # for instance_date in instances:
        #     event_id = self._create_instance(pattern_id, template_id, instance_date)

        # Пока возвращаем template_id (TODO: вернуть pattern_id когда таблицы будут готовы)
        return template_id

    def _generate_instances(
        self,
        pattern_id: int,
        days: int = 90
    ) -> List[date]:
        """
        Сгенерировать даты экземпляров событий.

        Args:
            pattern_id: ID паттерна повторения
            days: На сколько дней вперёд генерировать (по умолчанию 90)

        Returns:
            Список дат для создания экземпляров событий
        """
        # TODO: Реализовать после добавления таблиц в database.py
        # pattern = self.db.get_recurring_pattern(pattern_id)
        instances = []

        # Пример логики для daily:
        # if pattern['recurrence_type'] == 'daily':
        #     current_date = pattern['start_date']
        #     while len(instances) < (days // pattern['interval']):
        #         instances.append(current_date)
        #         current_date += timedelta(days=pattern['interval'])

        return instances

    def _create_instance(
        self,
        pattern_id: int,
        template_id: int,
        occurrence_date: date
    ) -> int:
        """
        Создать экземпляр повторяющегося события на конкретную дату.

        Args:
            pattern_id: ID паттерна повторения
            template_id: ID шаблона события
            occurrence_date: Дата этого экземпляра

        Returns:
            ID созданного события
        """
        # TODO: Реализовать после добавления таблиц
        # 1. Получить шаблон события
        # template = self.db.get_event_by_id(template_id)

        # 2. Создать новое событие на основе шаблона
        # event_id = self.db.save_event(
        #     user_id=template['user_id'],
        #     title=template['title'],
        #     start_time=datetime.combine(occurrence_date, template['start_time'].time()),
        #     ...
        # )

        # 3. Сохранить связь instance -> pattern
        # self.db.save_recurring_instance(pattern_id, event_id, occurrence_date)

        # return event_id
        return 0

    def add_exception(
        self,
        pattern_id: int,
        exception_date: date
    ):
        """
        Добавить исключение (пропустить дату в повторениях).

        Args:
            pattern_id: ID паттерна повторения
            exception_date: Дата исключения
        """
        # TODO: Реализовать после добавления таблиц
        # self.db.add_recurring_exception(pattern_id, exception_date)
        # instance = self.db.get_recurring_instance(pattern_id, exception_date)
        # if instance:
        #     self.db.delete_event(instance['event_id'])
        pass

    def update_recurring_event(
        self,
        pattern_id: int,
        update_type: str,  # 'this', 'future', 'all'
        **changes
    ):
        """
        Обновить повторяющееся событие.

        Args:
            pattern_id: ID паттерна повторения
            update_type: Тип обновления:
                - 'this': только текущий экземпляр (создаёт исключение)
                - 'future': текущий и все будущие (новый паттерн)
                - 'all': все экземпляры (обновляет шаблон)
            **changes: Изменения для применения
        """
        # TODO: Реализовать после добавления таблиц
        if update_type == 'this':
            # Обновить только один экземпляр (создать исключение + новое событие)
            pass
        elif update_type == 'future':
            # Создать новый паттерн с updated start_date
            pass
        elif update_type == 'all':
            # Обновить шаблон и пересоздать все будущие экземпляры
            pass
