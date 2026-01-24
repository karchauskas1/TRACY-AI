#!/usr/bin/env python3
"""
Тест для проверки исправления команды delete.

Проверяем что при команде "Удали" после создания события,
бот удаляет событие вместо того чтобы спрашивать "Что именно планируешь?"
"""
import asyncio
import sys
import logging
from datetime import datetime
from decision_engine import DecisionEngine

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_delete_without_title():
    """Тест: Команда 'Удали' после создания события должна удалять, а не спрашивать."""

    from database import Database
    db = Database()
    engine = DecisionEngine(db=db)
    test_user_id = 999999  # тестовый пользователь

    print("\n" + "="*70)
    print("ТЕСТ: Удаление события командой 'Удали' без указания title")
    print("="*70)

    # ШАГИ ТЕСТА:

    # 1. Создаем событие "Закончить встречу с Настей"
    print("\n[1] Создаем тестовое событие...")
    import pytz
    tz = pytz.timezone('Europe/Moscow')
    now = datetime.now(tz)

    event_data_create = {
        'intent': 'event',
        'title': 'Закончить встречу с Настей',
        'start_time': now.replace(hour=15, minute=0, second=0, microsecond=0),
        'has_explicit_time': True,
        'original_text': 'Закончить встречу с Настей в 15:00'
    }

    result_create = await engine.process_intent(
        user_id=test_user_id,
        extracted_data=event_data_create,
        last_event=None,
        reply_to_event=None
    )

    print(f"Результат создания: action={result_create.get('action')}")
    print(f"Сообщение: {result_create.get('message', 'N/A')[:100]}...")

    # Получаем ID созданного события
    event_id = result_create.get('event_id')
    if not event_id:
        print("❌ ОШИБКА: Событие не создано!")
        return False

    # Получаем последнее событие для контекста
    last_event = db.get_last_event(test_user_id)

    print(f"✓ Событие создано с ID={event_id}")
    print(f"✓ last_event: {last_event.get('title') if last_event else 'None'}")

    # 2. Удаляем событие командой "Удали" БЕЗ указания title
    print("\n[2] Отправляем команду 'Удали' без указания title...")
    delete_data = {
        'intent': 'delete',
        # НЕТ 'title'!
        # НЕТ 'refers_to_last_event'!
        'original_text': 'Удали'
    }

    result_delete = await engine.process_intent(
        user_id=test_user_id,
        extracted_data=delete_data,
        last_event=last_event,  # Передаем last_event
        reply_to_event=None
    )

    action = result_delete.get('action')
    message = result_delete.get('message', '')

    print(f"\nРезультат удаления:")
    print(f"  action: {action}")
    print(f"  message: {message}")

    # 3. Проверяем результат
    print("\n" + "-"*70)

    # ОЖИДАЕМ: action='deleted' (событие удалено)
    # НЕ ОЖИДАЕМ: action='awaiting_input' (бот спрашивает "Что именно планируешь?")

    if action == 'deleted':
        print("✅ ТЕСТ ПРОЙДЕН: Событие удалено!")
        print(f"   Сообщение: {message}")
        success = True
    elif action == 'awaiting_input':
        print("❌ ТЕСТ ПРОВАЛЕН: Бот спросил 'Что именно планируешь?' вместо удаления!")
        print(f"   Сообщение: {message}")
        success = False
    else:
        print(f"⚠️  НЕОЖИДАННЫЙ РЕЗУЛЬТАТ: action={action}")
        print(f"   Сообщение: {message}")
        success = False

    # Очистка: удаляем тестовое событие если оно осталось
    if not success and event_id:
        print(f"\n[Cleanup] Удаляем тестовое событие {event_id}...")
        db.delete_event(event_id, test_user_id)

    print("="*70 + "\n")
    return success

async def main():
    success = await test_delete_without_title()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    asyncio.run(main())
