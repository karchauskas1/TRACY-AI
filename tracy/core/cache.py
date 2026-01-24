"""
==============================================================================
CACHE.PY - КЭШИРОВАНИЕ ДАННЫХ
==============================================================================

Модуль для кэширования часто запрашиваемых данных:
- Настройки пользователей
- Подключения к календарям
- Последние события

ИСПОЛЬЗОВАНИЕ:
    from tracy.core.cache import InMemoryCache, get_cache

    cache = InMemoryCache()

    # Простое использование
    await cache.set("key", "value", ttl_seconds=300)
    value = await cache.get("key")
    await cache.delete("key")

    # С декоратором
    @cached("user_settings", ttl=300)
    async def get_user_settings(user_id: int):
        return await db.get_user_settings(user_id)

ПОДДЕРЖИВАЕМЫЕ БЭКЕНДЫ:
    - InMemoryCache: для single-instance (разработка)
    - RedisCache: для production (масштабирование)

==============================================================================
"""
import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import wraps
from typing import Optional, Any, Callable, TypeVar, ParamSpec

logger = logging.getLogger(__name__)

P = ParamSpec('P')
T = TypeVar('T')


# =============================================================================
# Cache Keys
# =============================================================================

class CacheKeys:
    """Константы для ключей кэша."""

    @staticmethod
    def user_settings(user_id: int) -> str:
        return f"user:{user_id}:settings"

    @staticmethod
    def user_calendars(user_id: int) -> str:
        return f"user:{user_id}:calendars"

    @staticmethod
    def user_last_event(user_id: int) -> str:
        return f"user:{user_id}:last_event"

    @staticmethod
    def user_state(user_id: int) -> str:
        return f"user:{user_id}:state"

    @staticmethod
    def user_today_events(user_id: int) -> str:
        return f"user:{user_id}:events:today"


# =============================================================================
# Cache Item
# =============================================================================

@dataclass
class CacheItem:
    """Элемент кэша с временем истечения."""
    value: str
    expires_at: float

    @property
    def is_expired(self) -> bool:
        return time.time() > self.expires_at


# =============================================================================
# Abstract Cache Interface
# =============================================================================

class CacheService(ABC):
    """Абстрактный интерфейс кэша."""

    @abstractmethod
    async def get(self, key: str) -> Optional[str]:
        """Получить значение по ключу."""
        pass

    @abstractmethod
    async def set(self, key: str, value: str, ttl_seconds: int = 300) -> None:
        """Установить значение с TTL."""
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Удалить значение по ключу."""
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Проверить существование ключа."""
        pass

    async def get_json(self, key: str) -> Optional[dict]:
        """Получить значение как JSON."""
        value = await self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return None
        return None

    async def set_json(self, key: str, value: dict, ttl_seconds: int = 300) -> None:
        """Установить значение как JSON."""
        await self.set(key, json.dumps(value, ensure_ascii=False), ttl_seconds)

    async def get_or_set(
        self,
        key: str,
        factory: Callable[[], Any],
        ttl_seconds: int = 300
    ) -> Any:
        """
        Получить значение из кэша или вычислить и сохранить.

        Args:
            key: Ключ кэша
            factory: Функция для вычисления значения (может быть async)
            ttl_seconds: TTL для нового значения

        Returns:
            Значение из кэша или вычисленное
        """
        value = await self.get(key)
        if value is not None:
            return value

        # Вычисляем новое значение
        if asyncio.iscoroutinefunction(factory):
            new_value = await factory()
        else:
            new_value = factory()

        if new_value is not None:
            if isinstance(new_value, (dict, list)):
                await self.set_json(key, new_value, ttl_seconds)
            else:
                await self.set(key, str(new_value), ttl_seconds)

        return new_value


# =============================================================================
# In-Memory Cache
# =============================================================================

class InMemoryCache(CacheService):
    """
    Простой in-memory кэш.

    Подходит для:
    - Разработки
    - Single-instance deployment
    - Тестирования

    НЕ подходит для:
    - Multi-instance deployment (данные не разделяются)
    - Production с большим объёмом данных
    """

    def __init__(self, cleanup_interval: int = 60):
        """
        Args:
            cleanup_interval: Интервал очистки устаревших записей (секунды)
        """
        self._cache: dict[str, CacheItem] = {}
        self._lock = asyncio.Lock()
        self._cleanup_interval = cleanup_interval
        self._cleanup_task: Optional[asyncio.Task] = None
        logger.info("InMemoryCache инициализирован")

    async def start_cleanup(self) -> None:
        """Запустить фоновую очистку."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop_cleanup(self) -> None:
        """Остановить фоновую очистку."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            self._cleanup_task = None

    async def _cleanup_loop(self) -> None:
        """Фоновый цикл очистки устаревших записей."""
        while True:
            try:
                await asyncio.sleep(self._cleanup_interval)
                await self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Ошибка в cleanup loop: {e}")

    async def _cleanup_expired(self) -> None:
        """Удалить устаревшие записи."""
        async with self._lock:
            expired_keys = [
                key for key, item in self._cache.items()
                if item.is_expired
            ]
            for key in expired_keys:
                del self._cache[key]

            if expired_keys:
                logger.debug(f"Очищено {len(expired_keys)} устаревших записей из кэша")

    async def get(self, key: str) -> Optional[str]:
        """Получить значение по ключу."""
        async with self._lock:
            item = self._cache.get(key)
            if item is None:
                return None
            if item.is_expired:
                del self._cache[key]
                return None
            return item.value

    async def set(self, key: str, value: str, ttl_seconds: int = 300) -> None:
        """Установить значение с TTL."""
        async with self._lock:
            self._cache[key] = CacheItem(
                value=value,
                expires_at=time.time() + ttl_seconds
            )

    async def delete(self, key: str) -> None:
        """Удалить значение по ключу."""
        async with self._lock:
            self._cache.pop(key, None)

    async def exists(self, key: str) -> bool:
        """Проверить существование ключа."""
        async with self._lock:
            item = self._cache.get(key)
            if item is None:
                return False
            if item.is_expired:
                del self._cache[key]
                return False
            return True

    async def clear(self) -> None:
        """Очистить весь кэш."""
        async with self._lock:
            self._cache.clear()

    async def size(self) -> int:
        """Получить количество записей в кэше."""
        async with self._lock:
            return len(self._cache)

    def stats(self) -> dict:
        """Получить статистику кэша."""
        return {
            "type": "InMemoryCache",
            "size": len(self._cache),
            "cleanup_interval": self._cleanup_interval
        }


