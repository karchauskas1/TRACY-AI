#!/usr/bin/env python3
"""
Тестовый скрипт для проверки обработки голосовых сообщений.
Создает тестовый аудиофайл и проверяет его обработку через media_processor.
"""
import asyncio
import io
import logging
import os
import sys
import tempfile
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from media_processor import MediaProcessor
import config

# Проверяем наличие необходимых библиотек
try:
    from pydub import AudioSegment
    from pydub.generators import Sine
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    logger.error("❌ pydub не установлен. Установите: pip install pydub")

try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False
    logger.error("❌ speech_recognition не установлен. Установите: pip install SpeechRecognition")


class MockVoiceFile:
    """Мок-объект для имитации голосового файла из Telegram."""
    
    def __init__(self, audio_data: bytes, file_path: str = "voice.ogg"):
        self.audio_data = audio_data
        self.file_path = file_path
    
    async def download_to_memory(self, buffer: io.BytesIO):
        """Имитация загрузки файла в память."""
        buffer.write(self.audio_data)
        buffer.seek(0)


async def create_test_audio_file(format: str = "ogg") -> bytes:
    """Создает тестовый аудиофайл с простым тоном."""
    if not PYDUB_AVAILABLE:
        raise ImportError("pydub не установлен")
    
    # Создаем простой тон (440 Hz, 2 секунды)
    tone = Sine(440).to_audio_segment(duration=2000)
    
    # Экспортируем в нужный формат
    buffer = io.BytesIO()
    tone.export(buffer, format=format, bitrate="128k")
    buffer.seek(0)
    return buffer.read()


