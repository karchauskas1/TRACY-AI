#!/usr/bin/env python3
"""
Тест для проверки удаления события через reply.

Проверяем что при reply на конкретное событие и команде "Удали",
бот удаляет ИМЕННО то событие на которое был reply, а не последнее.
"""
import asyncio
import sys
import logging
from datetime import datetime
from decision_engine import DecisionEngine
from database import Database

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_reply_delete():
    """Тест: Удаление через reply должно удалять конкретное событие."""

    db = Database()
    engine = DecisionEngine(db=db)
    test_user_id = 888888  # тестовый пользователь

    print("\n" + "="*70)
    print("ТЕСТ: Удаление через reply на конкретное событие")
    print("="*70)

    import pytz
    tz = pytz.timezone('Europe/Moscow')
    now = datetime.now(tz)

    # СЦЕНАРИЙ:
    # 1. Создаем событие A: "Встреча с Настей" в 15:00
    # 2. Создаем событие B: "Позвонить маме" в 16:00 (это станет last_event)
    # 3. Делаем reply на событие A и пишем "Удали"
    # 4. ОЖИДАЕМ: Удалится событие A, а НЕ событие B (last_event)

    # 1. Создаем событие A
    print("\n[1] Создаем событие A: 'Встреча с Настей'...")
    event_a_data = {
        'intent': 'event',
        'title': 'Встреча с Настей',
        'start_time': now.replace(hour=15, minute=0, second=0, microsecond=0),
        'has_explicit_time': True,
        'original_text': 'Встреча с Настей в 15:00'
    }

    result_a = await engine.process_intent(
        user_id=test_user_id,
        extracted_data=event_a_data,
        last_event=None,
        reply_to_event=None
    )

    event_a_id = result_a.get('event_id')
    if not event_a_id:
        print("❌ ОШИБКА: Событие A не создано!")
        return False

    # Получаем событие A из БД
    event_a = db.get_last_event(test_user_id)
    print(f"✓ Событие A создано: ID={event_a_id}, title='{event_a['title']}'")

    # 2. Создаем событие B
    print("\n[2] Создаем событие B: 'Позвонить маме'...")
    event_b_data = {
        'intent': 'event',
        'title': 'Позвонить маме',
        'start_time': now.replace(hour=16, minute=0, second=0, microsecond=0),
        'has_explicit_time': True,
        'original_text': 'Позвонить маме в 16:00'
    }

    result_b = await engine.process_intent(
        user_id=test_user_id,
        extracted_data=event_b_data,
        last_event=event_a,
        reply_to_event=None
    )

    event_b_id = result_b.get('event_id')
    if not event_b_id:
        print("❌ ОШИБКА: Событие B не создано!")
        return False

    event_b = db.get_last_event(test_user_id)
    print(f"✓ Событие B создано: ID={event_b_id}, title='{event_b['title']}'")
    print(f"✓ last_event теперь: '{event_b['title']}'")

    # 3. Делаем reply на событие A с командой "Удали"
    print("\n[3] Делаем reply на событие A и пишем 'Удали'...")
    delete_data = {
        'intent': 'delete',
        'original_text': 'Удали'
    }

    result_delete = await engine.process_intent(
        user_id=test_user_id,
        extracted_data=delete_data,
        last_event=event_b,  # last_event = событие B!
        reply_to_event=event_a  # НО reply на событие A!
    )

    action = result_delete.get('action')
    message = result_delete.get('message', '')

    print(f"\nРезультат удаления:")
    print(f"  action: {action}")
    print(f"  message: {message}")

    # 4. Проверяем результат
    print("\n" + "-"*70)

    # ОЖИДАЕМ:
    # - action='deleted'
    # - В сообщении должно быть "Встреча с Настей" (событие A), а НЕ "Позвонить маме"

    if action == 'deleted':
        if 'Встреча с Настей' in message:
            print("✅ ТЕСТ ПРОЙДЕН: Удалено правильное событие (из reply)!")
            print(f"   Удалено: '{event_a['title']}' (событие A - из reply)")
            print(f"   НЕ удалено: '{event_b['title']}' (событие B - last_event)")

            # Проверим что событие B всё ещё в БД
            events = db.get_events(test_user_id, limit=10)
            event_b_exists = any(e['id'] == event_b_id for e in events)
            event_a_exists = any(e['id'] == event_a_id for e in events)

            if not event_a_exists and event_b_exists:
                print("   ✓ Подтверждение: событие A удалено, событие B осталось")
                success = True
            else:
                print(f"   ⚠️  Состояние БД некорректно: A exists={event_a_exists}, B exists={event_b_exists}")
                success = False
        else:
            print("❌ ТЕСТ ПРОВАЛЕН: Удалено неправильное событие!")
            print(f"   Ожидалось: 'Встреча с Настей' (событие A)")
            print(f"   Получено: {message}")
            success = False
    else:
        print(f"❌ ТЕСТ ПРОВАЛЕН: action={action} вместо 'deleted'")
        print(f"   Сообщение: {message}")
        success = False

    # Cleanup
    if not success:
        print(f"\n[Cleanup] Удаляем тестовые события...")
        if event_a_id:
            db.delete_event(event_a_id, test_user_id)
        if event_b_id:
            db.delete_event(event_b_id, test_user_id)
    else:
        # Если успех, удаляем оставшееся событие B
        print(f"\n[Cleanup] Удаляем оставшееся событие B...")
        db.delete_event(event_b_id, test_user_id)

    print("="*70 + "\n")
    return success

async def main():
    success = await test_reply_delete()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    asyncio.run(main())
