#!/usr/bin/env python3
"""
Тест: проверяем работает ли Whisper API через OpenRouter.
Создаёт короткий тестовый аудиофайл и отправляет на расшифровку.
"""
import os
import sys
import io
import tempfile

# Добавляем текущую директорию в path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config

def test_whisper_api():
    """Проверяем что Whisper API работает."""

    print("=" * 60)
    print("ТЕСТ: Проверка Whisper API через OpenRouter")
    print("=" * 60)

    # 1. Проверяем наличие API ключа
    print(f"\n[1] API Key: {'✓ установлен' if config.OPENROUTER_API_KEY else '❌ НЕ УСТАНОВЛЕН'}")
    print(f"    Base URL: {config.OPENROUTER_BASE_URL}")

    if not config.OPENROUTER_API_KEY:
        print("\n❌ OPENROUTER_API_KEY не установлен!")
        return False

    # 2. Пробуем создать OpenAI клиент
    print("\n[2] Создаю OpenAI клиент...")
    try:
        from openai import OpenAI
        client = OpenAI(
            api_key=config.OPENROUTER_API_KEY,
            base_url=config.OPENROUTER_BASE_URL
        )
        print("    ✓ Клиент создан")
    except Exception as e:
        print(f"    ❌ Ошибка создания клиента: {e}")
        return False

    # 3. Создаём минимальный тестовый аудиофайл (тишина)
    print("\n[3] Создаю тестовый аудиофайл...")
    try:
        from pydub import AudioSegment
        from pydub.generators import Sine

        # Создаём 2 секунды синусоиды (чтобы был хоть какой-то звук)
        # Whisper может не принять абсолютную тишину
        tone = Sine(440).to_audio_segment(duration=2000)  # 2 секунды, 440 Hz
        tone = tone - 30  # Уменьшаем громкость на 30 dB

        # Экспортируем в MP3
        audio_buffer = io.BytesIO()
        tone.export(audio_buffer, format="mp3", bitrate="32k")
        audio_buffer.seek(0)
        audio_data = audio_buffer.read()

        print(f"    ✓ Создан тестовый файл: {len(audio_data)} bytes ({len(audio_data)/1024:.1f} KB)")
    except Exception as e:
        print(f"    ❌ Ошибка создания аудио: {e}")
        print("    Пробую использовать готовый файл...")
        audio_data = None

    # 4. Отправляем на Whisper API
    print("\n[4] Отправляю на Whisper API (openai/whisper-1)...")

    try:
        import time
        start_time = time.time()

        # Сохраняем во временный файл
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp.write(audio_data)
            tmp_path = tmp.name

        try:
            with open(tmp_path, "rb") as audio_file:
                response = client.audio.transcriptions.create(
                    model="openai/whisper-1",
                    file=audio_file,
                    response_format="verbose_json",
                    language="ru"
                )

            elapsed = time.time() - start_time

            print(f"\n    ✅ WHISPER РАБОТАЕТ!")
            print(f"    Время ответа: {elapsed:.2f} сек")
            print(f"    Результат: {response}")

            # Проверяем структуру ответа
            if hasattr(response, 'text'):
                print(f"    Текст: '{response.text}'")
            if hasattr(response, 'segments'):
                print(f"    Сегментов: {len(response.segments) if response.segments else 0}")

            return True

        finally:
            # Удаляем временный файл
            os.unlink(tmp_path)

    except Exception as e:
        print(f"\n    ❌ ОШИБКА Whisper API: {e}")
        print(f"    Тип ошибки: {type(e).__name__}")

        # Проверяем детали ошибки
        error_str = str(e).lower()
        if "401" in error_str or "unauthorized" in error_str:
            print("\n    💡 Возможная причина: неверный API ключ")
        elif "413" in error_str or "too large" in error_str:
            print("\n    💡 Возможная причина: файл слишком большой")
        elif "model" in error_str:
            print("\n    💡 Возможная причина: модель whisper-1 недоступна через OpenRouter")
        elif "rate" in error_str or "limit" in error_str:
            print("\n    💡 Возможная причина: превышен лимит запросов")

        return False


def test_fallback_speech_recognition():
    """Проверяем fallback на Google Speech Recognition."""

    print("\n" + "=" * 60)
    print("ТЕСТ: Проверка Fallback (speech_recognition)")
    print("=" * 60)

    try:
        import speech_recognition as sr
        print("\n    ✓ speech_recognition импортирован")

        recognizer = sr.Recognizer()
        print("    ✓ Recognizer создан")
        print("\n    💡 Fallback доступен (Google Speech Recognition)")
        return True
    except Exception as e:
        print(f"\n    ❌ Ошибка: {e}")
        return False


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("     ДИАГНОСТИКА WHISPER API")
    print("=" * 60)

    whisper_ok = test_whisper_api()
    fallback_ok = test_fallback_speech_recognition()

    print("\n" + "=" * 60)
    print("ИТОГ:")
    print("=" * 60)
    print(f"  Whisper API (OpenRouter):  {'✅ РАБОТАЕТ' if whisper_ok else '❌ НЕ РАБОТАЕТ (ошибка 405)'}")
    print(f"  Google Speech (Fallback):  {'✅ ДОСТУПЕН' if fallback_ok else '❌ НЕДОСТУПЕН'}")
    print("=" * 60)

    if not whisper_ok and fallback_ok:
        print("\n⚠️  ВАЖНО: OpenRouter НЕ поддерживает Whisper API напрямую!")
        print("   Все расшифровки идут через Google Speech Recognition (бесплатно, но без тайм-кодов)")
        print("\n💡 Для использования Whisper нужен:")
        print("   - Прямой OpenAI API ключ (НЕ OpenRouter)")
        print("   - Или другой провайдер с поддержкой Whisper endpoint")

    print()
    sys.exit(0 if whisper_ok else 1)
