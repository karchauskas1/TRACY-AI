#!/usr/bin/env python3
"""Скрипт для проверки напоминаний в базе данных."""
import sys
from datetime import datetime
import pytz
from database import Database

def check_reminders(user_id=None):
    """Проверить напоминания в базе данных."""
    db = Database()
    
    # Подключаемся к БД
    conn = db.get_connection()
    cursor = conn.cursor()
    
    if user_id:
        cursor.execute("""
            SELECT r.*, e.title, e.start_time
            FROM reminders r
            JOIN events e ON r.event_id = e.id
            WHERE r.user_id = ? AND r.sent = 0
            ORDER BY r.reminder_time ASC
        """, (user_id,))
    else:
        cursor.execute("""
            SELECT r.*, e.title, e.start_time
            FROM reminders r
            JOIN events e ON r.event_id = e.id
            WHERE r.sent = 0
            ORDER BY r.reminder_time ASC
        """)
    
    reminders = cursor.fetchall()
    conn.close()
    
    if not reminders:
        print("❌ Нет напоминаний в базе данных (все отправлены или напоминания не созданы)")
        return
    
    print(f"✓ Найдено {len(reminders)} напоминаний в базе данных:\n")
    
    current_time = datetime.now(pytz.UTC)
    
    for reminder_row in reminders:
        # Преобразуем sqlite3.Row в словарь
        reminder = dict(reminder_row)
        
        reminder_id = reminder['id']
        event_title = reminder.get('title', 'Без названия')
        reminder_time_str = reminder['reminder_time']
        event_start_time_str = reminder.get('start_time')
        reminder_type = reminder.get('reminder_type', 'before')
        minutes_before = reminder.get('minutes_before')
        
        try:
            # Парсим время напоминания
            if isinstance(reminder_time_str, str):
                reminder_time_clean = reminder_time_str.replace('Z', '+00:00')
                reminder_time = datetime.fromisoformat(reminder_time_clean)
                if reminder_time.tzinfo is None:
                    reminder_time = pytz.UTC.localize(reminder_time)
                elif reminder_time.tzinfo != pytz.UTC:
                    reminder_time = reminder_time.astimezone(pytz.UTC)
            else:
                reminder_time = reminder_time_str
            
            # Вычисляем разницу во времени
            time_diff = (reminder_time - current_time).total_seconds()
            
            if time_diff < 0:
                status = "⚠️ ПРОСРОЧЕНО"
                time_info = f"{-time_diff/60:.1f} минут назад"
            elif time_diff < 60:
                status = "⏰ СЕЙЧАС"
                time_info = f"через {time_diff:.0f} секунд"
            elif time_diff < 3600:
                status = "🔔 СКОРО"
                time_info = f"через {time_diff/60:.1f} минут"
            else:
                status = "📅 БУДУЩЕЕ"
                time_info = f"через {time_diff/3600:.1f} часов"
            
            print(f"{status} ID: {reminder_id}")
            print(f"   Событие: {event_title}")
            print(f"   Время напоминания: {reminder_time.isoformat()} ({time_info})")
            if event_start_time_str:
                try:
                    event_start = datetime.fromisoformat(str(event_start_time_str).replace('Z', '+00:00'))
                    print(f"   Время события: {event_start.isoformat()}")
                except:
                    print(f"   Время события: {event_start_time_str}")
            print(f"   Тип: {reminder_type} (за {minutes_before} минут до события)" if reminder_type == 'before' and minutes_before else f"   Тип: {reminder_type} (в момент начала)")
            print()
            
        except Exception as e:
            print(f"❌ Ошибка обработки напоминания {reminder_id}: {e}")
            print(f"   reminder_time: {reminder_time_str}")
            print()

if __name__ == "__main__":
    user_id = None
    if len(sys.argv) > 1:
        try:
            user_id = int(sys.argv[1])
        except ValueError:
            print(f"Использование: {sys.argv[0]} [user_id]")
            sys.exit(1)
    
    check_reminders(user_id)

