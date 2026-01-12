#!/usr/bin/env python3
"""
Тесты для веб-интерфейса обратной связи.
Проверяет доступность страницы и корректность данных.
"""
import sys
import os
import httpx
import json

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config

API_BASE_URL = "http://5.35.126.42:8080"
SUPER_USER_ID = config.SUPER_USER_ID
TEST_USER_OTHER = 123456789

def test_web_api_access():
    """Тест доступа к API для веб-приложения."""
    print("\n" + "="*70)
    print("ТЕСТ: Доступ к API для веб-приложения")
    print("="*70)
    
    # Тест 1: Супер-пользователь
    print(f"\n1. Запрос от супер-пользователя (ID: {SUPER_USER_ID})")
    try:
        response = httpx.get(
            f"{API_BASE_URL}/api/feedback?user_id={SUPER_USER_ID}&limit=10",
            timeout=10.0
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Успешно получено {len(data.get('feedback', []))} записей")
            print(f"   Всего записей: {data.get('total', 0)}")
            
            # Проверяем структуру данных
            if data.get('feedback'):
                first_item = data['feedback'][0]
                required_fields = ['id', 'user_id', 'feedback_type', 'comment', 'created_at']
                missing_fields = [f for f in required_fields if f not in first_item]
                if missing_fields:
                    print(f"❌ Отсутствуют поля: {missing_fields}")
                    return False
                else:
                    print(f"✅ Структура данных корректна")
                    return True
            else:
                print("ℹ️  Нет записей для отображения (это нормально, если БД пустая)")
                return True
        else:
            print(f"❌ Ошибка: статус {response.status_code}")
            print(f"   Ответ: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False
    
    # Тест 2: Обычный пользователь
    print(f"\n2. Запрос от обычного пользователя (ID: {TEST_USER_OTHER})")
    try:
        response = httpx.get(
            f"{API_BASE_URL}/api/feedback?user_id={TEST_USER_OTHER}",
            timeout=10.0
        )
        
        if response.status_code == 403:
            print("✅ Правильно запрещен доступ для обычного пользователя")
            return True
        else:
            print(f"❌ Ожидался статус 403, получен {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    result = test_web_api_access()
    sys.exit(0 if result else 1)

