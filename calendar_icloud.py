"""Интеграция с iCloud Calendar через CalDAV."""
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from caldav import DAVClient, Calendar
import config

logger = logging.getLogger(__name__)


class ICloudCalendar:
    """Класс для работы с iCloud Calendar через CalDAV."""
    
    def __init__(self, user_id: int, caldav_url: str, username: str, password: str):
        """
        Инициализация CalDAV клиента.
        
        Args:
            user_id: ID пользователя
            caldav_url: URL CalDAV сервера (для iCloud: https://caldav.icloud.com)
            username: Apple ID
            password: App-specific password (не основной пароль!)
        """
        self.user_id = user_id
        self.caldav_url = caldav_url
        self.username = username
        self.password = password
        self.client = None
        self.calendar = None
    
    def connect(self) -> bool:
        """Подключиться к CalDAV серверу."""
        try:
            self.client = DAVClient(
                url=self.caldav_url,
                username=self.username,
                password=self.password
            )
            
            # Получить главный календарь
            principal = self.client.principal()
            calendars = principal.calendars()
            
            if calendars:
                self.calendar = calendars[0]  # Берем первый календарь
                logger.info(f"Подключено к iCloud Calendar для пользователя {self.user_id}")
                return True
            else:
                logger.warning("Не найдено календарей")
                return False
        
        except Exception as e:
            logger.error(f"Ошибка подключения к iCloud Calendar: {e}")
            return False
    
    def create_event(self, title: str, description: Optional[str] = None,
                    start_time: Optional[datetime] = None, end_time: Optional[datetime] = None,
                    location: Optional[str] = None) -> Optional[str]:
        """Создать событие в iCloud Calendar."""
        try:
            if not self.calendar:
                if not self.connect():
                    return None
            
            # Формируем VEVENT в формате iCalendar
            from ics import Event, Calendar as ICalCalendar
            
            event = Event()
            event.name = title
            event.begin = start_time if start_time else datetime.now()
            event.end = end_time if end_time else event.begin.replace(hour=event.begin.hour + 1)
            
            if description:
                event.description = description
            
            if location:
                event.location = location
            
            # Добавляем напоминание за 15 минут до события
            if start_time:
                from ics.alarm import DisplayAlarm
                alarm = DisplayAlarm(trigger=timedelta(minutes=-15))
                event.alarms = [alarm]
            
            # Сохраняем в календарь
            calendar_obj = ICalCalendar(events=[event])
            vcal = str(calendar_obj)
            
            # CalDAV требует уникальный UID
            event_result = self.calendar.save_event(vcal)
            
            logger.info(f"Создано событие в iCloud Calendar")
            # Извлекаем UID из созданного события
            return event.uid
        
        except Exception as e:
            logger.error(f"Ошибка создания события в iCloud Calendar: {e}")
            return None
    
    def update_event(self, event_uid: str, **kwargs) -> bool:
        """Обновить событие по UID."""
        try:
            if not self.calendar:
                if not self.connect():
                    return False
            
            # Найти событие по UID
            # CalDAV поиск по UID требует другого подхода
            events = self.calendar.events()
            target_event = None
            
            for event in events:
                try:
                    import icalendar
                    ical = icalendar.Calendar.from_ical(event.data)
                    for component in ical.walk():
                        if component.name == "VEVENT":
                            uid = str(component.get('uid', ''))
                            if uid == event_uid:
                                target_event = (event, component)
                                break
                    if target_event:
                        break
                except Exception:
                    continue
            
            if not target_event:
                logger.warning(f"Событие {event_uid} не найдено")
                return False
            
            event_obj, ical_event = target_event
            
            # Обновить поля
            if 'title' in kwargs:
                ical_event['summary'] = kwargs['title']
            if 'description' in kwargs:
                ical_event['description'] = kwargs['description']
            if 'location' in kwargs:
                ical_event['location'] = kwargs['location']
            if 'start_time' in kwargs:
                ical_event['dtstart'] = icalendar.vDatetime(kwargs['start_time'])
            if 'end_time' in kwargs:
                ical_event['dtend'] = icalendar.vDatetime(kwargs['end_time'])
            
            # Сохранить обновленное событие
            import icalendar
            calendar = icalendar.Calendar()
            calendar.add_component(ical_event)
            event_obj.data = calendar.to_ical()
            event_obj.save()
            
            logger.info(f"Обновлено событие в iCloud Calendar: {event_uid}")
            return True
        
        except Exception as e:
            logger.error(f"Ошибка обновления события: {e}", exc_info=True)
            return False
    
    def add_reminders_to_event(self, event_uid: str, reminder_intervals: List[str]) -> bool:
        """Добавить напоминания к существующему событию."""
        try:
            if not self.calendar:
                if not self.connect():
                    return False
            
            # Находим событие
            events = self.calendar.events()
            target_event = None
            
            for event in events:
                try:
                    import icalendar
                    ical = icalendar.Calendar.from_ical(event.data)
                    for component in ical.walk():
                        if component.name == "VEVENT":
                            uid = str(component.get('uid', ''))
                            if uid == event_uid:
                                target_event = (event, component)
                                break
                    if target_event:
                        break
                except Exception:
                    continue
            
            if not target_event:
                logger.warning(f"Событие {event_uid} не найдено для добавления напоминаний")
                return False
            
            event_obj, ical_event = target_event
            
            # Добавляем новые напоминания к существующим
            import re
            
            # Добавляем новые напоминания
            for interval in reminder_intervals:
                match = re.match(r'(\d+)\s*(hour|hours|minute|minutes|day|days)', interval.lower())
                if match:
                    num = int(match.group(1))
                    unit = match.group(2)
                    
                    # Создаем VALARM через icalendar
                    alarm = icalendar.Alarm()
                    alarm.add('action', 'DISPLAY')
                    alarm.add('description', 'Напоминание')
                    
                    # Устанавливаем триггер относительно времени начала события
                    if ical_event.get('dtstart'):
                        start_dt = ical_event['dtstart'].dt
                        if isinstance(start_dt, datetime):
                            # Вычисляем время напоминания
                            if unit.startswith('hour'):
                                delta_minutes = num * 60
                            elif unit.startswith('minute'):
                                delta_minutes = num
                            elif unit.startswith('day'):
                                delta_minutes = num * 24 * 60
                            else:
                                delta_minutes = 15
                            
                            # В iCalendar триггер указывается как отрицательное значение (минуты ДО события)
                            alarm.add('trigger', icalendar.vDuration(-timedelta(minutes=delta_minutes)))
                            ical_event.add_component(alarm)
            
            # Сохраняем обновленное событие
            import icalendar
            calendar = icalendar.Calendar()
            calendar.add_component(ical_event)
            event_obj.data = calendar.to_ical()
            event_obj.save()
            
            logger.info(f"Добавлены напоминания к событию в iCloud Calendar: {event_uid}")
            return True
        
        except Exception as e:
            logger.error(f"Ошибка добавления напоминаний: {e}", exc_info=True)
            return False
    
    def delete_event(self, event_uid: str) -> bool:
        """Удалить событие по UID."""
        try:
            if not self.calendar:
                if not self.connect():
                    return False
            
            # Найти событие по UID (аналогично update_event)
            events = self.calendar.events()
            target_event = None
            
            for event in events:
                try:
                    import icalendar
                    ical = icalendar.Calendar.from_ical(event.data)
                    for component in ical.walk():
                        if component.name == "VEVENT":
                            uid = str(component.get('uid', ''))
                            if uid == event_uid:
                                target_event = event
                                break
                    if target_event:
                        break
                except Exception:
                    continue
            
            if not target_event:
                logger.warning(f"Событие {event_uid} не найдено для удаления")
                return False
            
            # Удаляем событие
            target_event.delete()
            
            logger.info(f"✅ Событие {event_uid} успешно удалено из iCloud календаря")
            return True
        
        except Exception as e:
            logger.error(f"❌ Ошибка удаления события {event_uid} из iCloud календаря: {e}", exc_info=True)
            return False
    
    def search_events(self, query: str, time_min: Optional[datetime] = None,
                     time_max: Optional[datetime] = None, max_results: int = 10) -> List[Dict]:
        """Поиск событий."""
        try:
            if not self.calendar:
                if not self.connect():
                    return []
            
            # Поиск по временному диапазону
            if time_min and time_max:
                events = self.calendar.search(
                    start=time_min,
                    end=time_max
                )
            else:
                events = self.calendar.events()
            
            # Фильтрация по query (поиск в названии и описании)
            results = []
            for event in events[:max_results]:
                try:
                    import icalendar
                    ical = icalendar.Calendar.from_ical(event.data)
                    for component in ical.walk():
                        if component.name == "VEVENT":
                            summary = str(component.get('summary', ''))
                            description = str(component.get('description', ''))
                            
                            if not query or query.lower() in summary.lower() or query.lower() in description.lower():
                                dtstart = component.get('dtstart')
                                dtend = component.get('dtend')
                                results.append({
                                    'uid': str(component.get('uid', '')),
                                    'summary': summary,
                                    'description': description,
                                    'start': dtstart.dt if dtstart else None,
                                    'end': dtend.dt if dtend else None,
                                    'location': str(component.get('location', ''))
                                })
                            break
                except Exception as e:
                    logger.warning(f"Ошибка обработки события: {e}")
                    continue
            
            return results
        
        except Exception as e:
            logger.error(f"Ошибка поиска событий: {e}")
            return []
    
    def get_event_ics(self, event_uid: str) -> Optional[str]:
        """Получить событие в формате ICS."""
        try:
            if not self.calendar:
                if not self.connect():
                    return None
            
            events = self.calendar.events()
            
            for event in events:
                try:
                    import icalendar
                    ical = icalendar.Calendar.from_ical(event.data)
                    for component in ical.walk():
                        if component.name == "VEVENT":
                            uid = str(component.get('uid', ''))
                            if uid == event_uid:
                                return event.data
                except Exception:
                    continue
            
            return None
        
        except Exception as e:
            logger.error(f"Ошибка получения события: {e}")
            return None