# =============================================================================
# Redis Cache (опционально)
# =============================================================================

class RedisCache(CacheService):
    """
    Redis-based кэш для production.

    Требует: pip install redis

    Преимущества:
    - Разделение данных между instances
    - Персистентность
    - Масштабирование
    """

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        """
        Args:
            redis_url: URL для подключения к Redis
        """
        self._redis_url = redis_url
        self._redis = None
        self._initialized = False

    async def _ensure_connected(self) -> None:
        """Убедиться, что подключение к Redis установлено."""
        if self._initialized:
            return

        try:
            import redis.asyncio as redis
            self._redis = redis.from_url(self._redis_url)
            await self._redis.ping()
            self._initialized = True
            logger.info(f"RedisCache подключен к {self._redis_url}")
        except ImportError:
            raise RuntimeError("redis не установлен. Установите: pip install redis")
        except Exception as e:
            raise RuntimeError(f"Не удалось подключиться к Redis: {e}")

    async def get(self, key: str) -> Optional[str]:
        """Получить значение по ключу."""
        await self._ensure_connected()
        value = await self._redis.get(key)
        return value.decode('utf-8') if value else None

    async def set(self, key: str, value: str, ttl_seconds: int = 300) -> None:
        """Установить значение с TTL."""
        await self._ensure_connected()
        await self._redis.setex(key, ttl_seconds, value)

    async def delete(self, key: str) -> None:
        """Удалить значение по ключу."""
        await self._ensure_connected()
        await self._redis.delete(key)

    async def exists(self, key: str) -> bool:
        """Проверить существование ключа."""
        await self._ensure_connected()
        return await self._redis.exists(key) > 0

    async def close(self) -> None:
        """Закрыть подключение к Redis."""
        if self._redis:
            await self._redis.close()
            self._initialized = False


# =============================================================================
# Cache Decorator
# =============================================================================

def cached(
    key_prefix: str,
    ttl: int = 300,
    key_builder: Optional[Callable[..., str]] = None
):
    """
    Декоратор для кэширования результатов функции.

    Args:
        key_prefix: Префикс ключа кэша
        ttl: Время жизни кэша в секундах
        key_builder: Функция для построения ключа из аргументов

    Example:
        @cached("user_settings", ttl=300)
        async def get_user_settings(user_id: int):
            return await db.get_user_settings(user_id)
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            cache = get_cache()
            if cache is None:
                # Кэш не доступен, выполняем функцию напрямую
                return await func(*args, **kwargs)

            # Строим ключ
            if key_builder:
                key = f"{key_prefix}:{key_builder(*args, **kwargs)}"
            else:
                # Автоматическое построение ключа из аргументов
                key_parts = [str(arg) for arg in args]
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                key = f"{key_prefix}:{':'.join(key_parts)}"

            # Пробуем получить из кэша
            cached_value = await cache.get_json(key)
            if cached_value is not None:
                logger.debug(f"Cache hit: {key}")
                return cached_value

            # Выполняем функцию
            logger.debug(f"Cache miss: {key}")
            result = await func(*args, **kwargs)

            # Сохраняем в кэш
            if result is not None:
                await cache.set_json(key, result, ttl)

            return result

        return wrapper
    return decorator


# =============================================================================
# Global Cache Instance
# =============================================================================

_global_cache: Optional[CacheService] = None


def get_cache() -> Optional[CacheService]:
    """Получить глобальный экземпляр кэша."""
    return _global_cache


def set_cache(cache: CacheService) -> None:
    """Установить глобальный экземпляр кэша."""
    global _global_cache
    _global_cache = cache


def create_cache(backend: str = "memory", **kwargs) -> CacheService:
    """
    Создать и установить глобальный кэш.

    Args:
        backend: Тип бэкенда ("memory" или "redis")
        **kwargs: Аргументы для конструктора

    Returns:
        Созданный экземпляр кэша
    """
    if backend == "memory":
        cache = InMemoryCache(**kwargs)
    elif backend == "redis":
        redis_url = kwargs.get("redis_url", "redis://localhost:6379")
        cache = RedisCache(redis_url)
    else:
        raise ValueError(f"Unknown cache backend: {backend}")

    set_cache(cache)
    return cache
