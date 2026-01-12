#!/usr/bin/env python3
"""
Тесты для функционала обратной связи.
Проверяет работу Apps Script webhook и маппинг user_id.
"""
import sys
import os
import httpx
import json
from datetime import datetime

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from feedback_service import FeedbackService, get_feedback_sheet_mapping

# URL Apps Script
APPS_SCRIPT_URL = config.FEEDBACK_APPS_SCRIPT_URL

# Тестовые user_id
TEST_USER_KATYA = 332023536
TEST_USER_DANYA = 308477378
TEST_USER_OTHER = 123456789

def test_apps_script_connection():
    """Тест 1: Проверка подключения к Apps Script."""
    print("\n" + "="*60)
    print("ТЕСТ 1: Проверка подключения к Apps Script")
    print("="*60)
    
    if not APPS_SCRIPT_URL:
        print("❌ FEEDBACK_APPS_SCRIPT_URL не установлен")
        return False
    
    print(f"✅ URL Apps Script: {APPS_SCRIPT_URL[:50]}...")
    
    try:
        # Простой GET запрос для проверки доступности
        response = httpx.get(APPS_SCRIPT_URL, timeout=10.0, follow_redirects=True)
        print(f"✅ Apps Script доступен (статус: {response.status_code})")
        return True
    except Exception as e:
        print(f"❌ Ошибка подключения к Apps Script: {e}")
        return False

