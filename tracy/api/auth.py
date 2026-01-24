"""
==============================================================================
AUTH.PY - JWT АУТЕНТИФИКАЦИЯ ДЛЯ WEB API
==============================================================================

Модуль аутентификации для HTTP API:
- Верификация Telegram initData (Mini App)
- Генерация и валидация JWT токенов
- Middleware для защиты endpoints

ИСПОЛЬЗОВАНИЕ:
    from tracy.api.auth import JWTAuthService, auth_middleware

    auth_service = JWTAuthService(secret_key="your-secret")

    # Получение токена
    token = auth_service.create_token(user_id=12345)

    # Верификация
    payload = auth_service.verify_token(token)

FLOW АВТОРИЗАЦИИ:
    1. Mini App отправляет initData на POST /api/auth/token
    2. Сервер верифицирует initData через Telegram Bot Token
    3. Сервер генерирует JWT токен
    4. Клиент использует токен в Authorization: Bearer <token>
    5. Middleware проверяет токен на каждом protected endpoint

==============================================================================
"""
import hashlib
import hmac
import json
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Callable, Any
from urllib.parse import parse_qs, unquote

from aiohttp import web

logger = logging.getLogger(__name__)

# Пытаемся импортировать PyJWT
try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    logger.warning("PyJWT не установлен. JWT аутентификация недоступна. Установите: pip install PyJWT")


@dataclass
class TokenPayload:
    """Payload JWT токена."""
    user_id: int
    exp: datetime
    iat: datetime
    telegram_hash: Optional[str] = None


class JWTAuthService:
    """
    Сервис JWT аутентификации.

    Генерирует и валидирует JWT токены для авторизации API запросов.
    """

    def __init__(
        self,
        secret_key: Optional[str] = None,
        algorithm: str = "HS256",
        token_ttl_hours: int = 24
    ):
        """
        Args:
            secret_key: Секретный ключ для подписи токенов.
                       Если не задан, берётся из JWT_SECRET_KEY.
            algorithm: Алгоритм подписи (по умолчанию HS256)
            token_ttl_hours: Время жизни токена в часах (по умолчанию 24)
        """
        self.secret_key = secret_key or os.getenv('JWT_SECRET_KEY')
        self.algorithm = algorithm
        self.token_ttl = timedelta(hours=token_ttl_hours)

        if not self.secret_key:
            # Генерируем временный ключ для разработки
            import secrets
            self.secret_key = secrets.token_urlsafe(32)
            logger.warning(
                "JWT_SECRET_KEY не задан! Используется временный ключ. "
                f"Добавьте в .env:\nJWT_SECRET_KEY={self.secret_key}"
            )

        if not JWT_AVAILABLE:
            logger.error("PyJWT не установлен - JWT аутентификация не работает!")

    def create_token(
        self,
        user_id: int,
        telegram_hash: Optional[str] = None,
        extra_claims: Optional[dict] = None
    ) -> str:
        """
        Создать JWT токен для пользователя.

        Args:
            user_id: ID пользователя Telegram
            telegram_hash: Hash от initData (для отзыва токенов)
            extra_claims: Дополнительные claims

        Returns:
            JWT токен строкой

        Raises:
            RuntimeError: Если PyJWT не установлен
        """
        if not JWT_AVAILABLE:
            raise RuntimeError("PyJWT не установлен")

        now = datetime.utcnow()
        payload = {
            "user_id": user_id,
            "iat": now,
            "exp": now + self.token_ttl,
            "type": "access"
        }

        if telegram_hash:
            payload["tg_hash"] = telegram_hash

        if extra_claims:
            payload.update(extra_claims)

        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        logger.debug(f"Создан JWT токен для user_id={user_id}")
        return token

    def verify_token(self, token: str) -> Optional[TokenPayload]:
        """
        Верифицировать и декодировать JWT токен.

        Args:
            token: JWT токен

        Returns:
            TokenPayload если токен валиден, иначе None
        """
        if not JWT_AVAILABLE:
            logger.error("PyJWT не установлен")
            return None

        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )

            return TokenPayload(
                user_id=payload["user_id"],
                exp=datetime.fromtimestamp(payload["exp"]),
                iat=datetime.fromtimestamp(payload["iat"]),
                telegram_hash=payload.get("tg_hash")
            )

        except jwt.ExpiredSignatureError:
            logger.debug("JWT токен истёк")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Невалидный JWT токен: {e}")
            return None

    def refresh_token(self, token: str) -> Optional[str]:
        """
        Обновить JWT токен (если он ещё валиден).

        Args:
            token: Текущий JWT токен

        Returns:
            Новый JWT токен или None если текущий невалиден
        """
        payload = self.verify_token(token)
        if payload:
            return self.create_token(
                user_id=payload.user_id,
                telegram_hash=payload.telegram_hash
            )
        return None


