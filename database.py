"""Управление базой данных PostgreSQL/SQLite для хранения пользовательских данных."""
import json
import logging
from datetime import datetime
from typing import Optional, Dict, List, Tuple
import pytz
import config

logger = logging.getLogger(__name__)

# Определяем тип БД
USE_POSTGRESQL = bool(config.DATABASE_URL)

if USE_POSTGRESQL:
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        from psycopg2.pool import SimpleConnectionPool
        POSTGRESQL_AVAILABLE = True
    except ImportError:
        logger.warning("psycopg2 не установлен, но DATABASE_URL указан. Установите: pip install psycopg2-binary")
        POSTGRESQL_AVAILABLE = False
        USE_POSTGRESQL = False
else:
    POSTGRESQL_AVAILABLE = False

if not USE_POSTGRESQL:
    try:
        import sqlite3
        SQLITE_AVAILABLE = True
    except ImportError:
        SQLITE_AVAILABLE = False
        logger.error("SQLite недоступен. Установите Python с поддержкой SQLite.")


class Database:
    """Класс для работы с базой данных (PostgreSQL или SQLite)."""
    
    def __init__(self, db_path: str = None, db_url: str = None):
        """
        Инициализация базы данных.
        
        Args:
            db_path: Путь к SQLite файлу (если используется SQLite)
            db_url: PostgreSQL connection string (если используется PostgreSQL)
        """
        self.use_postgresql = USE_POSTGRESQL and POSTGRESQL_AVAILABLE
        self.db_path = db_path or config.DATABASE_PATH
        self.db_url = db_url or config.DATABASE_URL
        
        if self.use_postgresql:
            logger.info("Используется PostgreSQL")
            # Создаем connection pool для PostgreSQL
            try:
                self.pool = psycopg2.pool.SimpleConnectionPool(
                    1, 10, self.db_url
                )
                if not self.pool:
                    raise Exception("Не удалось создать connection pool для PostgreSQL")
            except Exception as e:
                logger.error(f"Ошибка подключения к PostgreSQL: {e}")
                logger.warning("Переключаюсь на SQLite fallback")
                self.use_postgresql = False
                self.pool = None
        else:
            logger.info("Используется SQLite")
            self.pool = None
        
        self.init_db()
    
    def get_connection(self):
        """Получить соединение с БД."""
        if self.use_postgresql and self.pool:
            return self.pool.getconn()
        else:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn
    
    def return_connection(self, conn):
        """Вернуть соединение в pool (для PostgreSQL)."""
        if self.use_postgresql and self.pool:
            self.pool.putconn(conn)
        else:
            conn.close()
    
    def _execute(self, cursor, query, params=None):
        """Выполнить запрос с правильными параметрами для БД."""
        if self.use_postgresql:
            # PostgreSQL использует %s
            if params:
                cursor.execute(query.replace('?', '%s'), params)
            else:
                cursor.execute(query.replace('?', '%s'))
        else:
            # SQLite использует ?
            cursor.execute(query, params or [])
    
    def init_db(self):
        """Инициализировать структуру БД."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            if self.use_postgresql:
                # PostgreSQL схемы
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        user_id BIGINT PRIMARY KEY,
                        timezone TEXT DEFAULT 'Europe/Moscow',
                        locale TEXT DEFAULT 'ru_RU',
                        notifications_enabled BOOLEAN DEFAULT TRUE,
                        default_reminder_minutes INTEGER DEFAULT 15,
                        morning_digest_time TEXT DEFAULT '09:00',
                        web_notifications_enabled BOOLEAN DEFAULT TRUE,
                        interpretation_mode TEXT DEFAULT 'soft',
                        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Добавляем новые колонки, если их еще нет (для существующих БД)
                try:
                    cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS notifications_enabled BOOLEAN DEFAULT TRUE")
                except:
                    pass  # Колонка уже существует
                
                try:
                    cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS default_reminder_minutes INTEGER DEFAULT 15")
                except:
                    pass  # Колонка уже существует
                
                try:
                    cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS morning_digest_time TEXT DEFAULT '09:00'")
                except:
                    pass  # Колонка уже существует
                
                try:
                    cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS web_notifications_enabled BOOLEAN DEFAULT TRUE")
                except:
                    pass  # Колонка уже существует
                
                try:
                    cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS interpretation_mode TEXT DEFAULT 'soft'")
                except:
                    pass  # Колонка уже существует

                # Обновляем тип колонки created_at
                try:
                    cursor.execute("ALTER TABLE users ALTER COLUMN created_at TYPE TIMESTAMPTZ")
                except:
                    pass
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS calendar_connections (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        provider TEXT NOT NULL,
                        calendar_id TEXT NOT NULL,
                        credentials TEXT,
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(user_id),
                        UNIQUE(user_id, provider, calendar_id)
                    )
                """)
                
                try:
                    cursor.execute("ALTER TABLE calendar_connections ALTER COLUMN created_at TYPE TIMESTAMPTZ")
                except:
                    pass
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS events (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        external_id TEXT,
                        provider TEXT,
                        title TEXT NOT NULL,
                        description TEXT,
                        start_time TIMESTAMPTZ,
                        end_time TIMESTAMPTZ,
                        location TEXT,
                        status TEXT DEFAULT 'confirmed',
                        priority INTEGER DEFAULT 0,
                        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(user_id)
                    )
                """)
                
                # Обновляем типы колонок для существующих таблиц в PostgreSQL
                try:
                    cursor.execute("ALTER TABLE events ALTER COLUMN start_time TYPE TIMESTAMPTZ")
                    cursor.execute("ALTER TABLE events ALTER COLUMN end_time TYPE TIMESTAMPTZ")
                    cursor.execute("ALTER TABLE events ALTER COLUMN created_at TYPE TIMESTAMPTZ")
                    cursor.execute("ALTER TABLE events ALTER COLUMN updated_at TYPE TIMESTAMPTZ")
                except:
                    pass
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS notes (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        content TEXT NOT NULL,
                        context TEXT,
                        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(user_id)
                    )
                """)
                
                try:
                    cursor.execute("ALTER TABLE notes ALTER COLUMN created_at TYPE TIMESTAMPTZ")
                except:
                    pass
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_last_event (
                        user_id BIGINT PRIMARY KEY,
                        event_id INTEGER NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(user_id),
                        FOREIGN KEY (event_id) REFERENCES events(id)
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS reminders (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        event_id INTEGER NOT NULL,
                        reminder_time TIMESTAMPTZ NOT NULL,
                        event_start_time TIMESTAMPTZ NOT NULL,
                        reminder_type TEXT DEFAULT 'before',
                        minutes_before INTEGER,
                        sent BOOLEAN DEFAULT FALSE,
                        sent_at TIMESTAMPTZ,
                        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(user_id),
                        FOREIGN KEY (event_id) REFERENCES events(id)
                    )
                """)
                
                try:
                    cursor.execute("ALTER TABLE reminders ALTER COLUMN reminder_time TYPE TIMESTAMPTZ")
                    cursor.execute("ALTER TABLE reminders ALTER COLUMN event_start_time TYPE TIMESTAMPTZ")
                    cursor.execute("ALTER TABLE reminders ALTER COLUMN sent_at TYPE TIMESTAMPTZ")
                    cursor.execute("ALTER TABLE reminders ALTER COLUMN created_at TYPE TIMESTAMPTZ")
                except:
                    pass
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS meetings (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        title TEXT,
                        transcript TEXT,
                        raw_text TEXT,
                        summary TEXT,
                        summary_extended TEXT,
                        segments JSONB,
                        duration INTEGER DEFAULT 0,
                        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(user_id)
                    )
                """)
                
                try:
                    cursor.execute("ALTER TABLE meetings ALTER COLUMN created_at TYPE TIMESTAMPTZ")
                    cursor.execute("ALTER TABLE meetings ALTER COLUMN updated_at TYPE TIMESTAMPTZ")
                except:
                    pass
                
                # Индексы
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_user_id ON events(user_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_start_time ON events(start_time)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_external_id ON events(external_id, provider)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_notes_user_id ON notes(user_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_reminders_user_id ON reminders(user_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_reminders_reminder_time ON reminders(reminder_time)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_reminders_sent ON reminders(sent)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_meetings_user_id ON meetings(user_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_meetings_created_at ON meetings(created_at)")
                
            else:
                # SQLite схемы (оригинальные)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        timezone TEXT DEFAULT 'Europe/Moscow',
                        locale TEXT DEFAULT 'ru_RU',
                        notifications_enabled INTEGER DEFAULT 1,
                        default_reminder_minutes INTEGER DEFAULT 15,
                        morning_digest_time TEXT DEFAULT '09:00',
                        web_notifications_enabled INTEGER DEFAULT 1,
                        interpretation_mode TEXT DEFAULT 'soft',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Добавляем новые колонки, если их еще нет (для существующих БД)
                try:
                    cursor.execute("ALTER TABLE users ADD COLUMN notifications_enabled INTEGER DEFAULT 1")
                except:
                    pass  # Колонка уже существует
                
                try:
                    cursor.execute("ALTER TABLE users ADD COLUMN default_reminder_minutes INTEGER DEFAULT 15")
                except:
                    pass  # Колонка уже существует
                
                try:
                    cursor.execute("ALTER TABLE users ADD COLUMN morning_digest_time TEXT DEFAULT '09:00'")
                except:
                    pass  # Колонка уже существует
                
                try:
                    cursor.execute("ALTER TABLE users ADD COLUMN web_notifications_enabled INTEGER DEFAULT 1")
                except:
                    pass  # Колонка уже существует
                
                try:
                    cursor.execute("ALTER TABLE users ADD COLUMN interpretation_mode TEXT DEFAULT 'soft'")
                except:
                    pass  # Колонка уже существует
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS calendar_connections (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        provider TEXT NOT NULL,
                        calendar_id TEXT NOT NULL,
                        credentials TEXT,
                        is_active BOOLEAN DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(user_id),
                        UNIQUE(user_id, provider, calendar_id)
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        external_id TEXT,
                        provider TEXT,
                        title TEXT NOT NULL,
                        description TEXT,
                        start_time TIMESTAMP,
                        end_time TIMESTAMP,
                        location TEXT,
                        status TEXT DEFAULT 'confirmed',
                        priority INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(user_id)
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS notes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        content TEXT NOT NULL,
                        context TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(user_id)
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_last_event (
                        user_id INTEGER PRIMARY KEY,
                        event_id INTEGER NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(user_id),
                        FOREIGN KEY (event_id) REFERENCES events(id)
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS reminders (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        event_id INTEGER NOT NULL,
                        reminder_time TIMESTAMP NOT NULL,
                        event_start_time TIMESTAMP NOT NULL,
                        reminder_type TEXT DEFAULT 'before',
                        minutes_before INTEGER,
                        sent BOOLEAN DEFAULT 0,
                        sent_at TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(user_id),
                        FOREIGN KEY (event_id) REFERENCES events(id)
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS meetings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        title TEXT,
                        transcript TEXT,
                        raw_text TEXT,
                        summary TEXT,
                        summary_extended TEXT,
                        segments TEXT,
                        duration INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(user_id)
                    )
                """)
                
                # Индексы
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_user_id ON events(user_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_start_time ON events(start_time)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_external_id ON events(external_id, provider)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_notes_user_id ON notes(user_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_reminders_user_id ON reminders(user_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_reminders_reminder_time ON reminders(reminder_time)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_reminders_sent ON reminders(sent)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_meetings_user_id ON meetings(user_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_meetings_created_at ON meetings(created_at)")
            
            conn.commit()
        except Exception as e:
            logger.error(f"Ошибка инициализации БД: {e}", exc_info=True)
            conn.rollback()
            raise
        finally:
            self.return_connection(conn)
    
    def get_or_create_user(self, user_id: int) -> Dict:
        """Получить или создать пользователя."""
        conn = self.get_connection()
        
        try:
            if self.use_postgresql:
                from psycopg2.extras import RealDictCursor
                cursor = conn.cursor(cursor_factory=RealDictCursor)
            else:
                cursor = conn.cursor()
            
            try:
                if self.use_postgresql:
                    cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
                else:
                    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
                
                user = cursor.fetchone()
                
                if not user:
                    if self.use_postgresql:
                        cursor.execute("INSERT INTO users (user_id) VALUES (%s) ON CONFLICT (user_id) DO NOTHING", (user_id,))
                        cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
                    else:
                        cursor.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
                        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
                    user = cursor.fetchone()
                    conn.commit()
                
                # Для PostgreSQL RealDictCursor уже возвращает словарь
                if self.use_postgresql:
                    return dict(user) if user else None
                else:
                    return dict(user) if user else None
            finally:
                cursor.close()
        except Exception as e:
            logger.error(f"Ошибка get_or_create_user: {e}", exc_info=True)
            conn.rollback()
            return None
        finally:
            self.return_connection(conn)
    
    def get_user_settings(self, user_id: int) -> Dict:
        """Получить настройки пользователя."""
        user = self.get_or_create_user(user_id)
        if not user:
            return {
                'timezone': 'Europe/Moscow',
                'locale': 'ru_RU',
                'notifications_enabled': True,
                'default_reminder_minutes': 15,
                'morning_digest_time': '09:00',
                'web_notifications_enabled': True,
                'interpretation_mode': 'soft'
            }
        
        # Преобразуем в словарь с правильными типами
        settings = {
            'timezone': user.get('timezone', 'Europe/Moscow'),
            'locale': user.get('locale', 'ru_RU'),
            'notifications_enabled': bool(user.get('notifications_enabled', True)),
            'default_reminder_minutes': int(user.get('default_reminder_minutes', 15)),
            'morning_digest_time': user.get('morning_digest_time', '09:00'),
            'web_notifications_enabled': bool(user.get('web_notifications_enabled', True)),
            'interpretation_mode': user.get('interpretation_mode', 'soft')
        }
        
        # Для SQLite преобразуем boolean
        if not self.use_postgresql:
            if isinstance(user.get('notifications_enabled'), int):
                settings['notifications_enabled'] = bool(user.get('notifications_enabled', 1))
            if isinstance(user.get('web_notifications_enabled'), int):
                settings['web_notifications_enabled'] = bool(user.get('web_notifications_enabled', 1))
        
        return settings
    
    def update_user_settings(self, user_id: int, timezone: Optional[str] = None, locale: Optional[str] = None, settings_dict: Optional[Dict] = None):
        """Обновить настройки пользователя.
        
        Args:
            user_id: ID пользователя
            timezone: Часовой пояс (устаревший параметр, используйте settings_dict)
            locale: Локаль (устаревший параметр, используйте settings_dict)
            settings_dict: Словарь с настройками для обновления
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            updates = []
            params = []
            
            # Используем settings_dict если передан, иначе используем старые параметры
            if settings_dict:
                if 'timezone' in settings_dict:
                    updates.append("timezone = %s" if self.use_postgresql else "timezone = ?")
                    params.append(settings_dict['timezone'])
                
                if 'locale' in settings_dict:
                    updates.append("locale = %s" if self.use_postgresql else "locale = ?")
                    params.append(settings_dict['locale'])
                
                if 'notifications_enabled' in settings_dict:
                    value = settings_dict['notifications_enabled']
                    if self.use_postgresql:
                        updates.append("notifications_enabled = %s")
                        params.append(bool(value))
                    else:
                        updates.append("notifications_enabled = ?")
                        params.append(1 if bool(value) else 0)
                
                if 'default_reminder_minutes' in settings_dict:
                    updates.append("default_reminder_minutes = %s" if self.use_postgresql else "default_reminder_minutes = ?")
                    params.append(int(settings_dict['default_reminder_minutes']))
                
                if 'morning_digest_time' in settings_dict:
                    value = settings_dict['morning_digest_time']
                    if value is None or value == '':
                        # NULL означает дайджест выключен
                        if self.use_postgresql:
                            updates.append("morning_digest_time = NULL")
                        else:
                            updates.append("morning_digest_time = NULL")
                        # Не добавляем в params для NULL
                    else:
                        updates.append("morning_digest_time = %s" if self.use_postgresql else "morning_digest_time = ?")
                        params.append(str(value))
                
                if 'web_notifications_enabled' in settings_dict:
                    value = settings_dict['web_notifications_enabled']
                    if self.use_postgresql:
                        updates.append("web_notifications_enabled = %s")
                        params.append(bool(value))
                    else:
                        updates.append("web_notifications_enabled = ?")
                        params.append(1 if bool(value) else 0)
                
                if 'interpretation_mode' in settings_dict:
                    updates.append("interpretation_mode = %s" if self.use_postgresql else "interpretation_mode = ?")
                    params.append(str(settings_dict['interpretation_mode']))
            else:
                # Обратная совместимость со старым API
                if timezone:
                    updates.append("timezone = %s" if self.use_postgresql else "timezone = ?")
                    params.append(timezone)
                
                if locale:
                    updates.append("locale = %s" if self.use_postgresql else "locale = ?")
                    params.append(locale)
            
            if updates:
                params.append(user_id)
                if self.use_postgresql:
                    cursor.execute(f"UPDATE users SET {', '.join(updates)} WHERE user_id = %s", params)
                else:
                    cursor.execute(f"UPDATE users SET {', '.join(updates)} WHERE user_id = ?", params)
                conn.commit()
        except Exception as e:
            logger.error(f"Ошибка update_user_settings: {e}", exc_info=True)
            conn.rollback()
        finally:
            self.return_connection(conn)
    
    def save_calendar_connection(self, user_id: int, provider: str, calendar_id: str, credentials: str):
        """Сохранить подключение календаря."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            if self.use_postgresql:
                cursor.execute("""
                    INSERT INTO calendar_connections 
                    (user_id, provider, calendar_id, credentials, is_active)
                    VALUES (%s, %s, %s, %s, TRUE)
                    ON CONFLICT (user_id, provider, calendar_id) 
                    DO UPDATE SET credentials = EXCLUDED.credentials, is_active = TRUE
                """, (user_id, provider, calendar_id, credentials))
            else:
                cursor.execute("""
                    INSERT OR REPLACE INTO calendar_connections 
                    (user_id, provider, calendar_id, credentials, is_active)
                    VALUES (?, ?, ?, ?, 1)
                """, (user_id, provider, calendar_id, credentials))
            
            conn.commit()
        except Exception as e:
            logger.error(f"Ошибка save_calendar_connection: {e}", exc_info=True)
            conn.rollback()
        finally:
            self.return_connection(conn)
    
    def get_calendar_connections(self, user_id: int, active_only: bool = True) -> List[Dict]:
        """Получить подключения календарей пользователя."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            if self.use_postgresql:
                query = "SELECT * FROM calendar_connections WHERE user_id = %s"
                params = [user_id]
                if active_only:
                    query += " AND is_active = TRUE"
            else:
                query = "SELECT * FROM calendar_connections WHERE user_id = ?"
                params = [user_id]
                if active_only:
                    query += " AND is_active = 1"
            
            cursor.execute(query, params)
            
            if self.use_postgresql:
                # Используем RealDictCursor для PostgreSQL
                cursor.close()
                dict_cursor = conn.cursor(cursor_factory=RealDictCursor)
                dict_cursor.execute(query, params)
                connections = [dict(row) for row in dict_cursor.fetchall()]
                dict_cursor.close()
            else:
                connections = [dict(row) for row in cursor.fetchall()]
            
            return connections
        except Exception as e:
            logger.error(f"Ошибка get_calendar_connections: {e}", exc_info=True)
            return []
        finally:
            self.return_connection(conn)
    
    def deactivate_calendar_connection(self, user_id: int, provider: str, calendar_id: str):
        """Деактивировать подключение календаря."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            if self.use_postgresql:
                cursor.execute("""
                    UPDATE calendar_connections 
                    SET is_active = FALSE 
                    WHERE user_id = %s AND provider = %s AND calendar_id = %s
                """, (user_id, provider, calendar_id))
            else:
                cursor.execute("""
                    UPDATE calendar_connections 
                    SET is_active = 0 
                    WHERE user_id = ? AND provider = ? AND calendar_id = ?
                """, (user_id, provider, calendar_id))
            
            conn.commit()
        except Exception as e:
            logger.error(f"Ошибка deactivate_calendar_connection: {e}", exc_info=True)
            conn.rollback()
        finally:
            self.return_connection(conn)
    
    def save_event(self, user_id: int, title: str, description: Optional[str] = None,
                   start_time: Optional[datetime] = None, end_time: Optional[datetime] = None,
                   location: Optional[str] = None, status: str = "confirmed",
                   priority: int = 0, external_id: Optional[str] = None,
                   provider: Optional[str] = None) -> int:
        """Сохранить событие в БД."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            logger.info(f"💾 БД: Сохранение события для {user_id}: '{title}' на {start_time}")
            if self.use_postgresql:
                cursor.execute("""
                    INSERT INTO events 
                    (user_id, external_id, provider, title, description, start_time, end_time, 
                     location, status, priority)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (user_id, external_id, provider, title, description, 
                      start_time, end_time, location, status, priority))
                event_id = cursor.fetchone()[0]
            else:
                cursor.execute("""
                    INSERT INTO events 
                    (user_id, external_id, provider, title, description, start_time, end_time, 
                     location, status, priority)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (user_id, external_id, provider, title, description, 
                      start_time.isoformat() if start_time else None,
                      end_time.isoformat() if end_time else None,
                      location, status, priority))
                event_id = cursor.lastrowid
            
            conn.commit()
            return event_id
        except Exception as e:
            logger.error(f"Ошибка save_event: {e}", exc_info=True)
            conn.rollback()
            return 0
        finally:
            self.return_connection(conn)
    
    def update_event(self, event_id: int, **kwargs):
        """Обновить событие."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            updates = []
            params = []
            
            param_placeholder = "%s" if self.use_postgresql else "?"
            
            for key, value in kwargs.items():
                if key in ['title', 'description', 'location', 'status', 'priority', 'external_id', 'provider']:
                    updates.append(f"{key} = {param_placeholder}")
                    params.append(value)
                elif key in ['start_time', 'end_time']:
                    updates.append(f"{key} = {param_placeholder}")
                    if self.use_postgresql:
                        params.append(value)
                    else:
                        params.append(value.isoformat() if value else None)
            
            if updates:
                updates.append("updated_at = CURRENT_TIMESTAMP")
                params.append(event_id)
                
                if self.use_postgresql:
                    cursor.execute(f"UPDATE events SET {', '.join(updates)} WHERE id = %s", params)
                else:
                    cursor.execute(f"UPDATE events SET {', '.join(updates)} WHERE id = ?", params)
                conn.commit()
        except Exception as e:
            logger.error(f"Ошибка update_event: {e}", exc_info=True)
            conn.rollback()
        finally:
            self.return_connection(conn)
    
    def find_similar_events(self, user_id: int, title: str, start_time: Optional[datetime] = None,
                           days_window: int = 7) -> List[Dict]:
        """Найти похожие события для дедупликации."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            param_placeholder = "%s" if self.use_postgresql else "?"
            
            query = f"""
                SELECT * FROM events 
                WHERE user_id = {param_placeholder} AND title LIKE {param_placeholder}
            """
            params = [user_id, f"%{title[:20]}%"]
            
            if start_time:
                from datetime import timedelta
                time_min = start_time - timedelta(days=days_window)
                time_max = start_time + timedelta(days=days_window)
                query += f" AND start_time BETWEEN {param_placeholder} AND {param_placeholder}"
                if self.use_postgresql:
                    params.extend([time_min, time_max])
                else:
                    params.extend([time_min.isoformat(), time_max.isoformat()])
            
            query += f" ORDER BY start_time DESC LIMIT 10"
            
            cursor.execute(query, params)
            
            if self.use_postgresql:
                cursor.close()
                dict_cursor = conn.cursor(cursor_factory=RealDictCursor)
                dict_cursor.execute(query, params)
                events = [dict(row) for row in dict_cursor.fetchall()]
                dict_cursor.close()
            else:
                events = [dict(row) for row in cursor.fetchall()]
            
            return events
        except Exception as e:
            logger.error(f"Ошибка find_similar_events: {e}", exc_info=True)
            return []
        finally:
            self.return_connection(conn)
    
    def get_events(self, user_id: int, limit: int = 50, start_from: Optional[datetime] = None,
                   start_to: Optional[datetime] = None) -> List[Dict]:
        """Получить события пользователя в заданном диапазоне."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            param_placeholder = "%s" if self.use_postgresql else "?"
            
            query = f"SELECT * FROM events WHERE user_id = {param_placeholder}"
            params = [user_id]
            
            # Лог для отладки - сколько всего событий у пользователя
            cursor.execute(query, params)
            all_rows = cursor.fetchall()
            all_events_count = len(all_rows)
            logger.info(f"🔍 БД: Всего событий у пользователя {user_id} в базе: {all_events_count}")
            if all_events_count > 0:
                # В PostgreSQL cursor.fetchall() возвращает кортежи, если не RealDictCursor
                try:
                    if self.use_postgresql:
                        # Просто берем первый элемент кортежа, если знаем индекс, или не логируем title
                        logger.info(f"🔍 БД: Первые {min(all_events_count, 3)} событий найдены")
                    else:
                        logger.info(f"🔍 БД: Примеры событий: {[dict(r).get('title') for r in all_rows[:3]]}")
                except Exception as log_err:
                    logger.debug(f"Ошибка логирования примеров: {log_err}")
            
            if start_from:
                query += f" AND start_time >= {param_placeholder}"
                if self.use_postgresql:
                    params.append(start_from)
                else:
                    params.append(start_from.isoformat())
            
            if start_to:
                query += f" AND start_time <= {param_placeholder}"
                if self.use_postgresql:
                    params.append(start_to)
                else:
                    params.append(start_to.isoformat())
            
            query += f" ORDER BY start_time ASC LIMIT {param_placeholder}"
            params.append(limit)
            
            logger.debug(f"SQL Query: {query}")
            logger.debug(f"SQL Params: {params}")
            
            cursor.execute(query, params)
            
            if self.use_postgresql:
                cursor.close()
                dict_cursor = conn.cursor(cursor_factory=RealDictCursor)
                dict_cursor.execute(query, params)
                rows = dict_cursor.fetchall()
                dict_cursor.close()
            else:
                rows = cursor.fetchall()
            
            # Парсим события из БД
            events = []
            for row in rows:
                event_dict = dict(row)
                # Парсим даты из строк в datetime
                if event_dict.get('start_time'):
                    try:
                        if isinstance(event_dict['start_time'], str):
                            event_dict['start_time'] = datetime.fromisoformat(event_dict['start_time'].replace('Z', '+00:00'))
                    except:
                        pass
                if event_dict.get('end_time'):
                    try:
                        if isinstance(event_dict['end_time'], str):
                            event_dict['end_time'] = datetime.fromisoformat(event_dict['end_time'].replace('Z', '+00:00'))
                    except:
                        pass
                events.append(event_dict)
            
            return events
        except Exception as e:
            logger.error(f"Ошибка get_events: {e}", exc_info=True)
            return []
        finally:
            self.return_connection(conn)
    
    def delete_event(self, event_id: int, user_id: int) -> bool:
        """Удалить событие."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            if self.use_postgresql:
                cursor.execute("DELETE FROM events WHERE id = %s AND user_id = %s", (event_id, user_id))
            else:
                cursor.execute("DELETE FROM events WHERE id = ? AND user_id = ?", (event_id, user_id))
            
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted
        except Exception as e:
            logger.error(f"Ошибка delete_event: {e}", exc_info=True)
            conn.rollback()
            return False
        finally:
            self.return_connection(conn)
    
    def delete_all_events(self, user_id: int) -> Tuple[int, List[Dict]]:
        """Удалить все события пользователя. Возвращает (количество, список событий)."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            param_placeholder = "%s" if self.use_postgresql else "?"
            
            # Получаем список событий перед удалением
            cursor.execute(f"SELECT id, external_id, provider FROM events WHERE user_id = {param_placeholder}", (user_id,))
            
            if self.use_postgresql:
                cursor.close()
                dict_cursor = conn.cursor(cursor_factory=RealDictCursor)
                dict_cursor.execute(f"SELECT id, external_id, provider FROM events WHERE user_id = %s", (user_id,))
                events = dict_cursor.fetchall()
                events_list = [dict(e) for e in events]
                dict_cursor.close()
            else:
                events = cursor.fetchall()
                events_list = [dict(e) for e in events]
            
            cursor.execute(f"DELETE FROM events WHERE user_id = {param_placeholder}", (user_id,))
            deleted_count = cursor.rowcount
            conn.commit()
            
            return deleted_count, events_list
        except Exception as e:
            logger.error(f"Ошибка delete_all_events: {e}", exc_info=True)
            conn.rollback()
            return 0, []
        finally:
            self.return_connection(conn)
    
    def delete_events_by_period(self, user_id: int, start_from: Optional[datetime] = None,
                                start_to: Optional[datetime] = None) -> tuple:
        """Удалить события за период. Возвращает (количество, список удаленных событий)."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            param_placeholder = "%s" if self.use_postgresql else "?"
            
            query = f"SELECT id, external_id, provider, title FROM events WHERE user_id = {param_placeholder}"
            params = [user_id]
            
            if start_from:
                query += f" AND start_time >= {param_placeholder}"
                if self.use_postgresql:
                    params.append(start_from)
                else:
                    params.append(start_from.isoformat())
            
            if start_to:
                query += f" AND start_time <= {param_placeholder}"
                if self.use_postgresql:
                    params.append(start_to)
                else:
                    params.append(start_to.isoformat())
            
            cursor.execute(query, params)
            
            if self.use_postgresql:
                cursor.close()
                dict_cursor = conn.cursor(cursor_factory=RealDictCursor)
                dict_cursor.execute(query, params)
                events = dict_cursor.fetchall()
                events_list = [dict(e) for e in events]
                dict_cursor.close()
            else:
                events = cursor.fetchall()
                events_list = [dict(e) for e in events]
            
            delete_query = f"DELETE FROM events WHERE user_id = {param_placeholder}"
            delete_params = [user_id]
            
            if start_from:
                delete_query += f" AND start_time >= {param_placeholder}"
                if self.use_postgresql:
                    delete_params.append(start_from)
                else:
                    delete_params.append(start_from.isoformat())
            
            if start_to:
                delete_query += f" AND start_time <= {param_placeholder}"
                if self.use_postgresql:
                    delete_params.append(start_to)
                else:
                    delete_params.append(start_to.isoformat())
            
            cursor.execute(delete_query, delete_params)
            deleted_count = cursor.rowcount
            conn.commit()
            
            return deleted_count, events_list
        except Exception as e:
            logger.error(f"Ошибка delete_events_by_period: {e}", exc_info=True)
            conn.rollback()
            return 0, []
        finally:
            self.return_connection(conn)
    
    def delete_events_by_pattern(self, user_id: int, pattern: str) -> tuple:
        """Удалить события по паттерну в названии. Возвращает (количество, список событий)."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            param_placeholder = "%s" if self.use_postgresql else "?"
            
            query = f"SELECT id, external_id, provider, title FROM events WHERE user_id = {param_placeholder} AND (title LIKE {param_placeholder} OR description LIKE {param_placeholder})"
            params = (user_id, f"%{pattern}%", f"%{pattern}%")
            
            cursor.execute(query, params)
            
            if self.use_postgresql:
                cursor.close()
                dict_cursor = conn.cursor(cursor_factory=RealDictCursor)
                dict_cursor.execute(query, params)
                events = dict_cursor.fetchall()
                events_list = [dict(e) for e in events]
                dict_cursor.close()
            else:
                events = cursor.fetchall()
                events_list = [dict(e) for e in events]
            
            cursor.execute(query, params)
            
            if self.use_postgresql:
                cursor.close()
                dict_cursor = conn.cursor(cursor_factory=RealDictCursor)
                dict_cursor.execute(query, params)
                events = dict_cursor.fetchall()
                events_list = [dict(e) for e in events]
                dict_cursor.close()
            else:
                events = cursor.fetchall()
                events_list = [dict(e) for e in events]
            
            delete_query = f"DELETE FROM events WHERE user_id = {param_placeholder} AND (title LIKE {param_placeholder} OR description LIKE {param_placeholder})"
            cursor.execute(delete_query, params)
            deleted_count = cursor.rowcount
            conn.commit()
            
            return deleted_count, events_list
        except Exception as e:
            logger.error(f"Ошибка delete_events_by_pattern: {e}", exc_info=True)
            conn.rollback()
            return 0, []
        finally:
            self.return_connection(conn)
    
    def delete_events_by_ids(self, user_id: int, event_ids: List[int]) -> tuple:
        """Удалить события по списку ID. Возвращает (количество, список событий)."""
        if not event_ids:
            return 0, []
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            param_placeholder = "%s" if self.use_postgresql else "?"
            placeholders = ','.join([param_placeholder] * len(event_ids))
            
            query = f"SELECT id, external_id, provider FROM events WHERE user_id = {param_placeholder} AND id IN ({placeholders})"
            params = [user_id] + event_ids
            
            cursor.execute(query, params)
            
            if self.use_postgresql:
                cursor.close()
                dict_cursor = conn.cursor(cursor_factory=RealDictCursor)
                dict_cursor.execute(query, params)
                events = dict_cursor.fetchall()
                events_list = [dict(e) for e in events]
                dict_cursor.close()
            else:
                events = cursor.fetchall()
                events_list = [dict(e) for e in events]
            
            delete_query = f"DELETE FROM events WHERE user_id = {param_placeholder} AND id IN ({placeholders})"
            cursor.execute(delete_query, params)
            deleted_count = cursor.rowcount
            conn.commit()
            
            return deleted_count, events_list
        except Exception as e:
            logger.error(f"Ошибка delete_events_by_ids: {e}", exc_info=True)
            conn.rollback()
            return 0, []
        finally:
            self.return_connection(conn)
    
    def save_note(self, user_id: int, content: str, context: Optional[Dict] = None) -> int:
        """Сохранить заметку."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            context_json = json.dumps(context, ensure_ascii=False) if context else None
            
            if self.use_postgresql:
                cursor.execute("""
                    INSERT INTO notes (user_id, content, context)
                    VALUES (%s, %s, %s)
                    RETURNING id
                """, (user_id, content, context_json))
                note_id = cursor.fetchone()[0]
            else:
                cursor.execute("""
                    INSERT INTO notes (user_id, content, context)
                    VALUES (?, ?, ?)
                """, (user_id, content, context_json))
                note_id = cursor.lastrowid
            
            conn.commit()
            return note_id
        except Exception as e:
            logger.error(f"Ошибка save_note: {e}", exc_info=True)
            conn.rollback()
            return 0
        finally:
            self.return_connection(conn)
    
    def get_notes(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Получить заметки пользователя."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            param_placeholder = "%s" if self.use_postgresql else "?"
            
            query = f"""
                SELECT * FROM notes 
                WHERE user_id = {param_placeholder} 
                ORDER BY created_at DESC 
                LIMIT {param_placeholder}
            """
            
            cursor.execute(query, (user_id, limit))
            
            if self.use_postgresql:
                cursor.close()
                dict_cursor = conn.cursor(cursor_factory=RealDictCursor)
                dict_cursor.execute(query, (user_id, limit))
                notes = [dict(row) for row in dict_cursor.fetchall()]
                dict_cursor.close()
            else:
                notes = [dict(row) for row in cursor.fetchall()]
            
            return notes
        except Exception as e:
            logger.error(f"Ошибка get_notes: {e}", exc_info=True)
            return []
        finally:
            self.return_connection(conn)
    
    def delete_note(self, note_id: int, user_id: int) -> bool:
        """Удалить заметку."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            if self.use_postgresql:
                cursor.execute("DELETE FROM notes WHERE id = %s AND user_id = %s", (note_id, user_id))
            else:
                cursor.execute("DELETE FROM notes WHERE id = ? AND user_id = ?", (note_id, user_id))
            
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted
        except Exception as e:
            logger.error(f"Ошибка delete_note: {e}", exc_info=True)
            conn.rollback()
            return False
        finally:
            self.return_connection(conn)
    
    def delete_all_notes(self, user_id: int) -> int:
        """Удалить все заметки пользователя. Возвращает количество удаленных."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            param_placeholder = "%s" if self.use_postgresql else "?"
            
            cursor.execute(f"DELETE FROM notes WHERE user_id = {param_placeholder}", (user_id,))
            deleted_count = cursor.rowcount
            conn.commit()
            return deleted_count
        except Exception as e:
            logger.error(f"Ошибка delete_all_notes: {e}", exc_info=True)
            conn.rollback()
            return 0
        finally:
            self.return_connection(conn)
    
    def save_reminder(self, user_id: int, event_id: int, reminder_time: datetime, 
                     event_start_time: datetime, reminder_type: str = 'before', 
                     minutes_before: Optional[int] = None) -> int:
        """Сохранить напоминание о событии."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            if self.use_postgresql:
                cursor.execute("""
                    INSERT INTO reminders (user_id, event_id, reminder_time, event_start_time, 
                                         reminder_type, minutes_before)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (user_id, event_id, reminder_time, event_start_time, 
                      reminder_type, minutes_before))
                reminder_id = cursor.fetchone()[0]
            else:
                cursor.execute("""
                    INSERT INTO reminders (user_id, event_id, reminder_time, event_start_time, 
                                         reminder_type, minutes_before)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (user_id, event_id, reminder_time.isoformat(), event_start_time.isoformat(), 
                      reminder_type, minutes_before))
                reminder_id = cursor.lastrowid
            
            conn.commit()
            return reminder_id
        except Exception as e:
            logger.error(f"Ошибка save_reminder: {e}", exc_info=True)
            conn.rollback()
            return 0
        finally:
            self.return_connection(conn)
    
    def get_pending_reminders(self, current_time: datetime) -> List[Dict]:
        """Получить напоминания, которые нужно отправить сейчас."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            if self.use_postgresql:
                cursor.execute("""
                    SELECT r.*, e.title, e.description, e.location, e.start_time, e.end_time
                    FROM reminders r
                    JOIN events e ON r.event_id = e.id
                    WHERE r.sent = FALSE
                    ORDER BY r.reminder_time ASC
                """)
            else:
                cursor.execute("""
                    SELECT r.*, e.title, e.description, e.location, e.start_time, e.end_time
                    FROM reminders r
                    JOIN events e ON r.event_id = e.id
                    WHERE r.sent = 0
                    ORDER BY r.reminder_time ASC
                """)
            
            # Получаем названия колонок
            if self.use_postgresql:
                cursor.close()
                dict_cursor = conn.cursor(cursor_factory=RealDictCursor)
                dict_cursor.execute("""
                    SELECT r.*, e.title, e.description, e.location, e.start_time, e.end_time
                    FROM reminders r
                    JOIN events e ON r.event_id = e.id
                    WHERE r.sent = FALSE
                    ORDER BY r.reminder_time ASC
                """)
                rows = dict_cursor.fetchall()
                dict_cursor.close()
            else:
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
            
            # Преобразуем в словари и фильтруем по времени
            reminders = []
            current_time_utc = current_time if current_time.tzinfo == pytz.UTC else current_time.astimezone(pytz.UTC)
            
            for row in rows:
                if self.use_postgresql:
                    reminder_dict = dict(row)
                else:
                    reminder_dict = dict(zip(columns, row))
                
                reminder_time_str = reminder_dict.get('reminder_time')
                
                if not reminder_time_str:
                    continue
                
                try:
                    # Парсим время напоминания с учетом часового пояса
                    reminder_time = None
                    if isinstance(reminder_time_str, str):
                        # Парсим ISO формат времени
                        try:
                            if 'Z' in reminder_time_str:
                                reminder_time_clean = reminder_time_str.replace('Z', '+00:00')
                            else:
                                reminder_time_clean = reminder_time_str
                            
                            reminder_time = datetime.fromisoformat(reminder_time_clean)
                            
                            # Конвертируем в UTC для сравнения
                            if reminder_time.tzinfo is None:
                                reminder_time = pytz.UTC.localize(reminder_time)
                            else:
                                reminder_time = reminder_time.astimezone(pytz.UTC)
                                
                        except (ValueError, AttributeError) as e:
                            logger.warning(f"Не удалось распарсить время напоминания {reminder_dict.get('id')}: {reminder_time_str}, ошибка: {e}")
                            continue
                    else:
                        # Если уже datetime объект
                        reminder_time = reminder_time_str
                        if reminder_time.tzinfo is None:
                            reminder_time = pytz.UTC.localize(reminder_time)
                        elif reminder_time.tzinfo != pytz.UTC:
                            reminder_time = reminder_time.astimezone(pytz.UTC)
                    
                    # Сравниваем в UTC
                    if reminder_time and reminder_time <= current_time_utc:
                        reminders.append(reminder_dict)
                        
                except Exception as e:
                    logger.warning(f"Ошибка парсинга времени напоминания {reminder_dict.get('id')}: {e}, время: {reminder_time_str}")
                    continue
            
            return reminders
        except Exception as e:
            logger.error(f"Ошибка get_pending_reminders: {e}", exc_info=True)
            return []
        finally:
            self.return_connection(conn)
    
    def mark_reminder_sent(self, reminder_id: int):
        """Пометить напоминание как отправленное."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            from datetime import datetime
            now = datetime.now()
            
            if self.use_postgresql:
                cursor.execute("""
                    UPDATE reminders 
                    SET sent = TRUE, sent_at = %s
                    WHERE id = %s
                """, (now, reminder_id))
            else:
                cursor.execute("""
                    UPDATE reminders 
                    SET sent = 1, sent_at = ?
                    WHERE id = ?
                """, (now.isoformat(), reminder_id))
            
            conn.commit()
        except Exception as e:
            logger.error(f"Ошибка mark_reminder_sent: {e}", exc_info=True)
            conn.rollback()
        finally:
            self.return_connection(conn)
    
    def get_reminders_for_event(self, event_id: int) -> List[Dict]:
        """Получить все напоминания для события."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            param_placeholder = "%s" if self.use_postgresql else "?"
            
            cursor.execute(f"SELECT * FROM reminders WHERE event_id = {param_placeholder}", (event_id,))
            
            if self.use_postgresql:
                cursor.close()
                dict_cursor = conn.cursor(cursor_factory=RealDictCursor)
                dict_cursor.execute("SELECT * FROM reminders WHERE event_id = %s", (event_id,))
                reminders = [dict(row) for row in dict_cursor.fetchall()]
                dict_cursor.close()
            else:
                reminders = [dict(row) for row in cursor.fetchall()]
            
            return reminders
        except Exception as e:
            logger.error(f"Ошибка get_reminders_for_event: {e}", exc_info=True)
            return []
        finally:
            self.return_connection(conn)
    
    def delete_reminders_for_event(self, event_id: int):
        """Удалить все напоминания для события."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            param_placeholder = "%s" if self.use_postgresql else "?"
            
            cursor.execute(f"DELETE FROM reminders WHERE event_id = {param_placeholder}", (event_id,))
            conn.commit()
        except Exception as e:
            logger.error(f"Ошибка delete_reminders_for_event: {e}", exc_info=True)
            conn.rollback()
        finally:
            self.return_connection(conn)
    
    def get_last_event(self, user_id: int) -> Optional[Dict]:
        """Получить последнее событие пользователя из контекста."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            param_placeholder = "%s" if self.use_postgresql else "?"
            
            query = f"""
                SELECT e.* FROM events e
                INNER JOIN user_last_event ule ON e.id = ule.event_id
                WHERE ule.user_id = {param_placeholder}
                ORDER BY ule.updated_at DESC
                LIMIT 1
            """
            
            cursor.execute(query, (user_id,))
            
            if self.use_postgresql:
                cursor.close()
                dict_cursor = conn.cursor(cursor_factory=RealDictCursor)
                dict_cursor.execute(query, (user_id,))
                row = dict_cursor.fetchone()
                dict_cursor.close()
            else:
                row = cursor.fetchone()
            
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"Ошибка get_last_event: {e}", exc_info=True)
            return None
        finally:
            self.return_connection(conn)
    
    def update_last_event_context(self, user_id: int, event_id: int):
        """Обновить контекст последнего события пользователя."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            if self.use_postgresql:
                cursor.execute("""
                    INSERT INTO user_last_event (user_id, event_id, updated_at)
                    VALUES (%s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (user_id) DO UPDATE SET event_id = EXCLUDED.event_id, updated_at = CURRENT_TIMESTAMP
                """, (user_id, event_id))
            else:
                cursor.execute("""
                    INSERT OR REPLACE INTO user_last_event (user_id, event_id, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                """, (user_id, event_id))
            
            conn.commit()
        except Exception as e:
            logger.error(f"Ошибка update_last_event_context: {e}", exc_info=True)
            conn.rollback()
        finally:
            self.return_connection(conn)
    
    def save_meeting(self, user_id: int, title: Optional[str], transcript: Optional[str], 
                     raw_text: Optional[str], summary: Optional[str], summary_extended: Optional[str] = None,
                     segments: Optional[List] = None, duration: int = 0) -> Optional[int]:
        """Сохранить встречу в БД."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            import json
            segments_json = json.dumps(segments) if segments else None
            
            if self.use_postgresql:
                cursor.execute("""
                    INSERT INTO meetings (user_id, title, transcript, raw_text, summary, summary_extended, segments, duration, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    RETURNING id
                """, (user_id, title, transcript, raw_text, summary, summary_extended, segments_json, duration))
                meeting_id = cursor.fetchone()[0]
            else:
                cursor.execute("""
                    INSERT INTO meetings (user_id, title, transcript, raw_text, summary, summary_extended, segments, duration, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """, (user_id, title, transcript, raw_text, summary, summary_extended, segments_json, duration))
                meeting_id = cursor.lastrowid
            
            conn.commit()
            logger.info(f"Встреча сохранена: id={meeting_id}, user_id={user_id}")
            return meeting_id
        except Exception as e:
            logger.error(f"Ошибка сохранения встречи: {e}", exc_info=True)
            conn.rollback()
            return None
        finally:
            self.return_connection(conn)
    
    def get_meetings(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Получить список встреч пользователя."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            if self.use_postgresql:
                cursor.execute("""
                    SELECT id, title, transcript, raw_text, summary, summary_extended, segments, duration, created_at, updated_at
                    FROM meetings
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                """, (user_id, limit))
            else:
                cursor.execute("""
                    SELECT id, title, transcript, raw_text, summary, summary_extended, segments, duration, created_at, updated_at
                    FROM meetings
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (user_id, limit))
            
            meetings = []
            for row in cursor.fetchall():
                meeting = dict(row) if self.use_postgresql else dict(row)
                # Парсим segments если это JSON
                if meeting.get('segments') and isinstance(meeting['segments'], str):
                    try:
                        import json
                        meeting['segments'] = json.loads(meeting['segments'])
                    except:
                        meeting['segments'] = []
                meetings.append(meeting)
            
            return meetings
        except Exception as e:
            logger.error(f"Ошибка получения встреч: {e}", exc_info=True)
            return []
        finally:
            self.return_connection(conn)
    
    def get_meeting(self, meeting_id: int, user_id: int) -> Optional[Dict]:
        """Получить конкретную встречу."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            if self.use_postgresql:
                cursor.execute("""
                    SELECT id, title, transcript, raw_text, summary, summary_extended, segments, duration, created_at, updated_at
                    FROM meetings
                    WHERE id = %s AND user_id = %s
                """, (meeting_id, user_id))
            else:
                cursor.execute("""
                    SELECT id, title, transcript, raw_text, summary, summary_extended, segments, duration, created_at, updated_at
                    FROM meetings
                    WHERE id = ? AND user_id = ?
                """, (meeting_id, user_id))
            
            row = cursor.fetchone()
            if row:
                meeting = dict(row) if self.use_postgresql else dict(row)
                # Парсим segments если это JSON
                if meeting.get('segments') and isinstance(meeting['segments'], str):
                    try:
                        import json
                        meeting['segments'] = json.loads(meeting['segments'])
                    except:
                        meeting['segments'] = []
                return meeting
            return None
        except Exception as e:
            logger.error(f"Ошибка получения встречи: {e}", exc_info=True)
            return None
        finally:
            self.return_connection(conn)
    
    def delete_meeting(self, meeting_id: int, user_id: int) -> bool:
        """Удалить встречу."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            if self.use_postgresql:
                cursor.execute("DELETE FROM meetings WHERE id = %s AND user_id = %s", (meeting_id, user_id))
            else:
                cursor.execute("DELETE FROM meetings WHERE id = ? AND user_id = ?", (meeting_id, user_id))
            
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted
        except Exception as e:
            logger.error(f"Ошибка удаления встречи: {e}", exc_info=True)
            conn.rollback()
            return False
        finally:
            self.return_connection(conn)
