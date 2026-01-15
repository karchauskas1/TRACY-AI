"""Система памяти диалога для поддержки естественных разговоров."""
import json
from typing import List, Dict, Optional
from datetime import datetime
import pytz


class ConversationMemory:
    """Управление памятью диалога и состоянием разговора."""

    def __init__(self, db):
        """
        Инициализация системы памяти диалога.

        Args:
            db: Экземпляр Database для работы с БД
        """
        self.db = db

    def add_message(self, user_id: int, role: str, content: str, intent: Optional[str] = None):
        """
        Добавить сообщение в историю диалога.

        Args:
            user_id: ID пользователя
            role: Роль отправителя ('user' или 'assistant')
            content: Содержимое сообщения
            intent: Извлеченный intent (если есть)
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()

        try:
            if self.db.use_postgresql:
                cursor.execute("""
                    INSERT INTO conversation_sessions (user_id, message_role, message_content, intent)
                    VALUES (%s, %s, %s, %s)
                """, (user_id, role, content, intent))
            else:
                cursor.execute("""
                    INSERT INTO conversation_sessions (user_id, message_role, message_content, intent)
                    VALUES (?, ?, ?, ?)
                """, (user_id, role, content, intent))

            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"❌ Ошибка добавления сообщения в историю: {e}")
        finally:
            self.db.return_connection(conn)

    def get_history(self, user_id: int, limit: int = 20) -> List[Dict]:
        """
        Получить историю диалога пользователя (скользящее окно).

        Args:
            user_id: ID пользователя
            limit: Количество последних сообщений (по умолчанию 20)

        Returns:
            Список словарей с сообщениями (от старых к новым)
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()

        try:
            if self.db.use_postgresql:
                cursor.execute("""
                    SELECT message_role, message_content, intent, created_at
                    FROM conversation_sessions
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                """, (user_id, limit))
            else:
                cursor.execute("""
                    SELECT message_role, message_content, intent, created_at
                    FROM conversation_sessions
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (user_id, limit))

            rows = cursor.fetchall()

            # Преобразуем в список словарей (реверсируем для порядка от старых к новым)
            messages = []
            for row in reversed(rows):
                messages.append({
                    'role': row['message_role'] if isinstance(row, dict) else row[0],
                    'content': row['message_content'] if isinstance(row, dict) else row[1],
                    'intent': row['intent'] if isinstance(row, dict) else row[2],
                    'created_at': row['created_at'] if isinstance(row, dict) else row[3]
                })

            return messages
        except Exception as e:
            print(f"❌ Ошибка получения истории диалога: {e}")
            return []
        finally:
            self.db.return_connection(conn)

    def get_state(self, user_id: int) -> Optional[Dict]:
        """
        Получить текущее состояние диалога пользователя.

        Args:
            user_id: ID пользователя

        Returns:
            Словарь с состоянием или None если состояния нет
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()

        try:
            if self.db.use_postgresql:
                cursor.execute("""
                    SELECT pending_action, partial_data, awaiting_field, context_event_id, updated_at
                    FROM conversation_state
                    WHERE user_id = %s
                """, (user_id,))
            else:
                cursor.execute("""
                    SELECT pending_action, partial_data, awaiting_field, context_event_id, updated_at
                    FROM conversation_state
                    WHERE user_id = ?
                """, (user_id,))

            row = cursor.fetchone()

            if not row:
                return None

            # Проверяем тайм-аут (10 минут)
            if isinstance(row, dict):
                updated_at = row['updated_at']
                partial_data_str = row['partial_data']
            else:
                updated_at = row[4]
                partial_data_str = row[1]

            if isinstance(updated_at, str):
                updated_at = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))

            time_diff = (datetime.now(pytz.UTC) - updated_at.replace(tzinfo=pytz.UTC)).total_seconds()
            if time_diff > 600:  # 10 минут
                # Состояние устарело - очищаем
                self.clear_state(user_id)
                return None

            # Парсим JSON partial_data
            partial_data = json.loads(partial_data_str) if partial_data_str else {}

            return {
                'pending_action': row['pending_action'] if isinstance(row, dict) else row[0],
                'partial_data': partial_data,
                'awaiting_field': row['awaiting_field'] if isinstance(row, dict) else row[2],
                'context_event_id': row['context_event_id'] if isinstance(row, dict) else row[3],
                'updated_at': updated_at
            }
        except Exception as e:
            print(f"❌ Ошибка получения состояния диалога: {e}")
            return None
        finally:
            self.db.return_connection(conn)

    def set_state(
        self,
        user_id: int,
        pending_action: str,
        partial_data: Dict,
        awaiting_field: str,
        context_event_id: Optional[int] = None
    ):
        """
        Установить состояние диалога пользователя.

        Args:
            user_id: ID пользователя
            pending_action: Ожидаемое действие ('create_event', 'delete_event', etc.)
            partial_data: Частично собранные данные (словарь)
            awaiting_field: Поле, которое ожидаем от пользователя ('time', 'title', etc.)
            context_event_id: ID события в контексте (опционально)
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()

        # Сериализуем partial_data в JSON
        partial_data_json = json.dumps(partial_data, ensure_ascii=False, default=str)

        try:
            if self.db.use_postgresql:
                # PostgreSQL: UPSERT (ON CONFLICT DO UPDATE)
                cursor.execute("""
                    INSERT INTO conversation_state (user_id, pending_action, partial_data, awaiting_field, context_event_id, updated_at)
                    VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (user_id)
                    DO UPDATE SET
                        pending_action = EXCLUDED.pending_action,
                        partial_data = EXCLUDED.partial_data,
                        awaiting_field = EXCLUDED.awaiting_field,
                        context_event_id = EXCLUDED.context_event_id,
                        updated_at = CURRENT_TIMESTAMP
                """, (user_id, pending_action, partial_data_json, awaiting_field, context_event_id))
            else:
                # SQLite: INSERT OR REPLACE
                cursor.execute("""
                    INSERT OR REPLACE INTO conversation_state (user_id, pending_action, partial_data, awaiting_field, context_event_id, updated_at)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (user_id, pending_action, partial_data_json, awaiting_field, context_event_id))

            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"❌ Ошибка установки состояния диалога: {e}")
        finally:
            self.db.return_connection(conn)

    def clear_state(self, user_id: int):
        """
        Очистить состояние диалога пользователя.

        Args:
            user_id: ID пользователя
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()

        try:
            if self.db.use_postgresql:
                cursor.execute("DELETE FROM conversation_state WHERE user_id = %s", (user_id,))
            else:
                cursor.execute("DELETE FROM conversation_state WHERE user_id = ?", (user_id,))

            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"❌ Ошибка очистки состояния диалога: {e}")
        finally:
            self.db.return_connection(conn)

    def update_partial_data(self, user_id: int, field: str, value):
        """
        Обновить одно поле в partial_data.

        Args:
            user_id: ID пользователя
            field: Имя поля
            value: Новое значение
        """
        state = self.get_state(user_id)
        if not state:
            print(f"⚠️ Нет активного состояния для пользователя {user_id}")
            return

        # Обновляем partial_data
        partial_data = state['partial_data']
        partial_data[field] = value

        # Сохраняем обновленное состояние
        self.set_state(
            user_id,
            state['pending_action'],
            partial_data,
            state['awaiting_field'],
            state.get('context_event_id')
        )

    def cleanup_old_messages(self, days: int = 30):
        """
        Удалить старые сообщения из истории диалога (для очистки БД).

        Args:
            days: Количество дней для хранения (по умолчанию 30)
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()

        try:
            if self.db.use_postgresql:
                cursor.execute("""
                    DELETE FROM conversation_sessions
                    WHERE created_at < NOW() - INTERVAL '%s days'
                """, (days,))
            else:
                cursor.execute("""
                    DELETE FROM conversation_sessions
                    WHERE created_at < datetime('now', '-%s days')
                """ % days)  # SQLite не поддерживает параметры в INTERVAL

            deleted_count = cursor.rowcount
            conn.commit()
            print(f"✅ Удалено {deleted_count} старых сообщений из истории диалога")
        except Exception as e:
            conn.rollback()
            print(f"❌ Ошибка очистки старых сообщений: {e}")
        finally:
            self.db.return_connection(conn)
