#!/usr/bin/env python3
"""Тестирование small_talk функциональности."""

import asyncio
import sys
from nlp_extractor import NLPExtractor
from decision_engine import DecisionEngine
from database import Database
import config

async def test_small_talk():
    """Протестировать различные сценарии small_talk."""

    print("🧪 Тестирование small_talk функциональности\n")
    print("=" * 60)

    # Инициализация компонентов
    nlp = NLPExtractor()
    db = Database()
    engine = DecisionEngine(db)

    test_user_id = 999999  # Тестовый пользователь

    # Тестовые кейсы
    test_cases = [
        # Сценарий 1: Чистые small_talk сообщения
        ("привет", "small_talk", "Должен ответить дружелюбным приветствием"),
        ("как дела?", "small_talk", "Должен спросить как у пользователя"),
        ("спасибо", "small_talk", "Должен ответить 'Пожалуйста'"),
        ("пока", "small_talk", "Должен попрощаться"),

        # Сценарий 2: Чистые команды
        ("Встреча завтра в 15:00", "event", "Должен создать событие, НЕ приветствие"),

        # Сценарий 3: Гибридные (команда + small_talk) - команда в приоритете
        ("Привет! Встреча завтра в 15:00", "event", "Должен создать событие, игнорировать 'привет'"),
        ("Спасибо! Удали встречу", "delete", "Должен удалить, игнорировать 'спасибо'"),
    ]

    results = []

    for i, (text, expected_intent, description) in enumerate(test_cases, 1):
        print(f"\n{'─' * 60}")
        print(f"Тест {i}/{len(test_cases)}: {description}")
        print(f"Ввод: '{text}'")
        print(f"Ожидаемый intent: {expected_intent}")

        try:
            # Извлекаем intent через NLP
            extracted = await nlp.extract_intent_and_context(text)
            actual_intent = extracted.get('intent', 'unknown')

            print(f"✓ NLP извлёк intent: {actual_intent}")

            # Если это small_talk, тестируем ответ
            if actual_intent == 'small_talk':
                result = await engine._handle_small_talk(test_user_id, extracted)
                bot_response = result.get('message', '')

                print(f"✓ Ответ бота: '{bot_response}'")

                # Проверяем, что ответ НЕ содержит "Что я умею" и другие формальности
                if len(bot_response) > 200:
                    print("⚠️  ПРЕДУПРЕЖДЕНИЕ: Ответ слишком длинный (>200 символов)")
                    results.append(('WARN', text, f"Ответ слишком длинный: {len(bot_response)} символов"))
                elif "умею" in bot_response.lower() or "возможности" in bot_response.lower():
                    print("⚠️  ПРЕДУПРЕЖДЕНИЕ: Ответ содержит описание возможностей бота")
                    results.append(('WARN', text, "Ответ содержит описание возможностей"))
                else:
                    print("✅ Ответ выглядит естественно и коротко")
                    results.append(('PASS', text, bot_response))

            # Проверяем соответствие ожидаемому intent
            if actual_intent == expected_intent:
                print(f"✅ Intent корректен: {actual_intent}")
                if actual_intent != 'small_talk':
                    results.append(('PASS', text, f"Intent: {actual_intent}"))
            else:
                print(f"❌ ОШИБКА: Ожидали {expected_intent}, получили {actual_intent}")
                results.append(('FAIL', text, f"Ожидали {expected_intent}, получили {actual_intent}"))

        except Exception as e:
            print(f"❌ ОШИБКА при обработке: {e}")
            results.append(('FAIL', text, str(e)))

    # Итоговый отчёт
    print(f"\n\n{'═' * 60}")
    print("📊 ИТОГОВЫЙ ОТЧЁТ")
    print(f"{'═' * 60}\n")

    passed = sum(1 for status, _, _ in results if status == 'PASS')
    failed = sum(1 for status, _, _ in results if status == 'FAIL')
    warnings = sum(1 for status, _, _ in results if status == 'WARN')

    print(f"✅ Пройдено: {passed}/{len(results)}")
    print(f"❌ Провалено: {failed}/{len(results)}")
    print(f"⚠️  Предупреждений: {warnings}/{len(results)}")

    if failed > 0:
        print("\n❌ Провалившиеся тесты:")
        for status, text, reason in results:
            if status == 'FAIL':
                print(f"  - '{text}': {reason}")

    if warnings > 0:
        print("\n⚠️  Тесты с предупреждениями:")
        for status, text, reason in results:
            if status == 'WARN':
                print(f"  - '{text}': {reason}")

    print(f"\n{'═' * 60}\n")

    return failed == 0 and warnings == 0

if __name__ == "__main__":
    try:
        success = asyncio.run(test_small_talk())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Тестирование прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
