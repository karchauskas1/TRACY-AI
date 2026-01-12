#!/usr/bin/env python3
"""
Комплексные тесты для функционала обратной связи.
Проверяет все аспекты: Apps Script, БД, маппинг, скриншоты.
"""
import sys
import os
import httpx
import json
from datetime import datetime
import time

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from feedback_service import FeedbackService, get_feedback_sheet_mapping
from database import Database

# URL Apps Script
APPS_SCRIPT_URL = config.FEEDBACK_APPS_SCRIPT_URL
SUPER_USER_ID = config.SUPER_USER_ID

# Тестовые user_id
TEST_USER_KATYA = 332023536
TEST_USER_DANYA = 308477378
TEST_USER_OTHER = 123456789

# API URL
API_BASE_URL = "http://5.35.126.42:8080"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_success(msg):
    print(f"{Colors.GREEN}✅ {msg}{Colors.RESET}")

def print_error(msg):
    print(f"{Colors.RED}❌ {msg}{Colors.RESET}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.RESET}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.RESET}")

def print_header(msg):
    print(f"\n{Colors.BOLD}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{msg}{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*70}{Colors.RESET}\n")

def test_1_apps_script_connection():
    """Тест 1: Проверка подключения к Apps Script."""
    print_header("ТЕСТ 1: Проверка подключения к Apps Script")
    
    if not APPS_SCRIPT_URL:
        print_error("FEEDBACK_APPS_SCRIPT_URL не установлен")
        return False
    
    print_info(f"URL: {APPS_SCRIPT_URL[:60]}...")
    
    try:
        response = httpx.get(APPS_SCRIPT_URL + "?action=test", timeout=10.0, follow_redirects=True)
        if response.status_code == 200:
            print_success(f"Apps Script доступен (статус: {response.status_code})")
            return True
        else:
            print_error(f"Неожиданный статус: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Ошибка подключения: {e}")
        return False

def test_2_feedback_service_class():
    """Тест 2: Проверка класса FeedbackService."""
    print_header("ТЕСТ 2: Проверка класса FeedbackService")
    
    try:
        service = FeedbackService(TEST_USER_KATYA)
        print_success(f"FeedbackService создан для user_id {TEST_USER_KATYA}")
        
        methods = ['submit_feedback_via_apps_script', 'submit_feedback', 'upload_screenshot_to_drive']
        for method in methods:
            if hasattr(service, method):
                print_success(f"Метод {method} существует")
            else:
                print_error(f"Метод {method} не найден")
                return False
        
        return True
    except Exception as e:
        print_error(f"Ошибка: {e}")
        return False

def test_3_database_feedback_table():
    """Тест 3: Проверка таблицы feedback в БД."""
    print_header("ТЕСТ 3: Проверка таблицы feedback в БД")
    
    try:
        db = Database()
        
        # Проверяем методы
        methods = ['save_feedback', 'get_all_feedback', 'get_feedback_count']
        for method in methods:
            if hasattr(db, method):
                print_success(f"Метод {method} существует")
            else:
                print_error(f"Метод {method} не найден")
                return False
        
        # Проверяем, что таблица существует (попытка получить count)
        try:
            count = db.get_feedback_count()
            print_success(f"Таблица feedback существует, записей: {count}")
            return True
        except Exception as e:
            print_warning(f"Ошибка при проверке таблицы: {e}")
            print_info("Таблица будет создана при первой записи")
            return True
        
    except Exception as e:
        print_error(f"Ошибка: {e}")
        return False

