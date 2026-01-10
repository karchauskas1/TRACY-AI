#!/usr/bin/env python3
"""
Скрипт для миграции данных из SQLite в PostgreSQL.

Использование:
1. Убедитесь, что PostgreSQL запущен и DATABASE_URL указан в .env
2. Запустите: python migrate_to_postgresql.py

Скрипт:
- Подключится к SQLite БД
- Подключится к PostgreSQL БД
- Скопирует все данные из SQLite в PostgreSQL
- Сохранит резервную копию SQLite БД
"""

import os
import sys
import json
import sqlite3
from datetime import datetime
import pytz

# Проверяем наличие psycopg2
try:
    import psycopg2
    from psycopg2.extras import execute_values
    POSTGRESQL_AVAILABLE = True
except ImportError:
    print("❌ psycopg2 не установлен. Установите: pip install psycopg2-binary")
    sys.exit(1)

# Загружаем конфигурацию
from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
DATABASE_PATH = os.getenv("DATABASE_PATH", "./data/tracy.db")

if not DATABASE_URL:
    print("❌ DATABASE_URL не указан в .env")
    print("Укажите DATABASE_URL в формате: postgresql://user:password@host:port/dbname")
    sys.exit(1)

if not os.path.exists(DATABASE_PATH):
    print(f"❌ SQLite файл не найден: {DATABASE_PATH}")
    sys.exit(1)

print("🔄 Начинаю миграцию данных из SQLite в PostgreSQL...")
print(f"📁 SQLite: {DATABASE_PATH}")
print(f"🐘 PostgreSQL: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else DATABASE_URL}")

# Подключаемся к SQLite
try:
    sqlite_conn = sqlite3.connect(DATABASE_PATH)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cursor = sqlite_conn.cursor()
    print("✅ Подключено к SQLite")
except Exception as e:
    print(f"❌ Ошибка подключения к SQLite: {e}")
    sys.exit(1)

# Подключаемся к PostgreSQL
try:
    pg_conn = psycopg2.connect(DATABASE_URL)
    pg_cursor = pg_conn.cursor()
    print("✅ Подключено к PostgreSQL")
except Exception as e:
    print(f"❌ Ошибка подключения к PostgreSQL: {e}")
    sqlite_conn.close()
    sys.exit(1)

try:
    # Мигрируем пользователей
    print("\n📦 Миграция пользователей...")
    sqlite_cursor.execute("SELECT * FROM users")
    users = sqlite_cursor.fetchall()
    
    for user in users:
        pg_cursor.execute("""
            INSERT INTO users (user_id, timezone, locale, created_at)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (user_id) DO NOTHING
        """, (user['user_id'], user['timezone'], user['locale'], user['created_at']))
    
    print(f"✅ Мигрировано пользователей: {len(users)}")
    
    # Мигрируем календарные подключения
    print("\n📦 Миграция календарных подключений...")
    sqlite_cursor.execute("SELECT * FROM calendar_connections")
    connections = sqlite_cursor.fetchall()
    
    for conn in connections:
        pg_cursor.execute("""
            INSERT INTO calendar_connections 
            (user_id, provider, calendar_id, credentials, is_active, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id, provider, calendar_id) DO NOTHING
        """, (conn['user_id'], conn['provider'], conn['calendar_id'], 
              conn['credentials'], bool(conn['is_active']), conn['created_at']))
    
    print(f"✅ Мигрировано подключений: {len(connections)}")
    
    # Мигрируем события
    print("\n📦 Миграция событий...")
    sqlite_cursor.execute("SELECT * FROM events")
    events = sqlite_cursor.fetchall()
    
    for event in events:
        pg_cursor.execute("""
            INSERT INTO events 
            (id, user_id, external_id, provider, title, description, start_time, 
             end_time, location, status, priority, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        """, (event['id'], event['user_id'], event['external_id'], event['provider'],
              event['title'], event['description'], event['start_time'], event['end_time'],
              event['location'], event['status'], event['priority'], 
              event['created_at'], event['updated_at']))
    
    print(f"✅ Мигрировано событий: {len(events)}")
    
    # Мигрируем заметки
    print("\n📦 Миграция заметок...")
    sqlite_cursor.execute("SELECT * FROM notes")
    notes = sqlite_cursor.fetchall()
    
    for note in notes:
        pg_cursor.execute("""
            INSERT INTO notes (id, user_id, content, context, created_at)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        """, (note['id'], note['user_id'], note['content'], 
              note['context'], note['created_at']))
    
    print(f"✅ Мигрировано заметок: {len(notes)}")
    
    # Мигрируем контекст последних событий
    print("\n📦 Миграция контекста последних событий...")
    sqlite_cursor.execute("SELECT * FROM user_last_event")
    last_events = sqlite_cursor.fetchall()
    
    for le in last_events:
        pg_cursor.execute("""
            INSERT INTO user_last_event (user_id, event_id, updated_at)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE SET event_id = EXCLUDED.event_id, updated_at = EXCLUDED.updated_at
        """, (le['user_id'], le['event_id'], le['updated_at']))
    
    print(f"✅ Мигрировано контекстов: {len(last_events)}")
    
    # Мигрируем напоминания
    print("\n📦 Миграция напоминаний...")
    sqlite_cursor.execute("SELECT * FROM reminders")
    reminders = sqlite_cursor.fetchall()
    
    for reminder in reminders:
        pg_cursor.execute("""
            INSERT INTO reminders 
            (id, user_id, event_id, reminder_time, event_start_time, reminder_type, 
             minutes_before, sent, sent_at, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        """, (reminder['id'], reminder['user_id'], reminder['event_id'],
              reminder['reminder_time'], reminder['event_start_time'], 
              reminder['reminder_type'], reminder['minutes_before'],
              bool(reminder['sent']), reminder['sent_at'], reminder['created_at']))
    
    print(f"✅ Мигрировано напоминаний: {len(reminders)}")
    
    # Коммитим изменения
    pg_conn.commit()
    print("\n✅ Миграция завершена успешно!")
    print(f"📊 Статистика:")
    print(f"   - Пользователи: {len(users)}")
    print(f"   - Подключения: {len(connections)}")
    print(f"   - События: {len(events)}")
    print(f"   - Заметки: {len(notes)}")
    print(f"   - Контексты: {len(last_events)}")
    print(f"   - Напоминания: {len(reminders)}")
    
    # Создаем резервную копию SQLite
    backup_path = f"{DATABASE_PATH}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    import shutil
    shutil.copy2(DATABASE_PATH, backup_path)
    print(f"\n💾 Создана резервная копия SQLite: {backup_path}")
    print("\n⚠️  ВАЖНО: После проверки работы с PostgreSQL можно удалить SQLite файл.")
    
except Exception as e:
    print(f"\n❌ Ошибка миграции: {e}")
    import traceback
    traceback.print_exc()
    pg_conn.rollback()
    sys.exit(1)
finally:
    sqlite_conn.close()
    pg_conn.close()
    print("\n✅ Соединения закрыты")


