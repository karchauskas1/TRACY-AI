"""Модуль для обработки мультимедиа: STT для голоса, OCR для изображений."""
import io
import logging
import base64
from typing import Optional
from PIL import Image
import speech_recognition as sr
from telegram import Update
from telegram.ext import ContextTypes
import config

logger = logging.getLogger(__name__)

# Tesseract импортируется опционально
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

# OpenAI клиент для Vision API
try:
    from openai import OpenAI
    vision_client = OpenAI(
        api_key=config.OPENROUTER_API_KEY,
        base_url=config.OPENROUTER_BASE_URL
    )
    VISION_AVAILABLE = True
except Exception:
    vision_client = None
    VISION_AVAILABLE = False


class MediaProcessor:
    """Класс для конвертации медиа в текст."""
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
    
    async def process_voice(self, voice_file, language: str = "ru") -> Optional[str]:
        """
        Конвертировать голосовое сообщение в текст через Google Speech Recognition.
        
        Args:
            voice_file: Файл голосового сообщения из Telegram
            language: Язык для распознавания (по умолчанию русский)
        
        Returns:
            Распознанный текст или None при ошибке
        """
        try:
            # Скачать файл
            voice_io = io.BytesIO()
            await voice_file.download_to_memory(voice_io)
            voice_io.seek(0)
            
            # Используем Google Speech Recognition
            try:
                from pydub import AudioSegment
                
                # Пробуем определить формат и конвертируем в WAV
                # M4A ставим первым, так как это популярный формат iPhone диктофона
                voice_io.seek(0)
                audio_data = None
                supported_formats = ['m4a', 'mp3', 'wav', 'ogg', 'opus', 'flac', 'aac', 'wma', 'amr', '3gp', 'mka']
                
                # Пробуем разные форматы
                for fmt in supported_formats:
                    try:
                        voice_io.seek(0)
                        logger.debug(f"Пробую определить формат голосового как {fmt}...")
                        audio_data = AudioSegment.from_file(voice_io, format=fmt)
                        logger.info(f"✅ Определен формат аудио для распознавания: {fmt}")
                        break
                    except Exception as e:
                        logger.debug(f"Формат {fmt} не подошел: {str(e)[:50]}")
                        continue
                
                # Если не удалось определить, пробуем автоопределение
                if audio_data is None:
                    try:
                        voice_io.seek(0)
                        audio_data = AudioSegment.from_file(voice_io)
                        logger.info("Формат определен автоматически для распознавания")
                    except Exception as e:
                        logger.error(f"Не удалось определить формат аудио: {e}")
                        return None
                
                # Конвертируем в WAV для Google Speech Recognition
                # AudioFile требует файл на диске, не BytesIO
                import tempfile
                import os
                with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
                    audio_data.export(temp_file.name, format="wav")
                    temp_file_path = temp_file.name
                
                try:
                    # Используем WAV для распознавания
                    with sr.AudioFile(temp_file_path) as source:
                        self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                        audio = self.recognizer.record(source)
                
                    # Распознавание через Google Speech Recognition
                    text = self.recognizer.recognize_google(
                        audio, 
                        language=language if language != "ru" else "ru-RU"
                    )
                    
                    if text and text.strip():
                        logger.info(f"Распознан текст через Google: {text[:50]}...")
                        return text.strip()
                finally:
                    # Удаляем временный файл
                    if os.path.exists(temp_file_path):
                        os.unlink(temp_file_path)
                    
            except sr.UnknownValueError:
                logger.warning("Не удалось распознать речь (речь не распознана)")
                return None
            except sr.RequestError as e:
                logger.error(f"Ошибка сервиса распознавания речи: {e}")
                return None
            except Exception as e:
                logger.error(f"Ошибка обработки голоса через Google: {e}", exc_info=True)
                return None
            
            return None
        
        except Exception as e:
            logger.error(f"Ошибка обработки голоса: {e}", exc_info=True)
            return None
    
    async def process_image(self, photo_file, language: str = "rus") -> Optional[str]:
        """
        Извлечь текст из изображения с помощью Vision API или OCR.
        
        Args:
            photo_file: Файл изображения из Telegram
            language: Язык для OCR (rus, eng, etc.) - используется только для Tesseract fallback
        
        Returns:
            Извлеченный текст или None при ошибке
        """
        try:
            # Скачать файл
            image_io = io.BytesIO()
            await photo_file.download_to_memory(image_io)
            image_io.seek(0)
            
            # Сначала пробуем Vision API через OpenRouter (более надежно)
            if VISION_AVAILABLE and vision_client:
                try:
                    logger.info("Пробую извлечь текст через Vision API...")
                    
                    # Открываем и оптимизируем изображение перед кодированием
                    image_io.seek(0)
                    image = Image.open(image_io)
                    
                    # Оптимизируем изображение: уменьшаем размер для экономии токенов
                    max_size = 1024  # Максимальный размер по большей стороне
                    if image.width > max_size or image.height > max_size:
                        image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                        logger.info(f"Изображение уменьшено до {image.width}x{image.height}")
                    
                    # Конвертируем в RGB если нужно (для JPEG)
                    if image.mode != 'RGB':
                        image = image.convert('RGB')
                    
                    # Сохраняем в BytesIO с оптимизацией качества
                    optimized_io = io.BytesIO()
                    image.save(optimized_io, format='JPEG', quality=85, optimize=True)
                    optimized_io.seek(0)
                    
                    # Кодируем оптимизированное изображение в base64
                    base64_image = base64.b64encode(optimized_io.read()).decode('utf-8')
                    
                    format_map = {'JPEG': 'image/jpeg', 'PNG': 'image/png', 'WEBP': 'image/webp'}
                    image_format = 'image/jpeg'  # Всегда JPEG после оптимизации
                    
                    # Используем Vision API через OpenRouter
                    response = vision_client.chat.completions.create(
                        model="openai/gpt-4o-mini",  # Vision-модель
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": "Извлеки весь текст с этого изображения. Если это скриншот календаря, встречи или напоминания, опиши что там изображено, включая даты, время, названия событий. Верни только текст без дополнительных комментариев."
                                    },
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:{image_format};base64,{base64_image}"
                                        }
                                    }
                                ]
                            }
                        ],
                        max_tokens=500
                    )
                    
                    text = response.choices[0].message.content.strip()
                    
                    if text:
                        logger.info(f"Извлечен текст через Vision API: {text[:100]}...")
                        return text
                    
                except Exception as vision_error:
                    logger.warning(f"Vision API недоступен: {vision_error}, пробую Tesseract")
            
            # Fallback: используем Tesseract OCR
            if TESSERACT_AVAILABLE:
                try:
                    # Проверяем, что Tesseract установлен в системе
                    pytesseract.get_tesseract_version()
                    
                    image_io.seek(0)
                    image = Image.open(image_io)
                    
                    # OCR с помощью Tesseract
                    text = pytesseract.image_to_string(image, lang=language)
                    text = text.strip()
                    
                    if text:
                        logger.info(f"Извлечен текст через Tesseract: {text[:50]}...")
                        return text
                except Exception as tesseract_error:
                    logger.warning(f"Tesseract недоступен: {tesseract_error}")
            
            logger.warning("Не удалось извлечь текст из изображения ни одним способом")
            return None
        
        except Exception as e:
            logger.error(f"Ошибка обработки изображения: {e}", exc_info=True)
            return None
    
    async def extract_text_from_message(self, update: Update, bot=None) -> Optional[str]:
        """
        Извлечь текст из сообщения Telegram любого типа.
        
        Args:
            update: Update объект от Telegram
            bot: Bot объект для загрузки файлов (обязателен для голосовых/изображений)
        
        Returns:
            Текст из сообщения или None
        """
        try:
            # Для текстовых сообщений bot не нужен
            if update.message and update.message.text:
                logger.info("Обработка текстового сообщения")
                return update.message.text
            
            # Для медиа нужен bot
            if not bot:
                raise ValueError("Bot объект обязателен для обработки голосовых/изображений. Используйте context.bot")
            
            # Голосовое сообщение
            if update.message and update.message.voice:
                logger.info(f"Обнаружено голосовое сообщение, file_id: {update.message.voice.file_id}")
                voice = update.message.voice
                logger.info(f"Длительность: {voice.duration} сек, размер: {voice.file_size} bytes")
                
                try:
                    logger.info("Загружаю голосовой файл...")
                    voice_file = await bot.get_file(voice.file_id)
                    logger.info(f"Голосовой файл загружен, путь: {voice_file.file_path}")
                    
                    logger.info("Начинаю обработку голосового сообщения...")
                    result = await self.process_voice(voice_file)
                    
                    if result:
                        logger.info(f"Голосовое сообщение успешно обработано: {result[:50]}...")
                    else:
                        logger.warning("Голосовое сообщение обработано, но результат пустой")
                    
                    return result
                except Exception as e:
                    logger.error(f"Ошибка при загрузке/обработке голосового файла: {e}", exc_info=True)
                    raise
            
            # Изображение
            if update.message and update.message.photo:
                logger.info("Обработка изображения")
                # Берем самое большое изображение
                photo = update.message.photo[-1]
                photo_file = await bot.get_file(photo.file_id)
                return await self.process_image(photo_file)
            
            # Документ (изображение или аудио)
            if update.message and update.message.document:
                doc = update.message.document
                # Изображение
                if doc.mime_type and doc.mime_type.startswith('image/'):
                    logger.info("Обработка документа-изображения")
                    doc_file = await bot.get_file(doc.file_id)
                    return await self.process_image(doc_file)
                
                # Аудиофайл (для обычного режима - создание событий из голоса)
                # Проверяем по расширению и mime_type
                is_audio = False
                if doc.mime_type and 'audio' in doc.mime_type.lower():
                    is_audio = True
                elif doc.file_name:
                    audio_extensions = ['.mp3', '.m4a', '.wav', '.ogg', '.oga', '.opus', '.flac', '.aac', '.wma', '.amr', '.3gp', '.mka']
                    file_ext = doc.file_name.lower()
                    if any(file_ext.endswith(ext) for ext in audio_extensions):
                        is_audio = True
                
                if is_audio:
                    logger.info(f"Обнаружен аудиофайл в обычном режиме: {doc.file_name or 'без имени'}, mime_type: {doc.mime_type}")
                    try:
                        doc_file = await bot.get_file(doc.file_id)
                        logger.info("Загружаю аудиофайл...")
                        # Обрабатываем как голосовое сообщение
                        result = await self.process_voice(doc_file)
                        if result:
                            logger.info(f"Аудиофайл успешно обработан: {result[:50]}...")
                        return result
                    except Exception as e:
                        logger.error(f"Ошибка при обработке аудиофайла: {e}", exc_info=True)
                        raise
            
            logger.warning(f"Неизвестный тип сообщения: {type(update.message)}")
            return None
        
        except Exception as e:
            logger.error(f"Критическая ошибка в extract_text_from_message: {e}", exc_info=True)
            raise

