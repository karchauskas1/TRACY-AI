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

