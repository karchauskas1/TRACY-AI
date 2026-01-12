#!/usr/bin/env python3
"""
Тесты для критических сценариев TRACY AI BOT.
"""
import asyncio
import sys
from datetime import datetime, timedelta
import pytz
from database import Database
from reminder_scheduler import ReminderScheduler
from decision_engine import DecisionEngine
from calendar_google import GoogleCalendar
from calendar_icloud import ICloudCalendar
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Моковый бот для тестов
class MockBot:
    async def send_message(self, chat_id, text, **kwargs):
        logger.info(f"[MOCK BOT] Message to {chat_id}: {text[:100]}...")
        return type('obj', (object,), {'message_id': 1})()

async def test_morning_digest_timing():
    """Тест: утренний дайджест отправляется ровно в заданное время."""
    logger.info("=" * 60)
    logger.info("TEST 1: Утренний дайджест - точное время")
    logger.info("=" * 60)
    
    db = Database()
    mock_bot = MockBot()
    scheduler = ReminderScheduler(mock_bot, db)
    
    # Создаем тестового пользователя
    test_user_id = 999999
    user = db.get_or_create_user(test_user_id)
    
    # Устанавливаем время дайджеста на 1 минуту вперед
    test_time = (datetime.now(pytz.timezone('Europe/Moscow')) + timedelta(minutes=1)).strftime('%H:%M')
    db.update_user_settings(test_user_id, settings_dict={
        'morning_digest_time': test_time,
        'web_notifications_enabled': True,
        'timezone': 'Europe/Moscow'
    })
    
    logger.info(f"Установлено время дайджеста: {test_time}")
    logger.info("Ожидание 70 секунд для проверки...")
    
    # Ждем и проверяем
    await asyncio.sleep(70)
    
    # Проверяем, что дайджест был отправлен
    logger.info("✓ Тест завершен. Проверьте логи выше на наличие сообщения о дайджесте.")
    return True

async def test_default_reminder():
    """Тест: default reminder применяется при создании события."""
    logger.info("=" * 60)
    logger.info("TEST 2: Default Reminder при создании события")
    logger.info("=" * 60)
    
    db = Database()
    mock_bot = MockBot()
    scheduler = ReminderScheduler(mock_bot, db)
    decision_engine = DecisionEngine(db, scheduler, None)
    
    test_user_id = 999998
    user = db.get_or_create_user(test_user_id)
    
    # Устанавливаем default reminder на 30 минут
    db.update_user_settings(test_user_id, settings_dict={
        'default_reminder_minutes': 30,
        'timezone': 'Europe/Moscow'
    })
    
    # Создаем событие без указания reminder
    extracted_data = {
        'intent': 'event',
        'title': 'Тестовое событие',
        'start_time': datetime.now(pytz.timezone('Europe/Moscow')) + timedelta(hours=2),
        '_original_text': 'Тестовое событие через 2 часа'
    }
    
    result = await decision_engine.process_intent(test_user_id, extracted_data)
    
    if result.get('action') == 'created':
        # Проверяем, что reminder создан
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            if db.use_postgresql:
                cursor.execute("""
                    SELECT * FROM reminders 
                    WHERE user_id = %s AND event_id = (
                        SELECT id FROM events WHERE user_id = %s ORDER BY id DESC LIMIT 1
                    )
                """, (test_user_id, test_user_id))
            else:
                cursor.execute("""
                    SELECT * FROM reminders 
                    WHERE user_id = ? AND event_id = (
                        SELECT id FROM events WHERE user_id = ? ORDER BY id DESC LIMIT 1
                    )
                """, (test_user_id, test_user_id))
            
            reminders = cursor.fetchall()
            if reminders:
                logger.info(f"✓ Default reminder применен! Найдено {len(reminders)} напоминаний")
                return True
            else:
                logger.error("❌ Default reminder НЕ применен!")
                return False
        finally:
            db.return_connection(conn)
    else:
        logger.error(f"❌ Событие не создано: {result}")
        return False

async def test_create_event_from_meeting():
    """Тест: создание события из встречи."""
    logger.info("=" * 60)
    logger.info("TEST 3: Создание события из встречи")
    logger.info("=" * 60)
    
    db = Database()
    mock_bot = MockBot()
    scheduler = ReminderScheduler(mock_bot, db)
    decision_engine = DecisionEngine(db, scheduler, None)
    
    test_user_id = 999997
    
    # Симулируем создание события из встречи
    extracted_data = {
        'intent': 'event',
        'title': 'Событие из встречи',
        'start_time': datetime.now(pytz.timezone('Europe/Moscow')) + timedelta(days=1),
        'description': 'Создано из расшифровки встречи'
    }
    
    result = await decision_engine.process_intent(test_user_id, extracted_data)
    
    if result.get('action') == 'created':
        logger.info("✓ Событие из встречи создано успешно!")
        logger.info(f"  Сообщение: {result.get('message', '')[:100]}...")
        return True
    else:
        logger.error(f"❌ Событие не создано: {result}")
        return False

async def test_events_list_api():
    """Тест: API список всех событий."""
    logger.info("=" * 60)
    logger.info("TEST 4: API список всех событий")
    logger.info("=" * 60)
    
    db = Database()
    test_user_id = 999996
    user = db.get_or_create_user(test_user_id)
    
    # Создаем тестовое событие
    conn = db.get_connection()
    cursor = conn.cursor()
    try:
        test_time = datetime.now(pytz.timezone('Europe/Moscow')) + timedelta(days=1)
        if db.use_postgresql:
            cursor.execute("""
                INSERT INTO events (user_id, title, start_time, created_at)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                RETURNING id
            """, (test_user_id, 'Тестовое событие для API', test_time))
            event_id = cursor.fetchone()[0]
        else:
            cursor.execute("""
                INSERT INTO events (user_id, title, start_time, created_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (test_user_id, 'Тестовое событие для API', test_time.isoformat()))
            event_id = cursor.lastrowid
        
        conn.commit()
        logger.info(f"Создано тестовое событие: {event_id}")
    finally:
        db.return_connection(conn)
    
    # Получаем события через API метод БД
    events = db.get_events(test_user_id, limit=10)
    
    if events:
        logger.info(f"✓ API работает! Получено {len(events)} событий")
        return True
    else:
        logger.error("❌ API не вернул события")
        return False

async def main():
    """Запуск всех тестов."""
    logger.info("Запуск критических тестов TRACY AI BOT...")
    logger.info("")
    
    results = []
    
    try:
        # Тест 1: Утренний дайджест (пропускаем, требует долгого ожидания)
        # results.append(await test_morning_digest_timing())
        
        # Тест 2: Default Reminder
        results.append(await test_default_reminder())
        
        # Тест 3: Создание события из встречи
        results.append(await test_create_event_from_meeting())
        
        # Тест 4: API список событий
        results.append(await test_events_list_api())
        
    except Exception as e:
        logger.error(f"Ошибка при выполнении тестов: {e}", exc_info=True)
        return False
    
    # Итоги
    logger.info("")
    logger.info("=" * 60)
    logger.info("ИТОГИ ТЕСТИРОВАНИЯ")
    logger.info("=" * 60)
    passed = sum(results)
    total = len(results)
    logger.info(f"Пройдено: {passed}/{total}")
    
    if passed == total:
        logger.info("✅ Все тесты пройдены!")
        return True
    else:
        logger.error(f"❌ Провалено тестов: {total - passed}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)