class TelegramInitDataVerifier:
    """
    Верификация initData от Telegram Mini App.

    Использует Bot Token для проверки подписи данных от Telegram.
    """

    def __init__(self, bot_token: str):
        """
        Args:
            bot_token: Токен Telegram бота
        """
        self.bot_token = bot_token
        # Секретный ключ = HMAC-SHA256(bot_token, "WebAppData")
        self._secret_key = hmac.new(
            b"WebAppData",
            bot_token.encode(),
            hashlib.sha256
        ).digest()

    def verify(self, init_data: str) -> Optional[dict]:
        """
        Верифицировать initData от Telegram.

        Args:
            init_data: URL-encoded строка initData

        Returns:
            Распарсенные данные если подпись верна, иначе None
        """
        try:
            # Парсим URL-encoded данные
            parsed = parse_qs(init_data)
            received_hash = parsed.get('hash', [None])[0]

            if not received_hash:
                logger.warning("initData не содержит hash")
                return None

            # Собираем строку для проверки подписи
            # Сортируем по ключам, исключаем hash
            data_check_parts = []
            for key in sorted(parsed.keys()):
                if key != 'hash':
                    data_check_parts.append(f"{key}={parsed[key][0]}")

            data_check_string = '\n'.join(data_check_parts)

            # Вычисляем ожидаемый hash
            expected_hash = hmac.new(
                self._secret_key,
                data_check_string.encode(),
                hashlib.sha256
            ).hexdigest()

            # Безопасное сравнение
            if not hmac.compare_digest(received_hash, expected_hash):
                logger.warning("initData: hash не совпадает")
                return None

            # Парсим результат
            result = {'hash': received_hash}
            for key, values in parsed.items():
                if key == 'user':
                    # user - это JSON
                    result['user'] = json.loads(unquote(values[0]))
                elif key == 'hash':
                    continue
                else:
                    result[key] = values[0]

            logger.debug(f"initData верифицирован для user_id={result.get('user', {}).get('id')}")
            return result

        except Exception as e:
            logger.error(f"Ошибка верификации initData: {e}")
            return None

    def get_user_id(self, init_data: str) -> Optional[int]:
        """
        Быстрое извлечение user_id из initData.

        Args:
            init_data: URL-encoded строка initData

        Returns:
            user_id если верификация успешна
        """
        verified = self.verify(init_data)
        if verified and 'user' in verified:
            return verified['user'].get('id')
        return None


def create_auth_middleware(
    auth_service: JWTAuthService,
    exclude_paths: Optional[list] = None
) -> Callable:
    """
    Создать aiohttp middleware для JWT аутентификации.

    Args:
        auth_service: Экземпляр JWTAuthService
        exclude_paths: Пути, не требующие аутентификации

    Returns:
        aiohttp middleware function
    """
    exclude_paths = exclude_paths or [
        '/',
        '/health',
        '/api/auth/token',
        '/api/auth/telegram'
    ]

    @web.middleware
    async def auth_middleware(request: web.Request, handler: Callable) -> web.Response:
        """Middleware для проверки JWT токена."""

        # Пропускаем excluded paths
        if request.path in exclude_paths:
            return await handler(request)

        # Также пропускаем OPTIONS для CORS preflight
        if request.method == 'OPTIONS':
            return await handler(request)

        # Получаем токен из заголовка
        auth_header = request.headers.get('Authorization', '')

        if not auth_header.startswith('Bearer '):
            return web.json_response(
                {'error': 'Missing or invalid Authorization header', 'code': 'UNAUTHORIZED'},
                status=401
            )

        token = auth_header[7:]  # Убираем 'Bearer '

        # Верифицируем токен
        payload = auth_service.verify_token(token)

        if not payload:
            return web.json_response(
                {'error': 'Invalid or expired token', 'code': 'TOKEN_INVALID'},
                status=401
            )

        # Добавляем user_id в request для использования в handlers
        request['user_id'] = payload.user_id
        request['token_payload'] = payload

        return await handler(request)

    return auth_middleware


