"""Интеграция с Google Calendar через OAuth."""
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dateutil import parser as dateutil_parser
from google.auth.transport.requests import Request
import config

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/calendar']


class GoogleCalendar:
    """Класс для работы с Google Calendar."""
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.token_path = os.path.join(config.TOKENS_DIR, f"google_token_{user_id}.json")
        self.service = None
    
    def get_credentials(self) -> Optional[Credentials]:
        """Получить credentials пользователя."""
        if not os.path.exists(self.token_path):
            return None
        
        try:
            from google.auth.transport.requests import Request
            creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
            return creds
        except Exception as e:
            logger.error(f"Ошибка загрузки credentials: {e}")
            return None
    
    def save_credentials(self, credentials: Credentials):
        """Сохранить credentials."""
        os.makedirs(os.path.dirname(self.token_path), exist_ok=True)
        with open(self.token_path, 'w') as token:
            token.write(credentials.to_json())
    
    def get_authorization_url(self) -> str:
        """Получить URL для OAuth авторизации."""
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": config.GOOGLE_CLIENT_ID,
                    "client_secret": config.GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [config.GOOGLE_REDIRECT_URI]
                }
            },
            SCOPES,
            redirect_uri=config.GOOGLE_REDIRECT_URI
        )
        
        authorization_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true'
        )
        
        # Сохраняем flow в сессию (в продакшене использовать Redis/DB)
        self._save_flow_state(flow)
        
        return authorization_url
    
    def handle_callback(self, authorization_response: str) -> bool:
        """
        Обработать OAuth callback.
        
        Args:
            authorization_response: URL с кодом авторизации
        """
        try:
            from urllib.parse import urlparse, parse_qs
            
            # Извлекаем код из URL
            if authorization_response.startswith('http'):
                parsed_url = urlparse(authorization_response)
                query_params = parse_qs(parsed_url.query)
                auth_code = query_params.get('code', [None])[0]
            else:
                # Если передан только код
                auth_code = authorization_response
            
            if not auth_code:
                logger.error("Не найден код авторизации в URL")
                return False
            
            # Создаем новый flow для обмена кода на токен
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": config.GOOGLE_CLIENT_ID,
                        "client_secret": config.GOOGLE_CLIENT_SECRET,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [config.GOOGLE_REDIRECT_URI]
                    }
                },
                SCOPES,
                redirect_uri=config.GOOGLE_REDIRECT_URI
            )
            
            # Обмениваем код на токен
            flow.fetch_token(code=auth_code)
            
            credentials = flow.credentials
            self.save_credentials(credentials)
            
            logger.info(f"Google Calendar успешно подключен для пользователя {self.user_id}")
            return True
        except Exception as e:
            logger.error(f"Ошибка обработки callback: {e}", exc_info=True)
            return False
    
    def _save_flow_state(self, flow: Flow):
        """Сохранить состояние flow (упрощенная версия)."""
        # В продакшене использовать Redis или сессию
        pass
    
    def _load_flow_state(self) -> Flow:
        """Загрузить состояние flow."""
        return Flow.from_client_config(
            {
                "web": {
                    "client_id": config.GOOGLE_CLIENT_ID,
                    "client_secret": config.GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [config.GOOGLE_REDIRECT_URI]
                }
            },
            SCOPES,
            redirect_uri=config.GOOGLE_REDIRECT_URI
        )
    
    def get_service(self):
        """Получить Google Calendar service."""
        if self.service:
            return self.service
        
        creds = self.get_credentials()
        if not creds:
            raise ValueError("Не авторизован в Google Calendar")
        
        self.service = build('calendar', 'v3', credentials=creds)
        return self.service
    
    def create_event(self, title: str, description: Optional[str] = None,
                    start_time: Optional[datetime] = None, end_time: Optional[datetime] = None,
                    location: Optional[str] = None, timezone: str = "Europe/Moscow") -> Optional[Dict]:
        """Создать событие в Google Calendar."""
        try:
            service = self.get_service()
            
            event = {
                'summary': title,
            }
            
            if description:
                event['description'] = description
            
            if location:
                event['location'] = location
            
            if start_time and end_time:
                event['start'] = {
                    'dateTime': start_time.isoformat(),
                    'timeZone': timezone,
                }
                event['end'] = {
                    'dateTime': end_time.isoformat(),
                    'timeZone': timezone,
                }
                
                # Добавляем напоминание за 15 минут до события
                event['reminders'] = {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'popup', 'minutes': 15}
                    ]
                }
            elif start_time:
                # Если только start_time, делаем событие на весь день
                event['start'] = {
                    'date': start_time.strftime('%Y-%m-%d'),
                }
                event['end'] = {
                    'date': (start_time + timedelta(days=1)).strftime('%Y-%m-%d'),
                }
            
            created_event = service.events().insert(
                calendarId='primary',
                body=event
            ).execute()
            
            logger.info(f"Создано событие в Google Calendar: {created_event.get('id')}")
            return created_event
        
        except HttpError as e:
            logger.error(f"Ошибка создания события в Google Calendar: {e}")
            return None
        except Exception as e:
            logger.error(f"Неожиданная ошибка: {e}")
            return None
    
    def update_event(self, event_id: str, **kwargs) -> Optional[Dict]:
        """Обновить событие."""
        try:
            service = self.get_service()
            
            # Получить существующее событие
            event = service.events().get(
                calendarId='primary',
                eventId=event_id
            ).execute()
            
            # Обновить поля
            if 'title' in kwargs:
                event['summary'] = kwargs['title']
            if 'description' in kwargs:
                event['description'] = kwargs['description']
            if 'location' in kwargs:
                event['location'] = kwargs['location']
            if 'start_time' in kwargs and 'end_time' in kwargs:
                timezone = kwargs.get('timezone', 'Europe/Moscow')
                event['start'] = {
                    'dateTime': kwargs['start_time'].isoformat(),
                    'timeZone': timezone,
                }
                event['end'] = {
                    'dateTime': kwargs['end_time'].isoformat(),
                    'timeZone': timezone,
                }
            
            # Обновить напоминания, если переданы
            if 'reminders' in kwargs:
                event['reminders'] = {
                    'useDefault': False,
                    'overrides': kwargs['reminders']
                }
            
            updated_event = service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=event
            ).execute()
            
            logger.info(f"Обновлено событие в Google Calendar: {event_id}")
            return updated_event
        
        except HttpError as e:
            logger.error(f"Ошибка обновления события: {e}")
            return None
    
    def delete_event(self, event_id: str) -> bool:
        """Удалить событие."""
        try:
            service = self.get_service()
            service.events().delete(
                calendarId='primary',
                eventId=event_id
            ).execute()
            
            logger.info(f"Удалено событие из Google Calendar: {event_id}")
            return True
        
        except HttpError as e:
            logger.error(f"Ошибка удаления события: {e}")
            return False
    
    def search_events(self, query: str, time_min: Optional[datetime] = None,
                     time_max: Optional[datetime] = None, max_results: int = 10) -> List[Dict]:
        """Поиск событий."""
        try:
            service = self.get_service()
            
            events_result = service.events().list(
                calendarId='primary',
                q=query,
                timeMin=time_min.isoformat() if time_min else None,
                timeMax=time_max.isoformat() if time_max else None,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            return events
        
        except HttpError as e:
            logger.error(f"Ошибка поиска событий: {e}")
            return []
    
    def get_event_ics(self, event_id: str) -> Optional[str]:
        """Получить событие в формате ICS."""
        try:
            service = self.get_service()
            event = service.events().get(
                calendarId='primary',
                eventId=event_id
            ).execute()
            
            # Формируем ICS файл
            from ics import Calendar, Event as ICSEvent
            from datetime import datetime
            
            ics_event = ICSEvent()
            ics_event.name = event.get('summary', 'Без названия')
            ics_event.description = event.get('description', '')
            ics_event.location = event.get('location', '')
            
            # Обрабатываем время
            start = event.get('start', {})
            end = event.get('end', {})
            
            if 'dateTime' in start:
                ics_event.begin = dateutil_parser.parse(start['dateTime'])
                ics_event.end = dateutil_parser.parse(end.get('dateTime', start['dateTime']))
            elif 'date' in start:
                # Событие на весь день
                ics_event.begin = dateutil_parser.parse(start['date']).date()
                end_date = dateutil_parser.parse(end.get('date', start['date']))
                ics_event.end = end_date.date()
            
            # Создаем календарь с одним событием
            calendar = Calendar(events=[ics_event])
            
            return str(calendar)
        
        except HttpError as e:
            logger.error(f"Ошибка получения события: {e}")
            return None
        except Exception as e:
            logger.error(f"Ошибка создания ICS: {e}")
            return None



