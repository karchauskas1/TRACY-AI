#!/usr/bin/env python3
"""
Тест API для веб-приложения.
Проверяет доступность API и правильность формата данных.
"""
import requests
import json

def test_api_access():
    """Тестирует доступность API."""
    print("=" * 70)
    print("🧪 ТЕСТ API ДЛЯ ВЕБ-ПРИЛОЖЕНИЯ")
    print("=" * 70)
    
    user_id = 308477378
    api_url = f"http://5.35.126.42/api/events?user_id={user_id}"
    
    print(f"\n📡 Тест 1: Прямой запрос к API")
    print(f"   URL: {api_url}")
    try:
        response = requests.get(api_url, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            events_count = len(data.get('events', []))
            print(f"   ✅ Успешно! Событий: {events_count}")
            
            if events_count > 0:
                print(f"\n   📅 Примеры событий:")
                for i, event in enumerate(data.get('events', [])[:3], 1):
                    title = event.get('title', 'Без названия')
                    start_at = event.get('startAt', 'N/A')
                    print(f"   {i}. {title[:40]}... (начало: {start_at})")
        else:
            print(f"   ❌ Ошибка: {response.status_code}")
            print(f"   Ответ: {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    print(f"\n📡 Тест 2: CORS заголовки")
    try:
        response = requests.options(api_url, timeout=5)
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
    
    print(f"\n📡 Тест 3: Mixed Content (HTTPS → HTTP)")
    print(f"   ⚠️ ПРОБЛЕМА: GitHub Pages работает по HTTPS, API по HTTP")
    print(f"   ⚠️ Браузер блокирует такие запросы из-за Mixed Content Policy")
    print(f"   💡 РЕШЕНИЕ: Использовать Telegram Web App API для получения событий")
    print(f"      или настроить HTTPS на сервере")
    
    print("\n" + "=" * 70)
    print("✅ ТЕСТЫ ЗАВЕРШЕНЫ")
    print("=" * 70)

if __name__ == "__main__":
    test_api_access()


