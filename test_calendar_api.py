#!/usr/bin/env python3
"""
Тест API календаря для веб-приложения.
Проверяет доступность API и правильность формата данных.
"""
import requests
import json
import sys

def test_calendar_api():
    """Тестирует API календаря."""
    print("=" * 70)
    print("🧪 ТЕСТ API КАЛЕНДАРЯ ДЛЯ ВЕБ-ПРИЛОЖЕНИЯ")
    print("=" * 70)
    
    # Тестируем локальный API
    print("\n📡 Тест 1: Локальный API (localhost:8080)")
    try:
        response = requests.get('http://localhost:8080/api/events?user_id=308477378', timeout=5)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Успешно! Событий: {len(data.get('events', []))}")
            if data.get('success'):
                print(f"   ✅ Формат данных корректен")
            else:
                print(f"   ⚠️ success=false в ответе")
        else:
            print(f"   ❌ Ошибка: {response.status_code}")
            print(f"   Ответ: {response.text[:200]}")
    except requests.exceptions.ConnectionError:
        print("   ⚠️ Локальный API недоступен (это нормально, если тест запущен не на сервере)")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    # Тестируем внешний API
    print("\n📡 Тест 2: Внешний API (5.35.126.42)")
    try:
        response = requests.get('http://5.35.126.42/api/events?user_id=308477378', timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            events_count = len(data.get('events', []))
            print(f"   ✅ Успешно! Событий: {events_count}")
            
            if data.get('success'):
                print(f"   ✅ Формат данных корректен (success=true)")
            else:
                print(f"   ⚠️ success=false в ответе")
            
            if events_count > 0:
                print(f"\n   📅 Примеры событий:")
                for i, event in enumerate(data.get('events', [])[:3], 1):
                    title = event.get('title', 'Без названия')
                    start_at = event.get('startAt', 'N/A')
                    print(f"   {i}. {title[:40]}... (начало: {start_at})")
                
                # Проверяем формат данных
                first_event = data.get('events', [])[0]
                required_fields = ['id', 'title', 'startAt', 'endAt', 'calendarSource']
                missing_fields = [f for f in required_fields if f not in first_event]
                if missing_fields:
                    print(f"   ⚠️ Отсутствуют поля: {missing_fields}")
                else:
                    print(f"   ✅ Все обязательные поля присутствуют")
            else:
                print(f"   ⚠️ Событий нет в ответе")
        else:
            print(f"   ❌ Ошибка: {response.status_code}")
            print(f"   Ответ: {response.text[:200]}")
            return False
    except requests.exceptions.ConnectionError:
        print("   ❌ Не удалось подключиться к API")
        return False
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return False
    
    # Тест CORS
    print("\n📡 Тест 3: CORS заголовки")
    try:
        response = requests.options('http://5.35.126.42/api/events?user_id=308477378', timeout=5)
        cors_headers = {
            'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
            'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
        }
        print(f"   CORS заголовки: {cors_headers}")
        if cors_headers.get('Access-Control-Allow-Origin'):
            print(f"   ✅ CORS настроен")
        else:
            print(f"   ⚠️ CORS заголовки отсутствуют")
    except Exception as e:
        print(f"   ⚠️ Не удалось проверить CORS: {e}")
    
    print("\n" + "=" * 70)
    print("✅ ТЕСТЫ ЗАВЕРШЕНЫ")
    print("=" * 70)
    return True

if __name__ == "__main__":
    try:
        result = test_calendar_api()
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Тест прерван пользователем")
        sys.exit(1)