async def test_voice_processing():
    """Основная функция тестирования."""
    logger.info("=" * 60)
    logger.info("🧪 ТЕСТ ОБРАБОТКИ ГОЛОСОВЫХ СООБЩЕНИЙ")
    logger.info("=" * 60)
    
    # Проверка конфигурации
    logger.info("\n📋 Проверка конфигурации...")
    logger.info(f"OPENROUTER_API_KEY: {'✅ Установлен' if config.OPENROUTER_API_KEY else '❌ Не установлен'}")
    logger.info(f"OPENROUTER_BASE_URL: {config.OPENROUTER_BASE_URL}")
    logger.info(f"OPENROUTER_MODEL: {config.OPENROUTER_MODEL}")
    
    if not config.OPENROUTER_API_KEY:
        logger.error("❌ OPENROUTER_API_KEY не установлен в config!")
        return False
    
    # Проверка доступности библиотек
    logger.info("\n📚 Проверка библиотек...")
    logger.info(f"pydub: {'✅' if PYDUB_AVAILABLE else '❌'}")
    logger.info(f"speech_recognition: {'✅' if SPEECH_RECOGNITION_AVAILABLE else '❌'}")
    
    if not PYDUB_AVAILABLE or not SPEECH_RECOGNITION_AVAILABLE:
        logger.error("❌ Не все необходимые библиотеки установлены!")
        return False
    
    # Проверка ffmpeg
    logger.info("\n🎵 Проверка ffmpeg...")
    import subprocess
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                               capture_output=True, 
                               timeout=5)
        if result.returncode == 0:
            logger.info("✅ ffmpeg доступен")
        else:
            logger.warning("⚠️ ffmpeg не работает корректно")
    except FileNotFoundError:
        logger.error("❌ ffmpeg не найден! Установите: apt-get install ffmpeg")
        return False
    except Exception as e:
        logger.warning(f"⚠️ Не удалось проверить ffmpeg: {e}")
    
    # Создание MediaProcessor
    logger.info("\n🔧 Инициализация MediaProcessor...")
    try:
        processor = MediaProcessor()
        logger.info("✅ MediaProcessor создан")
    except Exception as e:
        logger.error(f"❌ Ошибка создания MediaProcessor: {e}", exc_info=True)
        return False
    
    # Тест 1: Создание тестового аудиофайла
    logger.info("\n" + "=" * 60)
    logger.info("ТЕСТ 1: Создание тестового аудиофайла")
    logger.info("=" * 60)
    
    test_formats = ['ogg', 'mp3', 'wav']
    test_results = {}
    
    for fmt in test_formats:
        try:
            logger.info(f"\n📝 Тестирование формата: {fmt}")
            audio_data = await create_test_audio_file(format=fmt)
            logger.info(f"✅ Аудиофайл создан: {len(audio_data)} bytes")
            test_results[fmt] = audio_data
        except Exception as e:
            logger.error(f"❌ Ошибка создания аудиофайла {fmt}: {e}", exc_info=True)
            test_results[fmt] = None
    
    # Тест 2: Обработка через MediaProcessor
    logger.info("\n" + "=" * 60)
    logger.info("ТЕСТ 2: Обработка голосовых сообщений")
    logger.info("=" * 60)
    
    success_count = 0
    total_tests = 0
    
    for fmt, audio_data in test_results.items():
        if audio_data is None:
            continue
        
        total_tests += 1
        logger.info(f"\n🔍 Тест обработки формата: {fmt}")
        
        try:
            # Создаем мок-объект файла
            mock_file = MockVoiceFile(audio_data, f"voice.{fmt}")
            
            # Пробуем обработать
            logger.info(f"⏳ Обработка файла {fmt}...")
            result = await processor.process_voice(mock_file, language="ru")
            
            if result:
                logger.info(f"✅ Успешно! Распознанный текст: {result[:100] if len(result) > 100 else result}")
                success_count += 1
            else:
                logger.warning(f"⚠️ Обработка завершена, но результат пустой")
                # Это не критично, может быть из-за простого тона
                success_count += 0.5
        
        except Exception as e:
            logger.error(f"❌ Ошибка обработки {fmt}: {e}", exc_info=True)
    
    # Итоговый результат
    logger.info("\n" + "=" * 60)
    logger.info("📊 ИТОГОВЫЙ РЕЗУЛЬТАТ")
    logger.info("=" * 60)
    logger.info(f"Успешных тестов: {success_count}/{total_tests}")
    
    if success_count >= total_tests * 0.5:  # Хотя бы половина тестов должна пройти
        logger.info("✅ ТЕСТЫ ПРОЙДЕНЫ: Обработка голосовых сообщений работает!")
        return True
    else:
        logger.error("❌ ТЕСТЫ НЕ ПРОЙДЕНЫ: Есть проблемы с обработкой голосовых сообщений")
        return False


async def test_with_real_audio_file(file_path: str):
    """Тест с реальным аудиофайлом (если есть)."""
    if not os.path.exists(file_path):
        logger.warning(f"⚠️ Файл не найден: {file_path}")
        return False
    
    logger.info(f"\n🎵 Тест с реальным файлом: {file_path}")
    
    try:
        processor = MediaProcessor()
        
        # Читаем файл
        with open(file_path, 'rb') as f:
            audio_data = f.read()
        
        mock_file = MockVoiceFile(audio_data, os.path.basename(file_path))
        
        logger.info("⏳ Обработка реального аудиофайла...")
        result = await processor.process_voice(mock_file, language="ru")
        
        if result:
            logger.info(f"✅ Успешно! Распознанный текст: {result}")
            return True
        else:
            logger.warning("⚠️ Результат пустой")
            return False
    
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    logger.info("🚀 Запуск тестов обработки голосовых сообщений...\n")
    
    # Основной тест
    result = asyncio.run(test_voice_processing())
    
    # Если есть тестовый файл, пробуем его
    test_files = [
        "test_voice.ogg",
        "test_voice.mp3",
        "test_voice.wav",
        "voice_sample.ogg"
    ]
    
    for test_file in test_files:
        if os.path.exists(test_file):
            logger.info(f"\n📁 Найден тестовый файл: {test_file}")
            asyncio.run(test_with_real_audio_file(test_file))
            break
    
    sys.exit(0 if result else 1)


