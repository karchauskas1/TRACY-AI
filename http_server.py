"""
Простой HTTP сервер для обслуживания запросов от веб-приложения.
Позволяет веб-приложению получать события напрямую из БД через HTTP API.
"""
import asyncio
import base64
import json
import logging
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional
from aiohttp import web, web_request
from aiohttp.web_response import json_response
import pytz
from database import Database
from nlp_extractor import NLPExtractor
from decision_engine import DecisionEngine
import config

logger = logging.getLogger(__name__)

# Глобальная ссылка на БД
db_instance: Optional[Database] = None

# Lazy-initialized NLP/DecisionEngine for web chat
nlp_extractor_instance: Optional[NLPExtractor] = None
decision_engine_instance: Optional[DecisionEngine] = None

# Feedback screenshots storage (server disk)
FEEDBACK_UPLOADS_DIR = os.getenv("FEEDBACK_UPLOADS_DIR", "./data/feedback_uploads")
os.makedirs(FEEDBACK_UPLOADS_DIR, exist_ok=True)

# Временное хранилище токенов авторизации (token -> user_id)
# В production можно использовать Redis или БД
auth_tokens: Dict[str, Dict] = {}


def set_database(db: Database):
    """Устанавливает глобальную ссылку на БД."""
    global db_instance
    db_instance = db


def _get_nlp_and_engine(db: Database) -> tuple[NLPExtractor, DecisionEngine]:
    """
    Creates (once) and returns NLPExtractor + DecisionEngine for web chat.
    """
    global nlp_extractor_instance, decision_engine_instance
    if nlp_extractor_instance is None:
        nlp_extractor_instance = NLPExtractor()
    if decision_engine_instance is None:
        # Reuse NLPExtractor OpenAI client inside DecisionEngine (emoji + calls)
        decision_engine_instance = DecisionEngine(db, reminder_scheduler=None, ai_client=nlp_extractor_instance.client)
    return nlp_extractor_instance, decision_engine_instance


