#!/usr/bin/env python3
"""Тест fallback логики извлечения времени."""
import sys
sys.path.insert(0, '.')

from datetime import datetime
import dateparser
import pytz

def test_time_extraction():
    """Тестирует извлечение времени из текста."""
    test_cases = [
        ('сегодня в 12:30 стрижка', True),
        ('завтра в 15:40 футбол', True),
        ('в 12:00 встреча', True),
        ('сегодня стрижка', False),  # Нет времени
        ('стрижка', False),  # Нет времени и даты
    ]
    
    timezone = 'Europe/Moscow'
    tz = pytz.timezone(timezone)
    
    print("🧪 Тестирование fallback логики извлечения времени:\n")
    
    for text, expected_has_time in test_cases:
        try:
            parsed_time = dateparser.parse(
                text,
                settings={
                    'TIMEZONE': timezone,
                    'RETURN_AS_TIMEZONE_AWARE': True,
                    'RELATIVE_BASE': datetime.now(tz)
                }
            )
            
            if parsed_time:
                has_time = (parsed_time.hour != 0 or parsed_time.minute != 0)
                status = "✅" if has_time == expected_has_time else "❌"
                print(f"{status} '{text}' -> {parsed_time} (has_time={has_time}, expected={expected_has_time})")
            else:
                status = "✅" if not expected_has_time else "❌"
                print(f"{status} '{text}' -> None (expected_has_time={expected_has_time})")
        except Exception as e:
            print(f"❌ '{text}' -> Ошибка: {e}")

if __name__ == '__main__':
    test_time_extraction()

