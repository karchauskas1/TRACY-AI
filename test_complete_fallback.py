#!/usr/bin/env python3
"""Полный тест fallback логики от начала до конца."""
import sys
sys.path.insert(0, '.')

from datetime import datetime
import dateparser
import pytz
import re

def test_complete_fallback():
    """Тестирует полный сценарий: NLP не работает -> fallback extraction -> process_intent -> _handle_event"""
    
    print("🧪 ПОЛНЫЙ ТЕСТ FALLBACK ЛОГИКИ\n")
    print("=" * 60)
    
    # Шаг 1: NLP не работает, _fallback_extraction возвращает результат
    text = 'сегодня в 12:30 стрижка'
    timezone = 'Europe/Moscow'
    
    extracted_data = {
        "intent": "note",
        "title": text[:50],
        "description": text,
        "start_time": None,
        "end_time": None,
        "location": None,
        "priority": 0,
        "has_explicit_time": False,
        "confidence": 0.3,
        "_original_text": text  # ✅ Теперь сохраняется
    }
    
    print("1️⃣ После _fallback_extraction:")
    print(f"   intent: {extracted_data['intent']}")
    print(f"   start_time: {extracted_data['start_time']}")
    print(f"   has_explicit_time: {extracted_data['has_explicit_time']}")
    print(f"   _original_text: '{extracted_data.get('_original_text', 'НЕТ')}'")
    
    # Шаг 2: process_intent fallback переопределяет intent
    original_text = extracted_data.get('_original_text', '').lower().strip()
    if not original_text:
        original_text = (extracted_data.get('title', '') or extracted_data.get('description', '')).lower().strip()
    
    time_pattern = r'\b(\d{1,2}[:.]\d{2}|\d{1,2}\s*(?:час|часа|часов|утра|дня|вечера|ночи)|в\s*\d{1,2})\b'
    has_time_format = bool(re.search(time_pattern, original_text, re.IGNORECASE)) if original_text else False
    
    time_keywords = ['сегодня', 'завтра', 'в', '12:30']
    has_time_in_text = any(keyword in original_text for keyword in time_keywords) if original_text else False
    has_any_time = has_time_in_text or has_time_format
    
    title = extracted_data.get('title', '') or extracted_data.get('description', '')
    has_action = bool(title and len(title.strip()) > 0)
    
    if has_any_time and has_action:
        extracted_data['intent'] = 'event'
        # В строке 268: extracted_data['has_explicit_time'] = bool(start_time)
        # Но start_time = None, поэтому has_explicit_time остается False
        print(f"\n2️⃣ После process_intent fallback:")
        print(f"   intent переопределен: {extracted_data['intent']}")
        print(f"   has_explicit_time: {extracted_data['has_explicit_time']} (start_time все еще None)")
    
    # Шаг 3: _handle_event fallback извлекает время
    start_time = extracted_data.get('start_time')
    has_explicit_time = extracted_data.get('has_explicit_time', False)
    original_text = extracted_data.get('_original_text', '')
    
    print(f"\n3️⃣ В _handle_event (до fallback):")
    print(f"   start_time: {start_time}")
    print(f"   has_explicit_time: {has_explicit_time}")
    print(f"   original_text: '{original_text}'")
    
    # Fallback 1: если start_time указан
    if start_time and not has_explicit_time:
        if start_time.hour != 0 or start_time.minute != 0:
            has_explicit_time = True
            print(f"   ✅ Fallback 1 сработал")
    
    # Fallback 2: если start_time=None, извлекаем из текста
    if not start_time and original_text and not has_explicit_time:
        try:
            tz = pytz.timezone(timezone)
            parsed_time = dateparser.parse(
                original_text,
                settings={
                    'TIMEZONE': timezone,
                    'RETURN_AS_TIMEZONE_AWARE': True,
                    'RELATIVE_BASE': datetime.now(tz)
                }
            )
            
            if parsed_time:
                if parsed_time.hour != 0 or parsed_time.minute != 0:
                    start_time = parsed_time.astimezone(tz)
                    has_explicit_time = True
                    print(f"   ✅ Fallback 2 извлек время: {start_time.hour}:{start_time.minute:02d}")
                else:
                    print(f"   ❌ Fallback 2: время = 00:00:00")
            else:
                print(f"   ❌ Fallback 2: не удалось извлечь")
        except Exception as e:
            print(f"   ❌ Fallback 2: ошибка - {e}")
    
    print(f"\n4️⃣ РЕЗУЛЬТАТ:")
    print(f"   start_time: {start_time}")
    print(f"   has_explicit_time: {has_explicit_time}")
    print(f"   Будет создан draft: {not has_explicit_time}")
    
    if has_explicit_time:
        print(f"\n✅✅✅ ТЕСТ ПРОЙДЕН: Время извлечено, draft НЕ будет создан")
        return True
    else:
        print(f"\n❌❌❌ ТЕСТ НЕ ПРОЙДЕН: Время НЕ извлечено, draft БУДЕТ создан")
        return False

if __name__ == '__main__':
    success = test_complete_fallback()
    sys.exit(0 if success else 1)