async def get_events_handler(request: web_request.Request):
    """Обработчик GET запроса для получения событий."""
    try:
        # Получаем user_id из query параметров
        user_id_str = request.query.get('user_id')
        if not user_id_str:
            logger.warning("❌ HTTP API: user_id не предоставлен")
            return json_response({'error': 'user_id required'}, status=400)
        
        try:
            user_id = int(user_id_str)
        except ValueError:
            logger.warning(f"❌ HTTP API: неверный user_id: {user_id_str}")
            return json_response({'error': 'Invalid user_id'}, status=400)
        
        # Получаем параметры периода (опционально)
        from_date_str = request.query.get('from')
        to_date_str = request.query.get('to')
        
        if not db_instance:
            logger.error("❌ HTTP API: База данных не инициализирована")
            return json_response({'error': 'Database not initialized'}, status=500)
        
        # Получаем настройки пользователя для timezone
        try:
            user = db_instance.get_or_create_user(user_id)
            if not user:
                logger.error(f"❌ HTTP API: Не удалось получить/создать пользователя {user_id}")
                return json_response({'error': 'Failed to get or create user'}, status=500)
        except Exception as e:
            logger.error(f"❌ HTTP API: Ошибка при получении пользователя {user_id}: {e}", exc_info=True)
            return json_response({'error': f'Database error: {str(e)}'}, status=500)
        
        timezone = user.get('timezone', 'Europe/Moscow') if isinstance(user, dict) else 'Europe/Moscow'
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)
        
        # Определяем период
        if from_date_str:
            try:
                start_from = datetime.fromisoformat(from_date_str.replace('Z', '+00:00'))
                if start_from.tzinfo is None:
                    start_from = tz.localize(start_from)
            except:
                start_from = now - timedelta(days=90)
        else:
            start_from = now - timedelta(days=90)
        
        if to_date_str:
            try:
                start_to = datetime.fromisoformat(to_date_str.replace('Z', '+00:00'))
                if start_to.tzinfo is None:
                    start_to = tz.localize(start_to)
            except:
                start_to = now + timedelta(days=365)
        else:
            start_to = now + timedelta(days=365)
        
        # Получаем события из БД
        try:
            events = db_instance.get_events(user_id, limit=200, start_from=start_from, start_to=start_to)
            logger.info(f"📊 HTTP API: Получено {len(events)} событий для пользователя {user_id}")
        except Exception as e:
            logger.error(f"❌ HTTP API: Ошибка при получении событий для пользователя {user_id}: {e}", exc_info=True)
            return json_response({'error': f'Failed to get events: {str(e)}'}, status=500)
        
        # Преобразуем события в формат для веб-приложения
        web_events = []
        for event in events:
            start_time = event.get('start_time')
            end_time = event.get('end_time')
            
            # Конвертируем datetime в ISO строку
            if isinstance(start_time, datetime):
                start_iso = start_time.isoformat()
            elif isinstance(start_time, str):
                start_iso = start_time
            else:
                continue
            
            if isinstance(end_time, datetime):
                end_iso = end_time.isoformat()
            elif isinstance(end_time, str):
                end_iso = end_time
            else:
                # Если нет end_time, добавляем час
                if isinstance(start_time, datetime):
                    end_iso = (start_time + timedelta(hours=1)).isoformat()
                else:
                    continue
            
            web_events.append({
                'id': str(event.get('id', '')),
                'title': event.get('title', 'Без названия'),
                'startAt': start_iso,
                'endAt': end_iso,
                'allDay': False,
                'description': event.get('description'),
                'location': event.get('location'),
                'calendarSource': {
                    'color': '#3b82f6',
                    'name': 'TRACY'
                }
            })
        
        return json_response({
            'success': True,
            'events': web_events,
            'count': len(web_events),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Ошибка HTTP API get_events: {e}", exc_info=True)
        return json_response({'error': str(e)}, status=500)


async def get_meetings_handler(request: web_request.Request):
    """Обработчик GET запроса для получения списка встреч."""
    try:
        user_id_str = request.query.get('user_id')
        if not user_id_str:
            return json_response({'error': 'user_id required'}, status=400)
        
        try:
            user_id = int(user_id_str)
        except ValueError:
            return json_response({'error': 'Invalid user_id'}, status=400)
        
        if not db_instance:
            return json_response({'error': 'Database not initialized'}, status=500)
        
        try:
            meetings = db_instance.get_meetings(user_id, limit=100)
            web_meetings = []
            for meeting in meetings:
                web_meetings.append({
                    'id': str(meeting.get('id', '')),
                    'title': meeting.get('title') or meeting.get('summary', '')[:100] or 'Встреча',
                    'summary': meeting.get('summary'),
                    'transcript': meeting.get('transcript'),
                    'summaryExtended': meeting.get('summary_extended'),
                    'createdAt': meeting.get('created_at').isoformat() if isinstance(meeting.get('created_at'), datetime) else meeting.get('created_at'),
                })
            
            return json_response({
                'success': True,
                'meetings': web_meetings,
                'count': len(web_meetings)
            })
        except Exception as e:
            logger.error(f"Ошибка получения встреч: {e}", exc_info=True)
            return json_response({'error': str(e)}, status=500)
    except Exception as e:
        logger.error(f"Ошибка HTTP API get_meetings: {e}", exc_info=True)
        return json_response({'error': str(e)}, status=500)


async def get_meeting_handler(request: web_request.Request):
    """Обработчик GET запроса для получения конкретной встречи."""
    try:
        meeting_id_str = request.match_info.get('meeting_id')
        user_id_str = request.query.get('user_id')
        
        if not meeting_id_str or not user_id_str:
            return json_response({'error': 'meeting_id and user_id required'}, status=400)
        
        try:
            meeting_id = int(meeting_id_str)
            user_id = int(user_id_str)
        except ValueError:
            return json_response({'error': 'Invalid meeting_id or user_id'}, status=400)
        
        if not db_instance:
            return json_response({'error': 'Database not initialized'}, status=500)
        
        try:
            meeting = db_instance.get_meeting(meeting_id, user_id)
            if not meeting:
                return json_response({'error': 'Meeting not found'}, status=404)
            
            return json_response({
                'success': True,
                'meeting': {
                    'id': str(meeting.get('id', '')),
                    'title': meeting.get('title') or meeting.get('summary', '')[:100] or 'Встреча',
                    'summary': meeting.get('summary'),
                    'transcript': meeting.get('transcript'),
                    'summaryExtended': meeting.get('summary_extended'),
                    'createdAt': meeting.get('created_at').isoformat() if isinstance(meeting.get('created_at'), datetime) else meeting.get('created_at'),
                }
            })
        except Exception as e:
            logger.error(f"Ошибка получения встречи: {e}", exc_info=True)
            return json_response({'error': str(e)}, status=500)
    except Exception as e:
        logger.error(f"Ошибка HTTP API get_meeting: {e}", exc_info=True)
        return json_response({'error': str(e)}, status=500)


async def create_event_from_meeting_handler(request: web_request.Request):
    """Обработчик POST запроса для создания события из встречи."""
    try:
        meeting_id_str = request.match_info.get('meeting_id')
        if not meeting_id_str:
            return json_response({'error': 'meeting_id required'}, status=400)
        
        try:
            data = await request.json()
            user_id = int(data.get('user_id', 0))
            event_data = data.get('event_data', {})
        except:
            return json_response({'error': 'Invalid request body'}, status=400)
        
        # Создание события из встречи должно происходить через бота
        # так как требуется decision_engine и reminder_scheduler
        # Возвращаем инструкцию для использования бота
        return json_response({
            'success': True,
            'message': 'Event creation from meeting requires bot context',
            'action': 'open_bot',
            'bot_command': f'/start create_event_from_meeting_{meeting_id_str}',
            'note': 'Use Telegram bot command to create events from meetings. The bot has full context and can properly process event data.'
        })
    except Exception as e:
        logger.error(f"Ошибка HTTP API create_event_from_meeting: {e}", exc_info=True)
        return json_response({'error': str(e)}, status=500)


async def update_settings_handler(request: web_request.Request):
    """Обработчик POST запроса для обновления настроек пользователя."""
    try:
        data = await request.json()
        user_id = data.get('user_id')
        
        if not user_id:
            return json_response({'error': 'user_id required'}, status=400)
        
        if not db_instance:
            return json_response({'error': 'Database not initialized'}, status=500)
        
        # Обновляем настройки в БД
        settings_to_update = {}
        if 'timezone' in data:
            settings_to_update['timezone'] = data['timezone']
        if 'locale' in data:
            settings_to_update['locale'] = data['locale']
        if 'notifications_enabled' in data:
            settings_to_update['notifications_enabled'] = data['notifications_enabled']
        if 'default_reminder_minutes' in data:
            settings_to_update['default_reminder_minutes'] = data['default_reminder_minutes']
        if 'morning_digest_time' in data:
            settings_to_update['morning_digest_time'] = data['morning_digest_time']
        if 'web_notifications_enabled' in data:
            settings_to_update['web_notifications_enabled'] = data['web_notifications_enabled']
        if 'interpretation_mode' in data:
            settings_to_update['interpretation_mode'] = data['interpretation_mode']
        
        if settings_to_update:
            db_instance.update_user_settings(int(user_id), settings_dict=settings_to_update)
            logger.info(f"⚙️ HTTP API: Обновлены настройки для пользователя {user_id}: {settings_to_update}")
        
        return json_response({'success': True})
        
    except Exception as e:
        logger.error(f"❌ Ошибка HTTP API update_settings: {e}", exc_info=True)
        return json_response({'error': str(e)}, status=500)


async def get_feedback_handler(request: web_request.Request):
    """Обработчик GET запроса для получения обратной связи (только для супер-пользователя)."""
    try:
        user_id_str = request.query.get('user_id')
        if not user_id_str:
            return json_response({'error': 'user_id required'}, status=400)
        
        try:
            user_id = int(user_id_str)
        except ValueError:
            return json_response({'error': 'Invalid user_id'}, status=400)
        
        if user_id != config.SUPER_USER_ID:
            return json_response({'error': 'Access denied'}, status=403)
        
        limit = int(request.query.get('limit', 100))
        offset = int(request.query.get('offset', 0))
        
        # ВСЕГДА создаем новый экземпляр БД для надежности (избегаем проблем с потоками)
        from database import Database
        import sqlite3
        db_to_use = Database()
        
        try:
            # ПРЯМОЙ SQL ЗАПРОС для получения данных (обход get_all_feedback)
            if not db_to_use.use_postgresql:
                conn = db_to_use.get_connection()
                cursor = conn.cursor()
                
                # Получаем все записи напрямую
                cursor.execute("""
                    SELECT id, user_id, feedback_type, comment, screenshot_url, created_at
                    FROM feedback
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                """, (limit, offset))
                
                columns = [desc[0] for desc in cursor.description]
                direct_rows = cursor.fetchall()
                
                # Преобразуем в список словарей
                feedback_list = []
                logger.info(f"📊 HTTP API: Получено {len(direct_rows)} строк из SQL запроса, колонки: {columns}")
                for idx, row in enumerate(direct_rows):
                    try:
                        # row - это sqlite3.Row, доступ к полям через имя колонки
                        row_dict = {}
                        for col_name in columns:
                            try:
                                row_dict[col_name] = row[col_name]  # Доступ через имя колонки для sqlite3.Row
                            except (KeyError, IndexError) as e:
                                logger.error(f"❌ HTTP API: Ошибка доступа к колонке {col_name} в строке {idx+1}: {e}")
                                # Пробуем через индекс
                                col_idx = columns.index(col_name)
                                row_dict[col_name] = row[col_idx]
                        row_dict['sheet_name'] = None
                        row_dict['sheet_row_number'] = None
                        feedback_list.append(row_dict)
                        logger.debug(f"📊 HTTP API: Обработана строка {idx+1}: {row_dict}")
                    except Exception as e:
                        logger.error(f"❌ HTTP API: Ошибка обработки строки {idx+1}: {e}", exc_info=True)
                        import traceback
                        logger.error(traceback.format_exc())
                
                # Получаем total count
                cursor.execute("SELECT COUNT(*) FROM feedback")
                total_count = cursor.fetchone()[0]
                
                db_to_use.return_connection(conn)
                logger.info(f"📊 HTTP API: Прямой SQL запрос вернул {len(feedback_list)} записей, total={total_count}")
                if len(feedback_list) > 0:
                    logger.info(f"📊 HTTP API: Первая запись: {feedback_list[0]}")
                else:
                    logger.warning(f"⚠️ HTTP API: feedback_list пустой после обработки {len(direct_rows)} строк!")
            else:
                # Для PostgreSQL используем get_all_feedback
                feedback_list = db_to_use.get_all_feedback(limit=limit, offset=offset)
                total_count = db_to_use.get_feedback_count()
                logger.info(f"📊 HTTP API: get_all_feedback вернул {len(feedback_list)} записей, total={total_count}")
                
        except Exception as e:
            logger.error(f"❌ HTTP API: Ошибка при получении обратной связи: {e}", exc_info=True)
            import traceback
            logger.error(traceback.format_exc())
            return json_response({'error': f'Failed to get feedback: {str(e)}'}, status=500)
        
        web_feedback = []
        logger.info(f"📊 HTTP API: Начинаю обработку {len(feedback_list)} записей, total_count={total_count}")
        
        # КРИТИЧЕСКАЯ ПРОВЕРКА: если feedback_list пустой, но total_count > 0
        if len(feedback_list) == 0 and total_count > 0:
            logger.error(f"❌ HTTP API: КРИТИЧЕСКАЯ ОШИБКА: feedback_list пустой, но total_count={total_count}")
            # Вместо ошибки, возвращаем пустой массив с total для совместимости
            # Но логируем проблему
            logger.warning(f"⚠️ HTTP API: Возвращаю пустой массив, хотя total_count={total_count}")
            return json_response({
                'feedback': [],
                'total': total_count,
                'limit': limit,
                'offset': offset,
                'warning': 'feedback_list is empty but total_count > 0'
            })
        
        for idx, item in enumerate(feedback_list):
            try:
                created_at = item.get('created_at')
                if isinstance(created_at, datetime):
                    created_at_str = created_at.isoformat()
                elif isinstance(created_at, str):
                    created_at_str = created_at
                else:
                    created_at_str = None
                
                web_feedback.append({
                    'id': str(item.get('id', '')),
                    'userId': str(item.get('user_id', '')),
                    'type': item.get('feedback_type'),
                    'comment': item.get('comment'),
                    'screenshotUrl': item.get('screenshot_url'),
                    'sheetName': item.get('sheet_name'),
                    'sheetRowNumber': item.get('sheet_row_number'),
                    'createdAt': created_at_str
                })
            except Exception as e:
                logger.error(f"❌ HTTP API: Ошибка обработки записи {idx+1}: {e}", exc_info=True)
                import traceback
                logger.error(traceback.format_exc())
        
        logger.info(f"📊 HTTP API: Сформировано {len(web_feedback)} записей для ответа")
        
        return json_response({
            'feedback': web_feedback,
            'total': total_count,
            'limit': limit,
            'offset': offset
        })
    except Exception as e:
        logger.error(f"❌ HTTP API: Неожиданная ошибка get_feedback: {e}", exc_info=True)
        return json_response({'error': f'Internal server error: {str(e)}'}, status=500)


def _public_base_url(request: web_request.Request) -> str:
    """
    Best-effort base URL for building absolute links behind reverse proxies.
    Uses X-Forwarded-* if present.
    """
    proto = request.headers.get("X-Forwarded-Proto", request.scheme)
    host = request.headers.get("X-Forwarded-Host", request.host)
    return f"{proto}://{host}"


def _decode_base64_payload(payload: str) -> bytes:
    """
    Accepts raw base64 or data URL (data:image/png;base64,....)
    """
    if not payload:
        raise ValueError("Empty screenshot_base64")
    data = payload.strip()
    if data.startswith("data:"):
        # data:image/png;base64,XXXX
        comma = data.find(",")
        if comma == -1:
            raise ValueError("Invalid data URL")
        data = data[comma + 1 :]
    return base64.b64decode(data, validate=False)


def _guess_ext_and_content_type(image_bytes: bytes) -> tuple[str, str]:
    # PNG signature: 89 50 4E 47 0D 0A 1A 0A
    if image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return (".png", "image/png")
    # JPEG signature: FF D8
    if image_bytes.startswith(b"\xff\xd8"):
        return (".jpg", "image/jpeg")
    # Fallback
    return (".jpg", "image/jpeg")


async def submit_feedback_handler(request: web_request.Request):
    """
    POST /api/feedback/submit
    Body: { user_id, type, comment, screenshot_base64? }
    Saves feedback to DB and optionally stores screenshot on server disk.
    """
    try:
        try:
            data = await request.json()
        except Exception as e:
            return json_response({'error': f'Invalid JSON: {str(e)}'}, status=400)

        user_id = data.get("user_id")
        feedback_type = data.get("type") or data.get("feedback_type")
        comment = data.get("comment")
        screenshot_base64 = data.get("screenshot_base64")

        if not user_id or not feedback_type or not comment:
            return json_response({'error': 'user_id, type, comment required'}, status=400)

        try:
            user_id_int = int(user_id)
        except ValueError:
            return json_response({'error': 'Invalid user_id'}, status=400)

        screenshot_url = None
        if screenshot_base64:
            try:
                image_bytes = _decode_base64_payload(screenshot_base64)
                ext, _content_type = _guess_ext_and_content_type(image_bytes)
                file_id = uuid.uuid4().hex
                filename = f"{file_id}{ext}"
                file_path = os.path.join(FEEDBACK_UPLOADS_DIR, filename)
                with open(file_path, "wb") as f:
                    f.write(image_bytes)
                screenshot_url = f"{_public_base_url(request)}/feedback/screenshots/{filename}"
            except Exception as e:
                logger.error(f"❌ Feedback submit: screenshot save error: {e}", exc_info=True)
                # Continue without screenshot
                screenshot_url = None

        # Save feedback in DB
        db = Database()
        feedback_id = db.save_feedback(user_id_int, str(feedback_type), str(comment), screenshot_url=screenshot_url)
        if not feedback_id:
            return json_response({'error': 'Failed to save feedback'}, status=500)

        return json_response({
            'success': True,
            'id': str(feedback_id),
            'screenshotUrl': screenshot_url,
        })
    except Exception as e:
        logger.error(f"❌ HTTP API: Error submit_feedback: {e}", exc_info=True)
        return json_response({'error': str(e)}, status=500)


async def get_feedback_screenshot_handler(request: web_request.Request):
    """
    GET /feedback/screenshots/{filename}
    Serves stored feedback screenshots.
    """
    try:
        filename = request.match_info.get("filename")
        if not filename:
            return web.Response(status=404)

        # Basic path traversal protection
        if "/" in filename or "\\" in filename or ".." in filename:
            return web.Response(status=400, text="Invalid filename")

        # Only allow common image extensions we store
        lower = filename.lower()
        if not (lower.endswith(".jpg") or lower.endswith(".jpeg") or lower.endswith(".png")):
            return web.Response(status=400, text="Unsupported file type")

        file_path = os.path.join(FEEDBACK_UPLOADS_DIR, filename)
        if not os.path.exists(file_path):
            return web.Response(status=404)

        # Cache aggressively (filename is UUID-based)
        resp = web.FileResponse(file_path)
        if lower.endswith(".png"):
            resp.content_type = "image/png"
        else:
            resp.content_type = "image/jpeg"
        resp.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        return resp
    except Exception as e:
        logger.error(f"❌ HTTP API: Error get_feedback_screenshot: {e}", exc_info=True)
        return web.Response(status=500, text="Internal server error")


async def health_handler(request: web_request.Request):
    """Обработчик для health check."""
    return json_response({'status': 'ok', 'timestamp': datetime.now().isoformat()})

async def root_handler(request: web_request.Request):
    """Обработчик для корневого пути."""
    return json_response({
        'service': 'TRACY API Server',
        'status': 'running',
        'endpoints': {
            '/health': 'Health check',
            '/api/events': 'Get events (requires ?user_id=XXX)'
        }
    })


# === To-Do Lists API Handlers ===

async def get_todo_lists_handler(request: web_request.Request):
    """GET /api/todo-lists?user_id=XXX - Получить все списки задач пользователя."""
    try:
        user_id_str = request.query.get('user_id')
        if not user_id_str:
            return json_response({'error': 'user_id required'}, status=400)
        
        try:
            user_id = int(user_id_str)
        except ValueError:
            return json_response({'error': 'Invalid user_id'}, status=400)
        
        db = db_instance or Database()
        lists = db.get_todo_lists(user_id)
        
        return json_response({
            'success': True,
            'lists': lists
        })
    except Exception as e:
        logger.error(f"Ошибка получения списков задач: {e}", exc_info=True)
        return json_response({'error': str(e)}, status=500)


async def create_todo_list_handler(request: web_request.Request):
    """POST /api/todo-lists - Создать новый список задач."""
    try:
        data = await request.json()
        user_id = data.get('user_id')
        title = data.get('title')
        
        if not user_id or not title:
            return json_response({'error': 'user_id and title required'}, status=400)
        
        try:
            user_id = int(user_id)
        except ValueError:
            return json_response({'error': 'Invalid user_id'}, status=400)
        
        if not title.strip():
            return json_response({'error': 'Title cannot be empty'}, status=400)
        
        db = db_instance or Database()
        list_id = db.create_todo_list(user_id, title.strip())
        
        if list_id:
            return json_response({
                'success': True,
                'list_id': list_id
            }, status=201)
        else:
            return json_response({'error': 'Failed to create list'}, status=500)
    except Exception as e:
        logger.error(f"Ошибка создания списка задач: {e}", exc_info=True)
        return json_response({'error': str(e)}, status=500)


async def get_todo_list_handler(request: web_request.Request):
    """GET /api/todo-lists/{list_id}?user_id=XXX - Получить конкретный список задач."""
    try:
        list_id_str = request.match_info.get('list_id')
        user_id_str = request.query.get('user_id')
        
        if not list_id_str or not user_id_str:
            return json_response({'error': 'list_id and user_id required'}, status=400)
        
        try:
            list_id = int(list_id_str)
            user_id = int(user_id_str)
        except ValueError:
            return json_response({'error': 'Invalid list_id or user_id'}, status=400)
        
        db = db_instance or Database()
        todo_list = db.get_todo_list(list_id, user_id)
        
        if not todo_list:
            return json_response({'error': 'List not found'}, status=404)
        
        # Получаем задачи списка
        items = db.get_todo_items(list_id)
        
        return json_response({
            'success': True,
            'list': todo_list,
            'items': items
        })
    except Exception as e:
        logger.error(f"Ошибка получения списка задач: {e}", exc_info=True)
        return json_response({'error': str(e)}, status=500)


async def update_todo_list_handler(request: web_request.Request):
    """PUT /api/todo-lists/{list_id} - Обновить список задач."""
    try:
        list_id_str = request.match_info.get('list_id')
        data = await request.json()
        user_id = data.get('user_id')
        title = data.get('title')
        
        if not list_id_str or not user_id or not title:
            return json_response({'error': 'list_id, user_id and title required'}, status=400)
        
        try:
            list_id = int(list_id_str)
            user_id = int(user_id)
        except ValueError:
            return json_response({'error': 'Invalid list_id or user_id'}, status=400)
        
        if not title.strip():
            return json_response({'error': 'Title cannot be empty'}, status=400)
        
        db = db_instance or Database()
        updated = db.update_todo_list(list_id, user_id, title.strip())
        
        if updated:
            return json_response({'success': True})
        else:
            return json_response({'error': 'List not found or update failed'}, status=404)
    except Exception as e:
        logger.error(f"Ошибка обновления списка задач: {e}", exc_info=True)
        return json_response({'error': str(e)}, status=500)


async def delete_todo_list_handler(request: web_request.Request):
    """DELETE /api/todo-lists/{list_id}?user_id=XXX - Удалить список задач."""
    try:
        list_id_str = request.match_info.get('list_id')
        user_id_str = request.query.get('user_id')
        
        if not list_id_str or not user_id_str:
            return json_response({'error': 'list_id and user_id required'}, status=400)
        
        try:
            list_id = int(list_id_str)
            user_id = int(user_id_str)
        except ValueError:
            return json_response({'error': 'Invalid list_id or user_id'}, status=400)
        
        db = db_instance or Database()
        deleted = db.delete_todo_list(list_id, user_id)
        
        if deleted:
            return json_response({'success': True})
        else:
            return json_response({'error': 'List not found'}, status=404)
    except Exception as e:
        logger.error(f"Ошибка удаления списка задач: {e}", exc_info=True)
        return json_response({'error': str(e)}, status=500)


async def create_todo_item_handler(request: web_request.Request):
    """POST /api/todo-lists/{list_id}/items - Создать задачу в списке."""
    try:
        list_id_str = request.match_info.get('list_id')
        data = await request.json()
        text = data.get('text')
        
        if not list_id_str or not text:
            return json_response({'error': 'list_id and text required'}, status=400)
        
        try:
            list_id = int(list_id_str)
        except ValueError:
            return json_response({'error': 'Invalid list_id'}, status=400)
        
        if not text.strip():
            return json_response({'error': 'Text cannot be empty'}, status=400)
        
        db = db_instance or Database()
        item_id = db.create_todo_item(list_id, text.strip())
        
        if item_id:
            return json_response({
                'success': True,
                'item_id': item_id
            }, status=201)
        else:
            return json_response({'error': 'Failed to create item'}, status=500)
    except Exception as e:
        logger.error(f"Ошибка создания задачи: {e}", exc_info=True)
        return json_response({'error': str(e)}, status=500)


async def update_todo_item_handler(request: web_request.Request):
    """PUT /api/todo-items/{item_id} - Обновить задачу."""
    try:
        item_id_str = request.match_info.get('item_id')
        data = await request.json()
        
        if not item_id_str:
            return json_response({'error': 'item_id required'}, status=400)
        
        try:
            item_id = int(item_id_str)
        except ValueError:
            return json_response({'error': 'Invalid item_id'}, status=400)
        
        text = data.get('text')
        completed = data.get('completed')
        
        if text is not None and not text.strip():
            return json_response({'error': 'Text cannot be empty'}, status=400)
        
        db = db_instance or Database()
        updated = db.update_todo_item(item_id, text.strip() if text else None, completed)
        
        if updated:
            return json_response({'success': True})
        else:
            return json_response({'error': 'Item not found or update failed'}, status=404)
    except Exception as e:
        logger.error(f"Ошибка обновления задачи: {e}", exc_info=True)
        return json_response({'error': str(e)}, status=500)


async def delete_todo_item_handler(request: web_request.Request):
    """DELETE /api/todo-items/{item_id} - Удалить задачу."""
    try:
        item_id_str = request.match_info.get('item_id')
        
        if not item_id_str:
            return json_response({'error': 'item_id required'}, status=400)
        
        try:
            item_id = int(item_id_str)
        except ValueError:
            return json_response({'error': 'Invalid item_id'}, status=400)
        
        db = db_instance or Database()
        deleted = db.delete_todo_item(item_id)
        
        if deleted:
            return json_response({'success': True})
        else:
            return json_response({'error': 'Item not found'}, status=404)
    except Exception as e:
        logger.error(f"Ошибка удаления задачи: {e}", exc_info=True)
        return json_response({'error': str(e)}, status=500)


# === Chat API Handlers ===

async def get_chat_messages_handler(request: web_request.Request):
    """GET /api/chat/messages?user_id=XXX - Получить историю сообщений чата."""
    try:
        user_id_str = request.query.get('user_id')
        if not user_id_str:
            return json_response({'error': 'user_id required'}, status=400)
        
        try:
            user_id = int(user_id_str)
        except ValueError:
            return json_response({'error': 'Invalid user_id'}, status=400)
        
        limit = int(request.query.get('limit', 50))
        
        db = db_instance or Database()
        messages = db.get_chat_messages(user_id, limit=limit)
        
        # Преобразуем даты в ISO строки
        for msg in messages:
            created_at = msg.get('created_at')
            if isinstance(created_at, datetime):
                msg['created_at'] = created_at.isoformat()
            elif isinstance(created_at, str):
                pass  # Уже строка
        
        return json_response({
            'success': True,
            'messages': messages
        })
    except Exception as e:
        logger.error(f"Ошибка получения сообщений чата: {e}", exc_info=True)
        return json_response({'error': str(e)}, status=500)


async def generate_chat_greeting_handler(request: web_request.Request):
    """GET /api/chat/greeting?user_id=XXX - Генерировать приветственное сообщение с анализом событий."""
    try:
        user_id_str = request.query.get('user_id')
        if not user_id_str:
            return json_response({'error': 'user_id required'}, status=400)
        
        try:
            user_id = int(user_id_str)
        except ValueError:
            return json_response({'error': 'Invalid user_id'}, status=400)
        
        db = db_instance or Database()
        
        # Получаем настройки пользователя
        user = db.get_or_create_user(user_id)
        timezone = user.get('timezone', 'Europe/Moscow') if isinstance(user, dict) else 'Europe/Moscow'
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        # Получаем события на сегодня
        today_events = db.get_events(user_id, limit=100, start_from=today_start, start_to=today_end)
        
        # Если событий на сегодня нет, получаем ближайшие события
        if not today_events:
            future_events = db.get_events(user_id, limit=10, start_from=now, start_to=now + timedelta(days=365))
            if future_events:
                # Берем первое событие
                first_event = future_events[0]
                start_time = first_event.get('start_time')
                if isinstance(start_time, datetime):
                    if start_time.tzinfo is None:
                        start_time = tz.localize(start_time)
                    event_time_str = start_time.strftime('%d.%m.%Y в %H:%M')
                else:
                    event_time_str = "в ближайшее время"
                
                title = first_event.get('title', 'Событие')
                
                greeting = f"Привет! 👋\n\nУ вас {event_time_str} запланировано «{title}». Хотите это обсудить?"
            else:
                greeting = "Привет! 👋\n\nЯ TRACY, твой AI-ассистент для планирования. Чем могу помочь?"
        else:
            # Формируем список событий на сегодня
            events_text = []
            for event in sorted(today_events, key=lambda e: e.get('start_time', datetime.min)):
                start_time = event.get('start_time')
                title = event.get('title', 'Событие')
                
                if isinstance(start_time, datetime):
                    if start_time.tzinfo is None:
                        start_time = tz.localize(start_time)
                    time_str = start_time.strftime('%H:%M')
                    events_text.append(f"• {time_str} — {title}")
                else:
                    events_text.append(f"• {title}")
            
            events_list = "\n".join(events_text)
            greeting = f"Привет! 👋\n\nНа сегодня у вас запланировано:\n\n{events_list}\n\nХотите обсудить планы на день или нужна помощь с планированием?"
        
        # Сохраняем приветственное сообщение в историю
        db.save_chat_message(user_id, 'assistant', greeting)
        
        return json_response({
            'success': True,
            'greeting': greeting
        })
    except Exception as e:
        logger.error(f"Ошибка генерации приветствия: {e}", exc_info=True)
        return json_response({'error': str(e)}, status=500)


async def telegram_proxy_handler(request: web_request.Request):
    """
    Универсальный прокси для Telegram Mini App.
    Принимает запросы от Mini App и проксирует их к внутренним эндпоинтам.
    
    POST /api/telegram-proxy
    Body: {
        "endpoint": "/api/events",
        "method": "GET",
        "params": {"user_id": 123},
        "data": null
    }
    """
    try:
        # Получаем данные запроса
        try:
            proxy_data = await request.json()
        except Exception as e:
            logger.error(f"❌ Telegram Proxy: Invalid JSON: {e}")
            return json_response({'error': f'Invalid JSON: {str(e)}'}, status=400)
        
        endpoint = proxy_data.get('endpoint')
        method = proxy_data.get('method', 'GET').upper()
        params = proxy_data.get('params', {})
        data_payload = proxy_data.get('data')
        
        if not endpoint:
            return json_response({'error': 'endpoint required'}, status=400)
        
        logger.info(f"📡 Telegram Proxy: {method} {endpoint} params={params}")
        
        # Построим новый URL с параметрами
        from urllib.parse import urlencode
        query_string = urlencode(params) if params else ""
        # Используем localhost для внутренних запросов
        internal_url = f"http://localhost:8080{endpoint}"
        if query_string:
            internal_url += f"?{query_string}"
        
        # Используем aiohttp client для внутреннего запроса
        import aiohttp
        async with aiohttp.ClientSession() as session:
            try:
                if method == 'GET':
                    async with session.get(internal_url) as resp:
                        result = await resp.json()
                        status = resp.status
                elif method == 'POST':
                    async with session.post(internal_url, json=data_payload) as resp:
                        result = await resp.json()
                        status = resp.status
                elif method == 'PUT':
                    async with session.put(internal_url, json=data_payload) as resp:
                        result = await resp.json()
                        status = resp.status
                elif method == 'DELETE':
                    async with session.delete(internal_url) as resp:
                        result = await resp.json()
                        status = resp.status
                else:
                    return json_response({'error': f'Unsupported method: {method}'}, status=400)
                
                logger.info(f"✅ Telegram Proxy: Response {status}")
                return json_response(result, status=status)
            except Exception as e:
                logger.error(f"❌ Telegram Proxy: Internal request failed: {e}")
                return json_response({'error': f'Internal request failed: {str(e)}'}, status=500)
    
    except Exception as e:
        logger.error(f"❌ Telegram Proxy: Error: {e}", exc_info=True)
        return json_response({'error': str(e)}, status=500)


async def send_chat_message_handler(request: web_request.Request):
    """POST /api/chat/send - Отправить сообщение и получить ответ от AI."""
    try:
        data = await request.json()
        user_id = data.get('user_id')
        message = data.get('message')
        
        if not user_id or not message:
            return json_response({'error': 'user_id and message required'}, status=400)
        
        try:
            user_id = int(user_id)
        except ValueError:
            return json_response({'error': 'Invalid user_id'}, status=400)
        
        if not message.strip():
            return json_response({'error': 'Message cannot be empty'}, status=400)
        
        db = db_instance or Database()
        
        # Сохраняем сообщение пользователя
        db.save_chat_message(user_id, 'user', message.strip())

        # Получаем настройки пользователя
        user = db.get_or_create_user(user_id)
        timezone = user.get('timezone', 'Europe/Moscow') if isinstance(user, dict) else 'Europe/Moscow'
        locale = user.get('locale', 'ru_RU') if isinstance(user, dict) else 'ru_RU'
        interpretation_mode = user.get('interpretation_mode', 'soft') if isinstance(user, dict) else 'soft'

        # История чата для контекста (в т.ч. для follow-up команд вроде "перенеси на 16:00")
        chat_history = db.get_chat_messages(user_id, limit=50)

        # 1) Пытаемся обработать через decision_engine (создание/изменение событий, задач и т.д.)
        try:
            nlp, engine = _get_nlp_and_engine(db)
            last_event = db.get_last_event(user_id)

            extracted_data = await nlp.extract_intent_and_context(
                message.strip(),
                timezone,
                locale,
                last_event=last_event,
                is_reply=False,
                interpretation_mode=interpretation_mode,
                chat_history=chat_history,
            )

            result = await engine.process_intent(
                user_id,
                extracted_data,
                last_event=last_event,
                reply_to_event=None,
            )

            assistant_message = (result.get('message') or '').strip()
            if assistant_message:
                db.save_chat_message(user_id, 'assistant', assistant_message)

            return json_response({
                'success': True,
                'message': assistant_message,
                'action': result.get('action'),
                'event_id': result.get('event_id'),
                'needs_confirmation': result.get('needs_confirmation', False),
                'confirmation_type': result.get('confirmation_type'),
            })
        except Exception as e:
            logger.error(f"⚠️ Web chat: decision_engine failed, fallback to LLM-only: {e}", exc_info=True)

        # 2) Fallback: обычный LLM-ответ (без действий), как было раньше

        # Получаем события для контекста
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)
        events = db.get_events(user_id, limit=10, start_from=now, start_to=now + timedelta(days=30))

        # Формируем контекст событий
        events_context = ""
        if events:
            events_list = []
            for event in sorted(events[:5], key=lambda e: e.get('start_time', datetime.min)):
                start_time = event.get('start_time')
                title = event.get('title', 'Событие')

                if isinstance(start_time, datetime):
                    if start_time.tzinfo is None:
                        start_time = tz.localize(start_time)
                    time_str = start_time.strftime('%d.%m.%Y %H:%M')
                    events_list.append(f"- {time_str}: {title}")
                else:
                    events_list.append(f"- {title}")

            if events_list:
                events_context = f"\n\nБлижайшие события пользователя:\n" + "\n".join(events_list)

        # Формируем сообщения для AI
        messages = []

        # System prompt
        system_prompt = """Ты TRACY — дружелюбный AI-ассистент для планирования и управления календарем. 
Ты помогаешь пользователю:
- Планировать день и анализировать задачи
- Давать советы по тайм-менеджменту
- Обсуждать предстоящие события
- Помогать с организацией времени

Будь дружелюбным, полезным и кратки. Используй эмодзи где уместно."""

        messages.append({"role": "system", "content": system_prompt + events_context})

        # История чата
        for msg in chat_history:
            role = msg.get('role')
            content = msg.get('content', '')
            if role in ['user', 'assistant'] and content:
                messages.append({"role": role, "content": content})

        # Генерируем ответ через OpenRouter
        try:
            from openai import OpenAI

            ai_client = OpenAI(
                api_key=config.OPENROUTER_API_KEY,
                base_url=config.OPENROUTER_BASE_URL
            )

            response = ai_client.chat.completions.create(
                model=config.OPENROUTER_MODEL,
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )

            assistant_message = response.choices[0].message.content.strip()

            # Сохраняем ответ ассистента
            db.save_chat_message(user_id, 'assistant', assistant_message)

            return json_response({
                'success': True,
                'message': assistant_message
            })
        except Exception as e:
            logger.error(f"Ошибка генерации ответа AI: {e}", exc_info=True)
            return json_response({'error': f'Failed to generate response: {str(e)}'}, status=500)
        
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения: {e}", exc_info=True)
        return json_response({'error': str(e)}, status=500)


def create_app():
    """Создает и настраивает aiohttp приложение."""
    # Allow larger payloads for screenshots
    app = web.Application(client_max_size=12 * 1024 * 1024)  # 12MB
    
    # CORS middleware для разрешения запросов из веб-приложения
    @web.middleware
    async def cors_middleware(request, handler):
        # Разрешенные origins
        allowed_origins = [
            'https://karchauskas1.github.io',
            'http://localhost:3000',
            'http://localhost:3001',
        ]
        
        # Получаем origin из запроса
        origin = request.headers.get('Origin', '')
        
        # Определяем, какой origin разрешить
        allow_origin = None
        if origin in allowed_origins:
            allow_origin = origin
        elif origin.startswith('https://karchauskas1.github.io'):
            # Разрешаем любой поддомен GitHub Pages
            allow_origin = origin
        elif not origin:  # Для запросов без Origin (например, curl)
            allow_origin = '*'
        
        # Обработка preflight OPTIONS запросов
        if request.method == 'OPTIONS':
            response = web.Response(status=204)  # 204 No Content для OPTIONS
            if allow_origin:
                response.headers['Access-Control-Allow-Origin'] = allow_origin
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Access-Control-Max-Age'] = '3600'
            # Важно: для preflight также нужен Vary header
            response.headers['Vary'] = 'Origin'
            logger.info(f"✅ CORS preflight разрешен: {origin} -> {allow_origin}")
            return response
        
        try:
            response = await handler(request)
        except Exception as e:
            logger.error(f"Ошибка в handler: {e}", exc_info=True)
            response = json_response({'error': str(e)}, status=500)
        
        # Добавляем CORS заголовки ко всем ответам (включая ошибки)
        if allow_origin:
            response.headers['Access-Control-Allow-Origin'] = allow_origin
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        # Vary header для правильного кеширования CORS
        response.headers['Vary'] = 'Origin'
        
        return response
    
    app.middlewares.append(cors_middleware)
    
    # Регистрируем routes
    app.router.add_get('/', root_handler)
    app.router.add_get('/health', health_handler)
    app.router.add_get('/api/events', get_events_handler)
    app.router.add_get('/api/meetings', get_meetings_handler)
    app.router.add_get('/api/meetings/{meeting_id}', get_meeting_handler)
    app.router.add_post('/api/meetings/{meeting_id}/create-event', create_event_from_meeting_handler)
    app.router.add_post('/api/settings', update_settings_handler)
    app.router.add_get('/api/feedback', get_feedback_handler)
    app.router.add_post('/api/feedback/submit', submit_feedback_handler)
    app.router.add_get('/feedback/screenshots/{filename}', get_feedback_screenshot_handler)
    
    # To-Do Lists API
    app.router.add_get('/api/todo-lists', get_todo_lists_handler)
    app.router.add_post('/api/todo-lists', create_todo_list_handler)
    app.router.add_get('/api/todo-lists/{list_id}', get_todo_list_handler)
    app.router.add_put('/api/todo-lists/{list_id}', update_todo_list_handler)
    app.router.add_delete('/api/todo-lists/{list_id}', delete_todo_list_handler)
    app.router.add_post('/api/todo-lists/{list_id}/items', create_todo_item_handler)
    app.router.add_put('/api/todo-items/{item_id}', update_todo_item_handler)
    app.router.add_delete('/api/todo-items/{item_id}', delete_todo_item_handler)
    
    # Chat API
    app.router.add_get('/api/chat/messages', get_chat_messages_handler)
    app.router.add_get('/api/chat/greeting', generate_chat_greeting_handler)
    app.router.add_post('/api/chat/send', send_chat_message_handler)
    
    # Telegram Mini App Proxy - универсальный прокси для всех запросов
    app.router.add_post('/api/telegram-proxy', telegram_proxy_handler)
    
    return app


async def start_http_server(host: str = 'localhost', port: int = 8080):
    """Запускает HTTP сервер."""
    try:
        app = create_app()
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()
        logger.info(f"🌐 HTTP сервер запущен на http://{host}:{port}")
        logger.info(f"📡 Endpoint для получения событий: http://{host}:{port}/api/events?user_id=XXX")
        return runner
    except OSError as e:
        if "Address already in use" in str(e):
            logger.warning(f"⚠️ Порт {port} уже занят. HTTP сервер не запущен. Веб-приложение будет использовать fallback механизм.")
        else:
            logger.error(f"❌ Ошибка запуска HTTP сервера: {e}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"❌ Неожиданная ошибка запуска HTTP сервера: {e}", exc_info=True)
        return None

