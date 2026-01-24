"""
==============================================================================
STATE_SERVICE.PY - ПЕРСИСТЕНТНОЕ СОСТОЯНИЕ ПОЛЬЗОВАТЕЛЯ
==============================================================================

Замена context.user_data на персистентное хранилище.
Состояние сохраняется в БД и не теряется при рестарте бота.

ПРОБЛЕМА (раньше):
    # В bot.py
    context.user_data['waiting_meeting_audio'] = True
    # При рестарте бота - данные потеряны!

РЕШЕНИЕ (теперь):
    state_service = UserStateService(db, cache)
    state = await state_service.get_state(user_id)
    state.waiting_meeting_audio = True
    await state_service.save_state(state)
    # При рестарте бота - данные сохранены!

ИСПОЛЬЗОВАНИЕ:
    from tracy.services.state_service import UserStateService, UserState

    state_service = UserStateService(db, cache)

    # Получить состояние
    state = await state_service.get_state(user_id)

    # Изменить и сохранить
    state.waiting_meeting_audio = True
    await state_service.save_state(state)

    # Или через update
    await state_service.update(user_id, waiting_meeting_audio=True)

    # Очистить состояние
    await state_service.clear_state(user_id)

==============================================================================
"""
import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from tracy.core.database import DatabaseService
    from tracy.core.cache import CacheService

logger = logging.getLogger(__name__)


@dataclass
class UserState:
    """
    Персистентное состояние пользователя.

    Заменяет context.user_data из python-telegram-bot.
    Все поля здесь - это поля, которые раньше были в context.user_data.
    """

    user_id: int

    # ==========================================================================
    # Режимы работы
    # ==========================================================================

    # Режим расшифровки встреч
    waiting_meeting_audio: bool = False

    # Режим интерпретации AI ('soft' или 'strict')
    ai_mode: str = 'soft'

    # ==========================================================================
    # OAuth Flow
    # ==========================================================================

    # Ожидание URL от Google OAuth
    waiting_google_url: bool = False

    # ==========================================================================
    # iCloud Connection Flow
    # ==========================================================================

    # Шаг подключения iCloud: 'email', 'password', 'calendar_select', None
    icloud_step: Optional[str] = None

    # Apple ID email для iCloud
    icloud_email: Optional[str] = None

    # ==========================================================================
    # Feedback Flow
    # ==========================================================================

    # Тип обратной связи: 'bug', 'suggestion'
    feedback_type: Optional[str] = None

    # Шаг отправки feedback: 'text', 'screenshot', None
    feedback_step: Optional[str] = None

    # Текст комментария feedback
    feedback_text: Optional[str] = None

    # ==========================================================================
    # Event Operations
    # ==========================================================================

    # Тип ожидаемого подтверждения
    pending_confirmation: Optional[str] = None

    # ID события для переноса
    waiting_reschedule_event_id: Optional[int] = None

    # ==========================================================================
    # Meeting Data
    # ==========================================================================

    # Данные последней расшифрованной встречи
    last_meeting_data: Optional[dict] = field(default=None)

    # ==========================================================================
    # Timestamps
    # ==========================================================================

    # Время последнего обновления
    updated_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        """Конвертировать в словарь для сохранения."""
        data = asdict(self)
        # Удаляем user_id и updated_at из данных (они хранятся отдельно)
        data.pop('user_id', None)
        data.pop('updated_at', None)
        return data

    @classmethod
    def from_dict(cls, user_id: int, data: dict) -> 'UserState':
        """Создать из словаря."""
        # Фильтруем только известные поля
        known_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in known_fields}
        filtered_data['user_id'] = user_id
        return cls(**filtered_data)

    def reset(self) -> None:
        """Сбросить все поля до значений по умолчанию."""
        self.waiting_meeting_audio = False
        self.ai_mode = 'soft'
        self.waiting_google_url = False
        self.icloud_step = None
        self.icloud_email = None
        self.feedback_type = None
        self.feedback_step = None
        self.feedback_text = None
        self.pending_confirmation = None
        self.waiting_reschedule_event_id = None
        self.last_meeting_data = None

    def is_in_flow(self) -> bool:
        """Проверить, находится ли пользователь в каком-либо flow."""
        return any([
            self.waiting_meeting_audio,
            self.waiting_google_url,
            self.icloud_step is not None,
            self.feedback_step is not None,
            self.pending_confirmation is not None,
            self.waiting_reschedule_event_id is not None
        ])


