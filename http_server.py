"""
Простой HTTP сервер для обслуживания запросов от веб-приложения.
Позволяет веб-приложению получать события напрямую из БД через HTTP API.
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from aiohttp import web, web_request
from aiohttp.web_response import json_response
import pytz
from database import Database
import config

logger = logging.getLogger(__name__)

# Глобальная ссылка на БД
db_instance: Optional[Database] = None


def set_database(db: Database):
    """Устанавливает глобальную ссылку на БД."""
    global db_instance
    db_instance = db


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
        
        if not db_instance:
            logger.error("❌ HTTP API: db_instance не инициализирован!")
            return json_response({'error': 'Database not initialized'}, status=500)

        try:
            # Получаем данные из БД
            feedback_list = db_instance.get_all_feedback(limit=limit, offset=offset)
            total_count = db_instance.get_feedback_count()
            
            # КРИТИЧЕСКАЯ ПРОВЕРКА: если feedback_list пустой, но total_count > 0, пробуем без offset
            if len(feedback_list) == 0 and total_count > 0:
                logger.warning(f"⚠️ HTTP API: feedback_list пустой при limit={limit}, offset={offset}, total={total_count}. Пробую без offset.")
                feedback_list = db_instance.get_all_feedback(limit=limit, offset=0)
                logger.info(f"📊 HTTP API: После повторного запроса получено {len(feedback_list)} записей")
        except Exception as e:
            logger.error(f"❌ HTTP API: Ошибка при получении обратной связи: {e}", exc_info=True)
            import traceback
            logger.error(traceback.format_exc())
            return json_response({'error': f'Failed to get feedback: {str(e)}'}, status=500)
        
        web_feedback = []
        logger.info(f"📊 HTTP API: Начинаю обработку {len(feedback_list)} записей")
        for idx, item in enumerate(feedback_list):
            logger.debug(f"📊 HTTP API: Обработка записи {idx+1}: {item}")
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
        
        logger.info(f"📊 HTTP API: Сформировано {len(web_feedback)} записей для ответа")
        logger.info(f"📊 HTTP API: Возвращаю ответ с {len(web_feedback)} записями, total={total_count}")
        
        return json_response({
            'feedback': web_feedback,
            'total': total_count,
            'limit': limit,
            'offset': offset
        })
    except Exception as e:
        logger.error(f"❌ HTTP API: Неожиданная ошибка get_feedback: {e}", exc_info=True)
        return json_response({'error': f'Internal server error: {str(e)}'}, status=500)


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


def create_app():
    """Создает и настраивает aiohttp приложение."""
    app = web.Application()
    
    # CORS middleware для разрешения запросов из веб-приложения
    async def cors_middleware(app, handler):
        async def middleware_handler(request):
            # Разрешаем CORS для всех источников (в production можно ограничить)
            if request.method == 'OPTIONS':
                response = web.Response()
                response.headers['Access-Control-Allow-Origin'] = '*'
                response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
                response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
                return response
            
            response = await handler(request)
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
            return response
        return middleware_handler
    
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

