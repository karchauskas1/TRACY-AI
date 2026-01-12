#!/usr/bin/env python3
"""Тестовый скрипт для проверки системы напоминаний."""
import sys
import asyncio
from datetime import datetime
import pytz
from database import Database
from reminder_scheduler import ReminderScheduler
from telegram import Bot
import config

async def test_reminders():
    """Тестировать систему напоминаний."""
    print("🔍 Тестирование системы напоминаний...")
    
    # Инициализация
    db = Database()
    
    # Создаем временный бот (нужен только для инициализации)
    bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
    scheduler = ReminderScheduler(bot, db)
    
    # Проверяем напоминания в базе
    print("\n1. Проверка напоминаний в базе данных:")
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM reminders WHERE sent = 0")
    total = cursor.fetchone()[0]
    print(f"   Всего неотправленных напоминаний: {total}")
    conn.close()
    
    # Получаем текущее время
    current_time = datetime.now(pytz.UTC)
    print(f"\n2. Текущее время UTC: {current_time.isoformat()}")
    
    # Получаем напоминания для отправки
    print("\n3. Получение напоминаний для отправки:")
    pending = db.get_pending_reminders(current_time)
    print(f"   Найдено напоминаний: {len(pending)}")
    
    for reminder in pending:
        print(f"   - ID: {reminder['id']}, время: {reminder.get('reminder_time')}, событие: {reminder.get('title', 'N/A')}")
    
    # Проверяем планировщик
    print("\n4. Тест планировщика:")
    try:
        await scheduler.start()
        print("   ✅ Планировщик запущен")
        
        # Делаем одну проверку
        print("\n5. Выполнение проверки напоминаний:")
        await scheduler._check_and_send_reminders()
        print("   ✅ Проверка завершена")
        
        # Останавливаем
        await scheduler.stop()
        print("   ✅ Планировщик остановлен")
        
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n✅ Тестирование завершено")

if __name__ == "__main__":
    asyncio.run(test_reminders())