class UserStateService:
    """
    Сервис для управления персистентным состоянием пользователей.

    Использует БД для хранения и опционально кэш для ускорения.
    """

    CACHE_TTL = 300  # 5 минут
    CACHE_KEY_PREFIX = "user_state"

    def __init__(
        self,
        db: 'DatabaseService',
        cache: Optional['CacheService'] = None
    ):
        """
        Args:
            db: DatabaseService для хранения состояния
            cache: Опциональный CacheService для ускорения
        """
        self._db = db
        self._cache = cache
        self._ensure_table_exists()
        logger.info("UserStateService инициализирован")

    def _ensure_table_exists(self) -> None:
        """Создать таблицу user_state если её нет."""
        try:
            with self._db.connection() as conn:
                cursor = conn.cursor()

                # Определяем тип БД
                if self._db.use_postgresql:
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS user_state (
                            user_id BIGINT PRIMARY KEY,
                            state_data JSONB NOT NULL DEFAULT '{}',
                            updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                else:
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS user_state (
                            user_id INTEGER PRIMARY KEY,
                            state_data TEXT NOT NULL DEFAULT '{}',
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)

                conn.commit()
                logger.debug("Таблица user_state проверена/создана")

        except Exception as e:
            logger.error(f"Ошибка создания таблицы user_state: {e}")

    def _cache_key(self, user_id: int) -> str:
        """Сгенерировать ключ кэша для пользователя."""
        return f"{self.CACHE_KEY_PREFIX}:{user_id}"

    async def get_state(self, user_id: int) -> UserState:
        """
        Получить состояние пользователя.

        Сначала проверяет кэш, затем БД.
        Если состояния нет - возвращает новое с дефолтными значениями.

        Args:
            user_id: ID пользователя

        Returns:
            UserState объект
        """
        # Пробуем кэш
        if self._cache:
            try:
                cached = await self._cache.get_json(self._cache_key(user_id))
                if cached:
                    logger.debug(f"State cache hit для user_id={user_id}")
                    return UserState.from_dict(user_id, cached)
            except Exception as e:
                logger.warning(f"Ошибка чтения state из кэша: {e}")

        # Читаем из БД
        try:
            with self._db.connection() as conn:
                cursor = conn.cursor()
                self._db.legacy._execute(
                    cursor,
                    "SELECT state_data FROM user_state WHERE user_id = ?",
                    (user_id,)
                )
                row = cursor.fetchone()

                if row:
                    state_data = row[0] if isinstance(row, tuple) else row['state_data']
                    if isinstance(state_data, str):
                        state_data = json.loads(state_data)
                    state = UserState.from_dict(user_id, state_data)

                    # Обновляем кэш
                    if self._cache:
                        await self._cache.set_json(
                            self._cache_key(user_id),
                            state.to_dict(),
                            self.CACHE_TTL
                        )

                    return state

        except Exception as e:
            logger.error(f"Ошибка чтения state из БД: {e}")

        # Возвращаем новое состояние
        return UserState(user_id=user_id)

    async def save_state(self, state: UserState) -> bool:
        """
        Сохранить состояние пользователя.

        Args:
            state: UserState объект для сохранения

        Returns:
            True если успешно
        """
        try:
            state_data = state.to_dict()
            state_json = json.dumps(state_data, ensure_ascii=False, default=str)

            with self._db.transaction() as conn:
                cursor = conn.cursor()

                if self._db.use_postgresql:
                    self._db.legacy._execute(
                        cursor,
                        """
                        INSERT INTO user_state (user_id, state_data, updated_at)
                        VALUES (?, ?::jsonb, CURRENT_TIMESTAMP)
                        ON CONFLICT (user_id) DO UPDATE
                        SET state_data = ?::jsonb, updated_at = CURRENT_TIMESTAMP
                        """,
                        (state.user_id, state_json, state_json)
                    )
                else:
                    self._db.legacy._execute(
                        cursor,
                        """
                        INSERT OR REPLACE INTO user_state (user_id, state_data, updated_at)
                        VALUES (?, ?, CURRENT_TIMESTAMP)
                        """,
                        (state.user_id, state_json)
                    )

            # Обновляем кэш
            if self._cache:
                await self._cache.set_json(
                    self._cache_key(state.user_id),
                    state_data,
                    self.CACHE_TTL
                )

            logger.debug(f"State сохранён для user_id={state.user_id}")
            return True

        except Exception as e:
            logger.error(f"Ошибка сохранения state: {e}")
            return False

    async def update(self, user_id: int, **kwargs) -> UserState:
        """
        Обновить отдельные поля состояния.

        Args:
            user_id: ID пользователя
            **kwargs: Поля для обновления

        Returns:
            Обновлённый UserState

        Example:
            state = await state_service.update(
                user_id,
                waiting_meeting_audio=True,
                feedback_type='bug'
            )
        """
        state = await self.get_state(user_id)

        for key, value in kwargs.items():
            if hasattr(state, key):
                setattr(state, key, value)
            else:
                logger.warning(f"Неизвестное поле state: {key}")

        await self.save_state(state)
        return state

    async def clear_state(self, user_id: int) -> bool:
        """
        Очистить состояние пользователя (сбросить до дефолтов).

        Args:
            user_id: ID пользователя

        Returns:
            True если успешно
        """
        state = UserState(user_id=user_id)
        return await self.save_state(state)

    async def delete_state(self, user_id: int) -> bool:
        """
        Полностью удалить состояние пользователя из БД.

        Args:
            user_id: ID пользователя

        Returns:
            True если успешно
        """
        try:
            with self._db.transaction() as conn:
                cursor = conn.cursor()
                self._db.legacy._execute(
                    cursor,
                    "DELETE FROM user_state WHERE user_id = ?",
                    (user_id,)
                )

            # Удаляем из кэша
            if self._cache:
                await self._cache.delete(self._cache_key(user_id))

            logger.debug(f"State удалён для user_id={user_id}")
            return True

        except Exception as e:
            logger.error(f"Ошибка удаления state: {e}")
            return False


# =============================================================================
# Context Integration Helper
# =============================================================================

class ContextStateAdapter:
    """
    Адаптер для совместимости с context.user_data.

    Позволяет использовать новый state service как словарь,
    сохраняя обратную совместимость с существующим кодом.

    ИСПОЛЬЗОВАНИЕ:
        # В handlers
        state = await get_user_state(context, user_id)
        state['waiting_meeting_audio'] = True
        await save_user_state(context, user_id)
    """

    def __init__(self, state: UserState, state_service: UserStateService):
        self._state = state
        self._service = state_service
        self._dirty = False

    def __getitem__(self, key: str) -> Any:
        if hasattr(self._state, key):
            return getattr(self._state, key)
        return None

    def __setitem__(self, key: str, value: Any) -> None:
        if hasattr(self._state, key):
            setattr(self._state, key, value)
            self._dirty = True
        else:
            logger.warning(f"Попытка установить неизвестное поле state: {key}")

    def __contains__(self, key: str) -> bool:
        return hasattr(self._state, key)

    def get(self, key: str, default: Any = None) -> Any:
        if hasattr(self._state, key):
            value = getattr(self._state, key)
            return value if value is not None else default
        return default

    def pop(self, key: str, default: Any = None) -> Any:
        """Получить значение и сбросить его."""
        value = self.get(key, default)
        if hasattr(self._state, key):
            # Сбрасываем до дефолтного значения поля
            field_info = self._state.__dataclass_fields__.get(key)
            if field_info:
                default_value = field_info.default if field_info.default is not field_info.default_factory else None
                setattr(self._state, key, default_value)
                self._dirty = True
        return value

    async def save(self) -> bool:
        """Сохранить изменения если были."""
        if self._dirty:
            result = await self._service.save_state(self._state)
            self._dirty = False
            return result
        return True

    @property
    def state(self) -> UserState:
        """Прямой доступ к UserState."""
        return self._state