# =============================================================================
# API Handlers для аутентификации
# =============================================================================

async def token_handler(request: web.Request) -> web.Response:
    """
    POST /api/auth/token

    Получение JWT токена по Telegram initData.

    Body:
        {
            "init_data": "query_id=...&user=...&hash=..."
        }

    Response:
        {
            "success": true,
            "token": "eyJ...",
            "user_id": 12345,
            "expires_in": 86400
        }
    """
    try:
        data = await request.json()
        init_data = data.get('init_data')

        if not init_data:
            return web.json_response(
                {'success': False, 'error': 'init_data is required'},
                status=400
            )

        # Получаем сервисы из app
        verifier: TelegramInitDataVerifier = request.app.get('telegram_verifier')
        auth_service: JWTAuthService = request.app.get('auth_service')

        if not verifier or not auth_service:
            logger.error("Auth services not configured")
            return web.json_response(
                {'success': False, 'error': 'Server configuration error'},
                status=500
            )

        # Верифицируем initData
        verified = verifier.verify(init_data)

        if not verified or 'user' not in verified:
            return web.json_response(
                {'success': False, 'error': 'Invalid Telegram initData'},
                status=401
            )

        user_id = verified['user']['id']
        tg_hash = verified.get('hash')

        # Создаём JWT токен
        token = auth_service.create_token(user_id=user_id, telegram_hash=tg_hash)

        return web.json_response({
            'success': True,
            'token': token,
            'user_id': user_id,
            'expires_in': int(auth_service.token_ttl.total_seconds())
        })

    except json.JSONDecodeError:
        return web.json_response(
            {'success': False, 'error': 'Invalid JSON'},
            status=400
        )
    except Exception as e:
        logger.error(f"Error in token_handler: {e}", exc_info=True)
        return web.json_response(
            {'success': False, 'error': 'Internal server error'},
            status=500
        )


async def refresh_token_handler(request: web.Request) -> web.Response:
    """
    POST /api/auth/refresh

    Обновление JWT токена.

    Headers:
        Authorization: Bearer <current_token>

    Response:
        {
            "success": true,
            "token": "eyJ...",
            "expires_in": 86400
        }
    """
    try:
        auth_header = request.headers.get('Authorization', '')

        if not auth_header.startswith('Bearer '):
            return web.json_response(
                {'success': False, 'error': 'Missing Authorization header'},
                status=401
            )

        current_token = auth_header[7:]
        auth_service: JWTAuthService = request.app.get('auth_service')

        new_token = auth_service.refresh_token(current_token)

        if not new_token:
            return web.json_response(
                {'success': False, 'error': 'Token cannot be refreshed'},
                status=401
            )

        return web.json_response({
            'success': True,
            'token': new_token,
            'expires_in': int(auth_service.token_ttl.total_seconds())
        })

    except Exception as e:
        logger.error(f"Error in refresh_token_handler: {e}", exc_info=True)
        return web.json_response(
            {'success': False, 'error': 'Internal server error'},
            status=500
        )


def setup_auth_routes(app: web.Application) -> None:
    """
    Настроить роуты аутентификации.

    Args:
        app: aiohttp Application
    """
    app.router.add_post('/api/auth/token', token_handler)
    app.router.add_post('/api/auth/refresh', refresh_token_handler)
    logger.info("Auth routes configured: /api/auth/token, /api/auth/refresh")