def test_feedback_submission(user_id, feedback_type, comment, expected_sheet):
    """Тест отправки обратной связи через Apps Script."""
    print(f"\n{'='*60}")
    print(f"ТЕСТ: Отправка {feedback_type} от user_id {user_id}")
    print(f"Ожидаемый лист: {expected_sheet}")
    print("="*60)
    
    try:
        # Подготавливаем данные
        data = {
            "type": feedback_type,
            "user_id": str(user_id),
            "comment": comment,
        }
        
        print(f"📤 Отправляю данные: {json.dumps(data, ensure_ascii=False, indent=2)}")
        
        # Отправляем POST запрос
        response = httpx.post(
            APPS_SCRIPT_URL,
            json=data,
            timeout=10.0,
            follow_redirects=True
        )
        
        print(f"📥 Статус ответа: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"📋 Результат: {json.dumps(result, ensure_ascii=False, indent=2)}")
                
                if result.get("success"):
                    actual_sheet = result.get("sheet", "не указан")
                    if actual_sheet == expected_sheet:
                        print(f"✅ УСПЕХ: Запись добавлена в лист '{actual_sheet}'")
                        print(f"   Номер записи: #{result.get('number')}")
                        print(f"   Дата: {result.get('date')}")
                        return True
                    else:
                        print(f"❌ ОШИБКА: Ожидался лист '{expected_sheet}', получен '{actual_sheet}'")
                        return False
                else:
                    print(f"❌ ОШИБКА: Apps Script вернул ошибку: {result.get('error')}")
                    return False
            except json.JSONDecodeError:
                print(f"❌ ОШИБКА: Не удалось распарсить JSON ответ")
                print(f"   Ответ: {response.text[:200]}")
                return False
        elif response.status_code == 401:
            print(f"❌ ОШИБКА: Apps Script требует авторизации (401)")
            print(f"   💡 Нужно развернуть веб-приложение с доступом 'Все'")
            print(f"   Инструкция:")
            print(f"   1. Открой Apps Script")
            print(f"   2. Развернуть → Новое развертывание")
            print(f"   3. Тип: Веб-приложение")
            print(f"   4. Выполнять от имени: Меня")
            print(f"   5. У кого есть доступ: ВСЕ (важно!)")
            print(f"   6. Развернуть и скопировать новый URL")
            return False
        else:
            print(f"❌ ОШИБКА: HTTP статус {response.status_code}")
            print(f"   Ответ: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_sheet_mapping():
    """Тест маппинга user_id -> лист."""
    print("\n" + "="*60)
    print("ТЕСТ: Проверка маппинга user_id -> лист")
    print("="*60)
    
    mapping = get_feedback_sheet_mapping()
    print(f"📋 Маппинг из переменных окружения Python: {mapping}")
    print("ℹ️  Примечание: Маппинг также настроен в Apps Script")
    print("   Apps Script использует свой маппинг независимо от Python")
    
    # Проверяем ожидаемые маппинги (для информации)
    expected = {
        TEST_USER_KATYA: "Тестировщик Катя",
        TEST_USER_DANYA: "Тестировщик Даня",
    }
    
    all_ok = True
    for user_id, expected_sheet in expected.items():
        actual_sheet = mapping.get(user_id, "Общий")
        if actual_sheet == expected_sheet:
            print(f"✅ user_id {user_id} -> '{actual_sheet}' (в Python маппинге)")
        else:
            print(f"⚠️  user_id {user_id} -> '{actual_sheet}' в Python (ожидалось '{expected_sheet}')")
            print(f"   ℹ️  Но Apps Script использует свой маппинг, это нормально")
    
    # Маппинг в Apps Script проверяется через реальные запросы
    print("✅ Маппинг будет проверен через реальные запросы к Apps Script")
    return True

def test_feedback_service_class():
    """Тест класса FeedbackService."""
    print("\n" + "="*60)
    print("ТЕСТ: Проверка класса FeedbackService")
    print("="*60)
    
    try:
        # Проверяем, что класс можно создать
        service = FeedbackService(TEST_USER_KATYA)
        print(f"✅ FeedbackService создан для user_id {TEST_USER_KATYA}")
        
        # Проверяем метод submit_feedback_via_apps_script
        if hasattr(service, 'submit_feedback_via_apps_script'):
            print("✅ Метод submit_feedback_via_apps_script существует")
        else:
            print("❌ Метод submit_feedback_via_apps_script не найден")
            return False
        
        # Проверяем метод submit_feedback
        if hasattr(service, 'submit_feedback'):
            print("✅ Метод submit_feedback существует")
        else:
            print("❌ Метод submit_feedback не найден")
            return False
        
        return True
    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_all_tests():
    """Запуск всех тестов."""
    print("\n" + "🔬"*30)
    print("НАЧАЛО ТЕСТИРОВАНИЯ ОБРАТНОЙ СВЯЗИ")
    print("🔬"*30)
    
    results = []
    
    # Тест 1: Проверка подключения
    results.append(("Подключение к Apps Script", test_apps_script_connection()))
    
    # Тест 2: Проверка класса
    results.append(("Класс FeedbackService", test_feedback_service_class()))
    
    # Тест 3: Проверка маппинга
    results.append(("Маппинг user_id -> лист", test_sheet_mapping()))
    
    # Тест 4: Отправка бага от Кати
    results.append((
        f"Баг от Кати (user_id {TEST_USER_KATYA})",
        test_feedback_submission(
            TEST_USER_KATYA,
            "баг",
            f"Тестовый баг от Кати - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "Тестировщик Катя"
        )
    ))
    
    # Тест 5: Отправка предложения от Дани
    results.append((
        f"Предложение от Дани (user_id {TEST_USER_DANYA})",
        test_feedback_submission(
            TEST_USER_DANYA,
            "предложение",
            f"Тестовое предложение от Дани - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "Тестировщик Даня"
        )
    ))
    
    # Тест 6: Отправка от другого пользователя (должен попасть в "Общий")
    results.append((
        f"Баг от другого пользователя (user_id {TEST_USER_OTHER})",
        test_feedback_submission(
            TEST_USER_OTHER,
            "баг",
            f"Тестовый баг от другого пользователя - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "Общий"
        )
    ))
    
    # Итоговый отчет
    print("\n" + "="*60)
    print("ИТОГОВЫЙ ОТЧЕТ")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        print(f"{status}: {test_name}")
    
    print("\n" + "="*60)
    print(f"РЕЗУЛЬТАТ: {passed}/{total} тестов пройдено")
    print("="*60)
    
    if passed == total:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        return 0
    else:
        print("⚠️ НЕКОТОРЫЕ ТЕСТЫ ПРОВАЛЕНЫ")
        return 1

if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)