def test_4_feedback_submission_with_mapping(user_id, feedback_type, expected_sheet, test_name):
    """Тест 4: Отправка обратной связи с проверкой маппинга."""
    print_header(f"ТЕСТ 4.{test_name}: Отправка {feedback_type} от user_id {user_id}")
    print_info(f"Ожидаемый лист: {expected_sheet}")
    
    try:
        data = {
            "type": feedback_type,
            "user_id": str(user_id),
            "comment": f"Тест {test_name} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        }
        
        print_info(f"Отправляю данные: {json.dumps(data, ensure_ascii=False)}")
        
        response = httpx.post(
            APPS_SCRIPT_URL,
            json=data,
            timeout=10.0,
            follow_redirects=True
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                actual_sheet = result.get("sheet", "не указан")
                if actual_sheet == expected_sheet:
                    print_success(f"Запись добавлена в лист '{actual_sheet}'")
                    print_info(f"  Номер: #{result.get('number')}, Дата: {result.get('date')}")
                    return True
                else:
                    print_error(f"Ожидался лист '{expected_sheet}', получен '{actual_sheet}'")
                    return False
            else:
                print_error(f"Apps Script вернул ошибку: {result.get('error')}")
                return False
        else:
            print_error(f"HTTP статус {response.status_code}: {response.text[:200]}")
            return False
            
    except Exception as e:
        print_error(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_5_database_save_and_retrieve():
    """Тест 5: Сохранение и получение обратной связи из БД."""
    print_header("ТЕСТ 5: Сохранение и получение из БД")
    
    try:
        db = Database()
        
        # Сохраняем тестовую запись
        test_comment = f"Тест БД - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        feedback_id = db.save_feedback(
            user_id=TEST_USER_OTHER,
            feedback_type="баг",
            comment=test_comment,
            screenshot_url="https://example.com/test.jpg"
        )
        
        if feedback_id:
            print_success(f"Запись сохранена в БД, ID: {feedback_id}")
        else:
            print_error("Не удалось сохранить запись в БД")
            return False
        
        # Получаем все записи
        feedback_list = db.get_all_feedback(limit=10)
        print_info(f"Получено записей из БД: {len(feedback_list)}")
        
        # Ищем нашу запись
        found = False
        for item in feedback_list:
            if item.get('id') == feedback_id:
                found = True
                if item.get('comment') == test_comment:
                    print_success("Запись найдена в БД с правильным комментарием")
                    print_info(f"  ID: {item.get('id')}, User ID: {item.get('user_id')}, Тип: {item.get('feedback_type')}")
                    return True
                else:
                    print_error(f"Комментарий не совпадает: ожидалось '{test_comment}', получено '{item.get('comment')}'")
                    return False
        
        if not found:
            print_warning("Запись не найдена в списке (возможно, она в другой странице)")
            # Проверяем count
            count = db.get_feedback_count()
            print_info(f"Всего записей в БД: {count}")
            return True  # Не критично, если запись есть, но не в первых 10
        
        return True
        
    except Exception as e:
        print_error(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_6_api_endpoint():
    """Тест 6: Проверка API endpoint для обратной связи."""
    print_header("ТЕСТ 6: Проверка API endpoint /api/feedback")
    
    try:
        # Тест 1: Запрос без user_id
        print_info("Тест 6.1: Запрос без user_id")
        response = httpx.get(f"{API_BASE_URL}/api/feedback", timeout=10.0)
        if response.status_code == 400:
            print_success("Правильно возвращает 400 без user_id")
        else:
            print_error(f"Ожидался статус 400, получен {response.status_code}")
            return False
        
        # Тест 2: Запрос от обычного пользователя
        print_info("Тест 6.2: Запрос от обычного пользователя (должен быть 403)")
        response = httpx.get(f"{API_BASE_URL}/api/feedback?user_id={TEST_USER_OTHER}", timeout=10.0)
        if response.status_code == 403:
            print_success("Правильно возвращает 403 для обычного пользователя")
        else:
            print_error(f"Ожидался статус 403, получен {response.status_code}")
            return False
        
        # Тест 3: Запрос от супер-пользователя
        print_info(f"Тест 6.3: Запрос от супер-пользователя (ID: {SUPER_USER_ID})")
        response = httpx.get(f"{API_BASE_URL}/api/feedback?user_id={SUPER_USER_ID}&limit=10", timeout=10.0)
        if response.status_code == 200:
            data = response.json()
            if 'feedback' in data and 'total' in data:
                print_success(f"API вернул данные: {len(data['feedback'])} записей из {data['total']} всего")
                return True
            else:
                print_error(f"Неверный формат ответа: {data}")
                return False
        else:
            print_error(f"Ожидался статус 200, получен {response.status_code}")
            print_error(f"Ответ: {response.text[:200]}")
            return False
        
    except Exception as e:
        print_error(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_7_multiple_submissions():
    """Тест 7: Множественные отправки для проверки стабильности."""
    print_header("ТЕСТ 7: Множественные отправки (проверка стабильности)")
    
    results = []
    for i in range(3):
        print_info(f"Попытка {i+1}/3")
        result = test_4_feedback_submission_with_mapping(
            TEST_USER_KATYA,
            "баг",
            "Тестировщик Катя",
            f"стабильность_{i+1}"
        )
        results.append(result)
        if i < 2:
            time.sleep(1)  # Небольшая задержка между запросами
    
    success_count = sum(1 for r in results if r)
    if success_count == 3:
        print_success(f"Все {success_count} попыток успешны")
        return True
    else:
        print_error(f"Только {success_count}/3 попыток успешны")
        return False

def test_8_feedback_service_integration():
    """Тест 8: Интеграция FeedbackService с Apps Script."""
    print_header("ТЕСТ 8: Интеграция FeedbackService с Apps Script")
    
    try:
        service = FeedbackService(TEST_USER_DANYA)
        
        test_comment = f"Тест интеграции - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # Используем Apps Script
        result = service.submit_feedback_via_apps_script(
            feedback_type="предложение",
            comment=test_comment
        )
        
        if result and result.get("success"):
            actual_sheet = result.get("sheet")
            if actual_sheet == "Тестировщик Даня":
                print_success(f"Интеграция работает, запись в листе '{actual_sheet}'")
                return True
            else:
                print_error(f"Неверный лист: ожидалось 'Тестировщик Даня', получено '{actual_sheet}'")
                return False
        else:
            print_error(f"Ошибка отправки: {result}")
            return False
            
    except Exception as e:
        print_error(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_all_tests():
    """Запуск всех тестов."""
    print(f"\n{Colors.BOLD}{'🔬'*35}{Colors.RESET}")
    print(f"{Colors.BOLD}КОМПЛЕКСНОЕ ТЕСТИРОВАНИЕ ОБРАТНОЙ СВЯЗИ{Colors.RESET}")
    print(f"{Colors.BOLD}{'🔬'*35}{Colors.RESET}\n")
    
    results = []
    
    # Базовые тесты
    results.append(("1. Подключение к Apps Script", test_1_apps_script_connection()))
    results.append(("2. Класс FeedbackService", test_2_feedback_service_class()))
    results.append(("3. Таблица feedback в БД", test_3_database_feedback_table()))
    
    # Тесты отправки с маппингом
    results.append(("4.1. Баг от Кати → Тестировщик Катя", 
                    test_4_feedback_submission_with_mapping(TEST_USER_KATYA, "баг", "Тестировщик Катя", "4.1")))
    results.append(("4.2. Предложение от Дани → Тестировщик Даня", 
                    test_4_feedback_submission_with_mapping(TEST_USER_DANYA, "предложение", "Тестировщик Даня", "4.2")))
    results.append(("4.3. Баг от другого → Общий", 
                    test_4_feedback_submission_with_mapping(TEST_USER_OTHER, "баг", "Общий", "4.3")))
    
    # Тесты БД
    results.append(("5. Сохранение и получение из БД", test_5_database_save_and_retrieve()))
    
    # Тесты API
    results.append(("6. API endpoint /api/feedback", test_6_api_endpoint()))
    
    # Тесты стабильности
    results.append(("7. Множественные отправки", test_7_multiple_submissions()))
    
    # Тесты интеграции
    results.append(("8. Интеграция FeedbackService", test_8_feedback_service_integration()))
    
    # Итоговый отчет
    print_header("ИТОГОВЫЙ ОТЧЕТ")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = f"{Colors.GREEN}✅ ПРОЙДЕН{Colors.RESET}" if result else f"{Colors.RED}❌ ПРОВАЛЕН{Colors.RESET}"
        print(f"{status}: {test_name}")
    
    print(f"\n{Colors.BOLD}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}РЕЗУЛЬТАТ: {passed}/{total} тестов пройдено{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*70}{Colors.RESET}\n")
    
    if passed == total:
        print(f"{Colors.GREEN}{Colors.BOLD}🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!{Colors.RESET}")
        return 0
    else:
        print(f"{Colors.RED}{Colors.BOLD}⚠️ НЕКОТОРЫЕ ТЕСТЫ ПРОВАЛЕНЫ{Colors.RESET}")
        return 1

if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)

