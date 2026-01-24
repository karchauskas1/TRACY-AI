"""
==============================================================================
DATABASE.PY - ОБЁРТКА С CONTEXT MANAGERS
==============================================================================

Предоставляет безопасные context managers для работы с базой данных.
Оборачивает существующий Database класс, добавляя:
- Автоматическое управление соединениями
- Поддержку транзакций
- Защиту от утечки соединений

ИСПОЛЬЗОВАНИЕ:
    from tracy.core.database import DatabaseService

    db_service = DatabaseService(legacy_db)

    # Простой запрос
    with db_service.connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")

    # Транзакция
    with db_service.transaction() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users ...")
        cursor.execute("INSERT INTO events ...")
        # commit автоматически при выходе без ошибки
        # rollback автоматически при исключении

==============================================================================
"""
import logging
from contextlib import contextmanager
from typing import Optional, Any, Generator
import sys
import os

# Добавляем родительскую директорию в path для импорта config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

logger = logging.getLogger(__name__)


class DatabaseService:
    """
    Сервис для работы с базой данных с поддержкой context managers.

    Оборачивает существующий Database класс, обеспечивая:
    - Безопасное управление соединениями
    - Автоматические транзакции
    - Защиту от утечки соединений при исключениях
    """

    def __init__(self, legacy_db: Optional[Any] = None):
        """
        Инициализация сервиса.

        Args:
            legacy_db: Существующий Database объект для обратной совместимости.
                       Если None, создаётся новый.
        """
        if legacy_db is not None:
            self._db = legacy_db
        else:
            # Ленивый импорт для избежания циклических зависимостей
            from database import Database
            self._db = Database()

        self._use_postgresql = getattr(self._db, 'use_postgresql', False)
        logger.info(f"DatabaseService инициализирован (PostgreSQL: {self._use_postgresql})")

    @property
    def legacy(self) -> Any:
        """Доступ к legacy Database для обратной совместимости."""
        return self._db

    @property
    def use_postgresql(self) -> bool:
        """Используется ли PostgreSQL."""
        return self._use_postgresql

    @contextmanager
    def connection(self) -> Generator:
        """
        Context manager для получения соединения с БД.

        Гарантирует возврат соединения в pool даже при исключении.

        Yields:
            Соединение с базой данных

        Example:
            with db_service.connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users")
                rows = cursor.fetchall()
        """
        conn = None
        try:
            conn = self._db.get_connection()
            yield conn
        except Exception as e:
            logger.error(f"Ошибка при работе с БД: {e}", exc_info=True)
            raise
        finally:
            if conn is not None:
                try:
                    self._db.return_connection(conn)
                except Exception as e:
                    logger.error(f"Ошибка при возврате соединения: {e}")

    @contextmanager
    def transaction(self) -> Generator:
        """
        Context manager для транзакции.

        - Автоматический commit при успешном выходе
        - Автоматический rollback при исключении
        - Гарантированный возврат соединения

        Yields:
            Соединение с базой данных (внутри транзакции)

        Example:
            with db_service.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO events ...")
                cursor.execute("INSERT INTO reminders ...")
                # commit автоматически
        """
        conn = None
        try:
            conn = self._db.get_connection()
            yield conn
            conn.commit()
            logger.debug("Транзакция успешно завершена (commit)")
        except Exception as e:
            if conn is not None:
                try:
                    conn.rollback()
                    logger.warning(f"Транзакция отменена (rollback): {e}")
                except Exception as rollback_error:
                    logger.error(f"Ошибка при rollback: {rollback_error}")
            raise
        finally:
            if conn is not None:
                try:
                    self._db.return_connection(conn)
                except Exception as e:
                    logger.error(f"Ошибка при возврате соединения: {e}")

    @contextmanager
    def cursor(self) -> Generator:
        """
        Context manager для получения cursor напрямую.

        Yields:
            Cursor базы данных

        Example:
            with db_service.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
                row = cursor.fetchone()
        """
        with self.connection() as conn:
            cursor = conn.cursor()
            try:
                yield cursor
                conn.commit()
            except Exception:
                conn.rollback()
                raise

    def execute(self, query: str, params: tuple = None) -> Any:
        """
        Выполнить запрос с автоматическим управлением соединением.

        Args:
            query: SQL запрос (с ? для параметров)
            params: Параметры запроса

        Returns:
            cursor после выполнения запроса
        """
        with self.connection() as conn:
            cursor = conn.cursor()
            self._db._execute(cursor, query, params)
            conn.commit()
            return cursor

    def fetchone(self, query: str, params: tuple = None) -> Optional[Any]:
        """
        Выполнить запрос и получить одну строку.

        Args:
            query: SQL запрос
            params: Параметры запроса

        Returns:
            Одна строка или None
        """
        with self.connection() as conn:
            cursor = conn.cursor()
            self._db._execute(cursor, query, params)
            return cursor.fetchone()

    def fetchall(self, query: str, params: tuple = None) -> list:
        """
        Выполнить запрос и получить все строки.

        Args:
            query: SQL запрос
            params: Параметры запроса

        Returns:
            Список строк
        """
        with self.connection() as conn:
            cursor = conn.cursor()
            self._db._execute(cursor, query, params)
            return cursor.fetchall()

    # =========================================================================
    # Прокси-методы к legacy Database для обратной совместимости
    # =========================================================================

    def get_or_create_user(self, user_id: int) -> dict:
        """Получить или создать пользователя."""
        return self._db.get_or_create_user(user_id)

    def save_event(self, **kwargs) -> int:
        """Сохранить событие."""
        return self._db.save_event(**kwargs)

    def get_events(self, user_id: int, from_date=None, to_date=None, limit: int = None) -> list:
        """Получить события пользователя."""
        return self._db.get_events(user_id, from_date, to_date, limit)

    def get_event_by_id(self, event_id: int, user_id: int) -> Optional[dict]:
        """Получить событие по ID."""
        return self._db.get_event_by_id(event_id, user_id)

    def update_event(self, event_id: int, user_id: int, **kwargs) -> bool:
        """Обновить событие."""
        return self._db.update_event(event_id, user_id, **kwargs)

    def delete_event(self, event_id: int, user_id: int) -> bool:
        """Удалить событие."""
        return self._db.delete_event(event_id, user_id)

    def save_reminder(self, **kwargs) -> int:
        """Сохранить напоминание."""
        return self._db.save_reminder(**kwargs)

    def get_pending_reminders(self, user_id: int = None) -> list:
        """Получить неотправленные напоминания."""
        return self._db.get_pending_reminders(user_id)

    def mark_reminder_sent(self, reminder_id: int) -> bool:
        """Пометить напоминание как отправленное."""
        return self._db.mark_reminder_sent(reminder_id)

    def get_user_settings(self, user_id: int) -> Optional[dict]:
        """Получить настройки пользователя."""
        return self._db.get_user_settings(user_id)

    def update_user_settings(self, user_id: int, **kwargs) -> bool:
        """Обновить настройки пользователя."""
        return self._db.update_user_settings(user_id, **kwargs)

    def get_calendar_connections(self, user_id: int) -> list:
        """Получить подключения к календарям."""
        return self._db.get_calendar_connections(user_id)

    def save_calendar_connection(self, **kwargs) -> int:
        """Сохранить подключение к календарю."""
        return self._db.save_calendar_connection(**kwargs)

    def get_last_event(self, user_id: int) -> Optional[dict]:
        """Получить последнее событие пользователя."""
        return self._db.get_last_event(user_id)

    def set_last_event(self, user_id: int, event_id: int) -> None:
        """Установить последнее событие пользователя."""
        return self._db.set_last_event(user_id, event_id)

    def find_similar_events(self, user_id: int, title: str, start_time, end_time=None) -> list:
        """Найти похожие события (для дедупликации)."""
        return self._db.find_similar_events(user_id, title, start_time, end_time)


# =========================================================================
# Глобальный экземпляр для удобного импорта
# =========================================================================

_default_service: Optional[DatabaseService] = None


def get_database_service(legacy_db: Optional[Any] = None) -> DatabaseService:
    """
    Получить экземпляр DatabaseService (singleton).

    Args:
        legacy_db: Опциональный legacy Database для инициализации

    Returns:
        DatabaseService instance
    """
    global _default_service
    if _default_service is None:
        _default_service = DatabaseService(legacy_db)
    return _default_service


def reset_database_service() -> None:
    """Сбросить глобальный экземпляр (для тестов)."""
    global _default_service
    _default_service = None
