"""
==============================================================================
MIDDLEWARE.PY - HTTP MIDDLEWARE ДЛЯ API
==============================================================================

Middleware для aiohttp сервера:
- CORS (Cross-Origin Resource Sharing)
- Аутентификация (JWT)
- Логирование запросов
- Обработка ошибок

==============================================================================
"""
import logging
import time
from typing import Callable, Optional, List

from aiohttp import web

logger = logging.getLogger(__name__)


# =============================================================================
# CORS Middleware
# =============================================================================

def create_cors_middleware(
    allowed_origins: Optional[List[str]] = None,
    allowed_methods: Optional[List[str]] = None,
    allowed_headers: Optional[List[str]] = None,
    max_age: int = 86400
) -> Callable:
    """
    Создать CORS middleware.

    Args:
        allowed_origins: Список разрешённых origins. None = все.
        allowed_methods: Разрешённые HTTP методы
        allowed_headers: Разрешённые заголовки
        max_age: Время кэширования preflight в секундах

    Returns:
        aiohttp middleware
    """
    if allowed_origins is None:
        allowed_origins = [
            "https://karchauskas1.github.io",
            "http://localhost:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3000"
        ]

    if allowed_methods is None:
        allowed_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]

    if allowed_headers is None:
        allowed_headers = [
            "Content-Type",
            "Authorization",
            "X-Requested-With",
            "Accept",
            "Origin"
        ]

    @web.middleware
    async def cors_middleware(request: web.Request, handler: Callable) -> web.Response:
        """CORS middleware."""
        origin = request.headers.get('Origin', '')

        # Проверяем origin
        if origin in allowed_origins or '*' in allowed_origins:
            cors_origin = origin
        else:
            cors_origin = allowed_origins[0] if allowed_origins else '*'

        # Обрабатываем preflight (OPTIONS)
        if request.method == 'OPTIONS':
            response = web.Response(status=204)
            response.headers['Access-Control-Allow-Origin'] = cors_origin
            response.headers['Access-Control-Allow-Methods'] = ', '.join(allowed_methods)
            response.headers['Access-Control-Allow-Headers'] = ', '.join(allowed_headers)
            response.headers['Access-Control-Max-Age'] = str(max_age)
            return response

        # Выполняем handler
        try:
            response = await handler(request)
        except web.HTTPException as e:
            response = e

        # Добавляем CORS заголовки к ответу
        response.headers['Access-Control-Allow-Origin'] = cors_origin
        response.headers['Access-Control-Allow-Credentials'] = 'true'

        return response

    return cors_middleware


# =============================================================================
# Request Logging Middleware
# =============================================================================

def create_logging_middleware(log_body: bool = False) -> Callable:
    """
    Создать middleware для логирования запросов.

    Args:
        log_body: Логировать ли тело запроса (осторожно с персональными данными)

    Returns:
        aiohttp middleware
    """
    @web.middleware
    async def logging_middleware(request: web.Request, handler: Callable) -> web.Response:
        """Логирование запросов."""
        start_time = time.time()

        # Логируем входящий запрос
        logger.info(f"➡️ {request.method} {request.path}")

        if log_body and request.body_exists:
            try:
                body = await request.text()
                logger.debug(f"Body: {body[:500]}...")  # Максимум 500 символов
            except:
                pass

        try:
            response = await handler(request)
            duration = (time.time() - start_time) * 1000

            # Логируем результат
            logger.info(
                f"⬅️ {request.method} {request.path} "
                f"→ {response.status} ({duration:.1f}ms)"
            )

            return response

        except Exception as e:
            duration = (time.time() - start_time) * 1000
            logger.error(
                f"❌ {request.method} {request.path} "
                f"→ Error ({duration:.1f}ms): {e}"
            )
            raise

    return logging_middleware


# =============================================================================
# Error Handling Middleware
# =============================================================================

def create_error_middleware() -> Callable:
    """
    Создать middleware для обработки ошибок.

    Преобразует все исключения в JSON ответы.

    Returns:
        aiohttp middleware
    """
    @web.middleware
    async def error_middleware(request: web.Request, handler: Callable) -> web.Response:
        """Обработка ошибок."""
        try:
            return await handler(request)

        except web.HTTPException as e:
            # HTTP исключения (404, 401, etc.)
            return web.json_response(
                {
                    'success': False,
                    'error': e.reason or str(e),
                    'status': e.status
                },
                status=e.status
            )

        except ValueError as e:
            # Ошибки валидации
            logger.warning(f"Validation error: {e}")
            return web.json_response(
                {
                    'success': False,
                    'error': str(e),
                    'code': 'VALIDATION_ERROR'
                },
                status=400
            )

        except Exception as e:
            # Все остальные ошибки
            logger.error(f"Unhandled error: {e}", exc_info=True)
            return web.json_response(
                {
                    'success': False,
                    'error': 'Internal server error',
                    'code': 'INTERNAL_ERROR'
                },
                status=500
            )

    return error_middleware


# =============================================================================
# Combined Setup
# =============================================================================

def setup_middlewares(
    app: web.Application,
    enable_cors: bool = True,
    enable_logging: bool = True,
    enable_errors: bool = True,
    enable_auth: bool = False,
    auth_service: Optional['JWTAuthService'] = None,
    cors_origins: Optional[List[str]] = None
) -> None:
    """
    Настроить все middleware для приложения.

    Args:
        app: aiohttp Application
        enable_cors: Включить CORS
        enable_logging: Включить логирование
        enable_errors: Включить обработку ошибок
        enable_auth: Включить JWT аутентификацию
        auth_service: JWTAuthService (если enable_auth=True)
        cors_origins: Список разрешённых origins для CORS
    """
    middlewares = []

    # Порядок важен!

    # 1. Обработка ошибок (первым для перехвата всех ошибок)
    if enable_errors:
        middlewares.append(create_error_middleware())

    # 2. Логирование
    if enable_logging:
        middlewares.append(create_logging_middleware())

    # 3. CORS (до аутентификации для preflight)
    if enable_cors:
        middlewares.append(create_cors_middleware(allowed_origins=cors_origins))

    # 4. Аутентификация
    if enable_auth and auth_service:
        from tracy.api.auth import create_auth_middleware
        middlewares.append(create_auth_middleware(auth_service))

    # Добавляем все middleware
    app.middlewares.extend(middlewares)

    logger.info(
        f"✓ Middleware настроены: "
        f"CORS={enable_cors}, Logging={enable_logging}, "
        f"Errors={enable_errors}, Auth={enable_auth}"
    )
