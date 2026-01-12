"""Сервис для работы с обратной связью через Google Sheets и Drive."""
import os
import logging
from datetime import datetime
from typing import Optional, Dict
from io import BytesIO
import json
import httpx
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request
import config

logger = logging.getLogger(__name__)

# Scopes для Google Sheets и Drive
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file'
]

# ID таблицы Google Sheets (будет настроен через переменную окружения)
FEEDBACK_SPREADSHEET_ID = os.getenv("FEEDBACK_SPREADSHEET_ID", "")

# Название листа по умолчанию
DEFAULT_SHEET_NAME = "Общий"

# Маппинг user_id -> название листа в таблице
# Парсим из переменной окружения (формат: "user_id1:лист1,user_id2:лист2")
def get_feedback_sheet_mapping():
    """Получить маппинг user_id -> название листа."""
    mapping = {}
    env_mapping = os.getenv("FEEDBACK_SHEET_MAPPING", "")
    if env_mapping:
        for pair in env_mapping.split(","):
            if ":" in pair:
                user_id_str, sheet_name = pair.split(":", 1)
                try:
                    mapping[int(user_id_str.strip())] = sheet_name.strip()
                except ValueError:
                    logger.warning(f"Неверный формат user_id в FEEDBACK_SHEET_MAPPING: {pair}")
    return mapping


class FeedbackService:
    """Класс для работы с обратной связью через Google Sheets и Drive."""
    
    # Название папки для скриншотов обратной связи
    FEEDBACK_FOLDER_NAME = "TRACY Feedback Screenshots"
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        # Используем тот же токен, что и для Google Calendar (если есть)
        # Или создаем отдельный токен для Sheets/Drive
        self.token_path = os.path.join(config.TOKENS_DIR, f"google_feedback_token_{user_id}.json")
        self.sheets_service = None
        self.drive_service = None
        self._feedback_folder_id = None  # Кэш ID папки для скриншотов
    
    def get_credentials(self) -> Optional[Credentials]:
        """Получить credentials пользователя."""
        if not os.path.exists(self.token_path):
            return None
        
        try:
            creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
            return creds
        except Exception as e:
            logger.error(f"Ошибка загрузки credentials для обратной связи: {e}")
            return None
    
    def save_credentials(self, credentials: Credentials):
        """Сохранить credentials."""
        os.makedirs(os.path.dirname(self.token_path), exist_ok=True)
        with open(self.token_path, 'w') as token:
            token.write(credentials.to_json())
    
    def get_authorization_url(self) -> str:
        """Получить URL для OAuth авторизации."""
        if not config.GOOGLE_CLIENT_ID or not config.GOOGLE_CLIENT_SECRET:
            raise ValueError(
                "GOOGLE_CLIENT_ID и GOOGLE_CLIENT_SECRET должны быть установлены в переменных окружения."
            )
        
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
        
        # Сохраняем flow в сессию
        self._save_flow_state(flow)
        
        return authorization_url
    
    def _save_flow_state(self, flow: Flow):
        """Сохранить состояние OAuth flow."""
        flow_state_path = os.path.join(config.TOKENS_DIR, f"feedback_flow_{self.user_id}.json")
        os.makedirs(os.path.dirname(flow_state_path), exist_ok=True)
        with open(flow_state_path, 'w') as f:
            import json
            json.dump({
                'client_config': flow.client_config,
                'scopes': flow.scopes,
                'redirect_uri': flow.redirect_uri
            }, f)
    
    def _load_flow_state(self) -> Optional[Flow]:
        """Загрузить состояние OAuth flow."""
        flow_state_path = os.path.join(config.TOKENS_DIR, f"feedback_flow_{self.user_id}.json")
        if not os.path.exists(flow_state_path):
            return None
        
        try:
            import json
            with open(flow_state_path, 'r') as f:
                state = json.load(f)
            
            flow = Flow.from_client_config(
                state['client_config'],
                state['scopes'],
                redirect_uri=state['redirect_uri']
            )
            return flow
        except Exception as e:
            logger.error(f"Ошибка загрузки flow state: {e}")
            return None
    
    def handle_callback(self, authorization_response: str) -> bool:
        """Обработать OAuth callback."""
        try:
            from urllib.parse import urlparse, parse_qs
            
            if authorization_response.startswith('http'):
                parsed_url = urlparse(authorization_response)
                query_params = parse_qs(parsed_url.query)
                auth_code = query_params.get('code', [None])[0]
            else:
                auth_code = authorization_response
            
            if not auth_code:
                logger.error("Не найден код авторизации в ответе")
                return False
            
            flow = self._load_flow_state()
            if not flow:
                logger.error("Не найден сохраненный flow state")
                return False
            
            flow.fetch_token(code=auth_code)
            credentials = flow.credentials
            
            self.save_credentials(credentials)
            
            # Удаляем временный flow state
            flow_state_path = os.path.join(config.TOKENS_DIR, f"feedback_flow_{self.user_id}.json")
            if os.path.exists(flow_state_path):
                os.remove(flow_state_path)
            
            return True
        except Exception as e:
            logger.error(f"Ошибка обработки callback для обратной связи: {e}", exc_info=True)
            return False
    
    def _get_service(self):
        """Получить или создать сервис для работы с Google Sheets."""
        if self.sheets_service:
            return self.sheets_service
        
        creds = self.get_credentials()
        if not creds:
            raise ValueError("Не авторизован для работы с Google Sheets. Выполни авторизацию.")
        
        self.sheets_service = build('sheets', 'v4', credentials=creds)
        return self.sheets_service
    
    def _get_drive_service(self):
        """Получить или создать сервис для работы с Google Drive."""
        if self.drive_service:
            return self.drive_service
        
        creds = self.get_credentials()
        if not creds:
            raise ValueError("Не авторизован для работы с Google Drive. Выполни авторизацию.")
        
        self.drive_service = build('drive', 'v3', credentials=creds)
        return self.drive_service
    
    def _get_sheet_name(self) -> str:
        """Получить название листа для текущего пользователя."""
        # При использовании Apps Script маппинг выполняется на стороне Apps Script
        # Здесь возвращаем значение только для прямого API (fallback)
        mapping = get_feedback_sheet_mapping()
        return mapping.get(self.user_id, DEFAULT_SHEET_NAME)
    
    def _ensure_sheet_exists(self, sheet_name: str):
        """Убедиться, что лист существует в таблице."""
        if not FEEDBACK_SPREADSHEET_ID:
            raise ValueError("FEEDBACK_SPREADSHEET_ID не установлен в переменных окружения")
        
        service = self._get_service()
        
        try:
            # Получаем список всех листов
            spreadsheet = service.spreadsheets().get(spreadsheetId=FEEDBACK_SPREADSHEET_ID).execute()
            sheet_names = [sheet['properties']['title'] for sheet in spreadsheet.get('sheets', [])]
            
            # Если листа нет, создаем его
            if sheet_name not in sheet_names:
                requests = [{
                    'addSheet': {
                        'properties': {
                            'title': sheet_name
                        }
                    }
                }]
                
                body = {'requests': requests}
                service.spreadsheets().batchUpdate(
                    spreadsheetId=FEEDBACK_SPREADSHEET_ID,
                    body=body
                ).execute()
                
                # Добавляем заголовки в новый лист
                self._add_headers(sheet_name)
                
                logger.info(f"Создан новый лист: {sheet_name}")
        except HttpError as e:
            logger.error(f"Ошибка при проверке/создании листа: {e}")
            raise
    
    def _add_headers(self, sheet_name: str):
        """Добавить заголовки в лист, если их еще нет."""
        service = self._get_service()
        
        # Проверяем, есть ли уже данные в первой строке
        range_name = f"{sheet_name}!A1:F1"
        result = service.spreadsheets().values().get(
            spreadsheetId=FEEDBACK_SPREADSHEET_ID,
            range=range_name
        ).execute()
        
        values = result.get('values', [])
        if values and len(values) > 0:
            # Заголовки уже есть
            return
        
        # Добавляем заголовки (строка 1)
        # Порядок: A: №, B: Дата, C: Содержание комментария, D: Скриншот, E: Тип комментария, F: Статус
        headers = [['№', 'Дата', 'Содержание комментария', 'Скриншот', 'Тип комментария', 'Статус']]
        body = {'values': headers}
        
        service.spreadsheets().values().update(
            spreadsheetId=FEEDBACK_SPREADSHEET_ID,
            range=f"{sheet_name}!A1:F1",
            valueInputOption='RAW',
            body=body
        ).execute()
    
    def _get_next_row_number(self, sheet_name: str) -> int:
        """Получить номер следующей строки для записи."""
        service = self._get_service()
        
        range_name = f"{sheet_name}!A:A"
        result = service.spreadsheets().values().get(
            spreadsheetId=FEEDBACK_SPREADSHEET_ID,
            range=range_name
        ).execute()
        
        values = result.get('values', [])
        # Если лист пустой или только заголовки (1 строка), начинаем с 2-й строки
        if len(values) <= 1:
            return 2
        # Иначе возвращаем следующую строку после последней
        return len(values) + 1
    
    def _get_or_create_feedback_folder(self) -> Optional[str]:
        """Получить или создать папку для скриншотов обратной связи."""
        if self._feedback_folder_id:
            return self._feedback_folder_id
        
        try:
            drive_service = self._get_drive_service()
            
            # Ищем существующую папку
            query = f"name='{self.FEEDBACK_FOLDER_NAME}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = drive_service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            
            folders = results.get('files', [])
            
            if folders:
                # Папка уже существует
                self._feedback_folder_id = folders[0]['id']
                logger.info(f"Найдена существующая папка для скриншотов: {self.FEEDBACK_FOLDER_NAME} (ID: {self._feedback_folder_id})")
                return self._feedback_folder_id
            
            # Создаем новую папку
            folder_metadata = {
                'name': self.FEEDBACK_FOLDER_NAME,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            folder = drive_service.files().create(
                body=folder_metadata,
                fields='id, name'
            ).execute()
            
            self._feedback_folder_id = folder.get('id')
            logger.info(f"Создана папка для скриншотов: {self.FEEDBACK_FOLDER_NAME} (ID: {self._feedback_folder_id})")
            
            # Делаем папку доступной для всех (чтобы скриншоты внутри были доступны)
            drive_service.permissions().create(
                fileId=self._feedback_folder_id,
                body={'role': 'reader', 'type': 'anyone'}
            ).execute()
            
            return self._feedback_folder_id
            
        except Exception as e:
            logger.error(f"Ошибка при получении/создании папки для скриншотов: {e}", exc_info=True)
            return None
    
    def upload_screenshot_to_drive(self, photo_file: BytesIO, filename: str) -> Optional[str]:
        """Загрузить скриншот в Google Drive и вернуть ссылку."""
        try:
            drive_service = self._get_drive_service()
            
            # Получаем или создаем папку для скриншотов
            folder_id = self._get_or_create_feedback_folder()
            
            # Создаем файл в Drive
            file_metadata = {
                'name': filename
            }
            
            # Если папка найдена/создана, загружаем в неё
            if folder_id:
                file_metadata['parents'] = [folder_id]
            else:
                # Если не удалось создать папку, загружаем в корень
                logger.warning("Не удалось получить папку для скриншотов, загружаю в корень Drive")
                file_metadata['parents'] = []
            
            photo_file.seek(0)
            media = {
                'mimeType': 'image/jpeg',
                'body': photo_file
            }
            
            file = drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, webViewLink'
            ).execute()
            
            # Делаем файл доступным для всех (можно изменить настройки доступа)
            drive_service.permissions().create(
                fileId=file['id'],
                body={'role': 'reader', 'type': 'anyone'}
            ).execute()
            
            logger.info(f"Скриншот загружен в Drive: {filename} (ID: {file['id']})")
            return file.get('webViewLink')
        except Exception as e:
            logger.error(f"Ошибка загрузки скриншота в Drive: {e}", exc_info=True)
            return None
    
    def submit_feedback_via_apps_script(self, feedback_type: str, comment: str, screenshot_url: Optional[str] = None) -> Optional[Dict]:
        """
        Отправить обратную связь через Apps Script webhook (альтернативный способ).
        
        Args:
            feedback_type: "баг" или "предложение"
            comment: Текст комментария
            screenshot_url: Ссылка на скриншот в Drive (если есть)
        
        Returns:
            Dict с информацией о записи или None в случае ошибки
        """
        apps_script_url = config.FEEDBACK_APPS_SCRIPT_URL
        if not apps_script_url:
            logger.warning("FEEDBACK_APPS_SCRIPT_URL не установлен, пропускаем отправку через Apps Script")
            return None
        
        try:
            # Подготавливаем данные для отправки
            data = {
                "type": feedback_type,
                "user_id": str(self.user_id),
                "comment": comment,
            }
            if screenshot_url:
                data["screenshot_url"] = screenshot_url
            
            # Отправляем POST запрос
            response = httpx.post(
                apps_script_url,
                json=data,
                timeout=10.0,
                follow_redirects=True
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    logger.info(f"Обратная связь отправлена через Apps Script: {result}")
                    return result
                else:
                    logger.error(f"Apps Script вернул ошибку: {result.get('error')}")
                    return None
            else:
                logger.error(f"Ошибка HTTP при отправке через Apps Script: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка отправки через Apps Script: {e}", exc_info=True)
            return None
    
    def submit_feedback(self, feedback_type: str, comment: str, screenshot_url: Optional[str] = None, use_apps_script: bool = False) -> Dict:
        """
        Отправить обратную связь в Google Sheets.
        
        Args:
            feedback_type: "баг" или "предложение"
            comment: Текст комментария
            screenshot_url: Ссылка на скриншот в Drive (если есть)
            use_apps_script: Если True, использует Apps Script webhook вместо прямого API
        
        Returns:
            Dict с информацией о записи (номер, дата)
        """
        # Если указано использовать Apps Script, пробуем сначала его
        if use_apps_script:
            apps_script_result = self.submit_feedback_via_apps_script(feedback_type, comment, screenshot_url)
            if apps_script_result:
                return apps_script_result
            # Если Apps Script не сработал, fallback на обычный способ
            logger.info("Apps Script не сработал, используем обычный способ записи")
        
        if not FEEDBACK_SPREADSHEET_ID:
            raise ValueError("FEEDBACK_SPREADSHEET_ID не установлен в переменных окружения")
        
        sheet_name = self._get_sheet_name()
        self._ensure_sheet_exists(sheet_name)
        
        service = self._get_service()
        
        # Получаем номер следующей строки
        row_number = self._get_next_row_number(sheet_name)
        
        # Формируем данные для записи
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d %H:%M:%S")
        
        # Порядок столбцов: A: №, B: Дата, C: Содержание комментария, D: Скриншот, E: Тип комментария, F: Статус
        # Преобразуем тип: "баг" -> "Баг", "предложение" -> "Предложение"
        type_display = "Баг" if feedback_type.lower() == "баг" else "Предложение"
        
        values = [[
            row_number - 1,  # A: № (минус 1, так как первая строка - заголовок)
            date_str,        # B: Дата
            comment,         # C: Содержание комментария
            screenshot_url or "",  # D: Скриншот
            type_display,    # E: Тип комментария (Баг/Предложение)
            ""               # F: Статус (пусто по умолчанию)
        ]]
        
        body = {'values': values}
        
        # Записываем данные
        range_name = f"{sheet_name}!A{row_number}:F{row_number}"
        result = service.spreadsheets().values().update(
            spreadsheetId=FEEDBACK_SPREADSHEET_ID,
            range=range_name,
            valueInputOption='RAW',
            body=body
        ).execute()
        
        logger.info(f"Обратная связь записана в лист {sheet_name}, строка {row_number}")
        
        return {
            'number': row_number - 1,
            'date': date_str,
            'type': feedback_type,
            'sheet': sheet_name
        }

