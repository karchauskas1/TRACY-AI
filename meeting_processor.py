"""Модуль для обработки встреч и создания резюме из аудиозаписей."""
import io
import logging
import base64
import re
from typing import Optional, Dict, List, Tuple
from datetime import datetime
import speech_recognition as sr
from pydub import AudioSegment
import config

logger = logging.getLogger(__name__)

# OpenAI клиент для Whisper (высококачественная расшифровка)
try:
    from openai import OpenAI
    whisper_client = OpenAI(
        api_key=config.OPENROUTER_API_KEY,
        base_url=config.OPENROUTER_BASE_URL
    )
    WHISPER_AVAILABLE = True
except Exception:
    whisper_client = None
    WHISPER_AVAILABLE = False


class MeetingProcessor:
    """Класс для обработки встреч и создания резюме."""
    
    def __init__(self, nlp_client):
        """Инициализация с NLP клиентом для генерации резюме."""
        self.nlp_client = nlp_client
        self.recognizer = sr.Recognizer()
    
    async def transcribe_meeting_audio(self, audio_file, language: str = "ru") -> Optional[Dict]:
        """
        Расшифровать аудиозапись встречи с тайм-кодами.
        
        Args:
            audio_file: Файл аудио из Telegram
            language: Язык для распознавания
        
        Returns:
            Словарь с:
            - transcript: полная расшифровка с тайм-кодами
            - segments: список сегментов с временными метками
            - speakers: информация о спикерах (если определена)
        """
        try:
            # Скачиваем файл в память (правильный способ для python-telegram-bot)
            # Используем download_to_memory() как в media_processor.py
            audio_io = io.BytesIO()
            await audio_file.download_to_memory(audio_io)
            audio_io.seek(0)
            logger.info(f"Файл успешно загружен в память, размер: {len(audio_io.getvalue())} bytes")
            
            # Проверяем, что файл не пустой
            file_size = len(audio_io.getvalue())
            if file_size == 0:
                logger.error("Загруженный аудиофайл пуст")
                return None
            logger.info(f"Аудиофайл загружен, размер: {file_size} bytes")
            
            # Пробуем использовать Whisper API для качественной расшифровки
            if WHISPER_AVAILABLE and whisper_client:
                try:
                    logger.info("Используем Whisper API для расшифровки встречи...")
                    
                    # Определяем формат и конвертируем при необходимости
                    audio_io.seek(0)
                    
                    # Пробуем определить формат по содержимому файла
                    # M4A ставим первым, так как это популярный формат iPhone диктофона
                    audio_format = None
                    supported_formats = ['m4a', 'mp3', 'wav', 'ogg', 'opus', 'flac', 'aac', 'wma', 'amr', '3gp', 'mka']
                    
                    audio_data = None
                    for fmt in supported_formats:
                        try:
                            audio_io.seek(0)
                            logger.debug(f"Пробую определить формат как {fmt}...")
                            test_audio = AudioSegment.from_file(audio_io, format=fmt)
                            audio_format = fmt
                            logger.info(f"✅ Определен формат аудио: {fmt}")
                            
                            # Конвертируем в MP3 для Whisper (если не MP3 уже)
                            if fmt != 'mp3':
                                logger.info(f"Конвертирую {fmt} в MP3 для Whisper...")
                                converted_io = io.BytesIO()
                                test_audio.export(converted_io, format="mp3", bitrate="128k")
                                converted_io.seek(0)
                                audio_data = converted_io.read()
                                logger.info(f"✅ Конвертация {fmt} -> MP3 завершена, размер: {len(audio_data)} bytes")
                            else:
                                audio_io.seek(0)
                                audio_data = audio_io.read()
                            break
                        except Exception as e:
                            logger.debug(f"Формат {fmt} не подошел: {str(e)[:100]}")
                            continue
                    
                    # Если формат не определен, пробуем автоопределение
                    if not audio_format or not audio_data:
                        try:
                            audio_io.seek(0)
                            logger.info("Пробую автоопределение формата...")
                            test_audio = AudioSegment.from_file(audio_io)
                            converted_io = io.BytesIO()
                            test_audio.export(converted_io, format="mp3", bitrate="128k")
                            converted_io.seek(0)
                            audio_data = converted_io.read()
                            audio_format = "mp3"
                            logger.info("Формат определен автоматически, конвертировано в MP3")
                        except Exception as e:
                            logger.warning(f"Не удалось определить формат, используем как есть: {e}")
                            audio_io.seek(0)
                            audio_data = audio_io.read()
                            audio_format = "mp3"  # Пробуем как MP3
                    
                    # Используем Whisper для расшифровки с временными метками
                    import tempfile
                    import os
                    
                    # Определяем расширение для временного файла
                    suffix = f'.{audio_format}' if audio_format in ['mp3', 'wav', 'm4a'] else '.mp3'
                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                        temp_file.write(audio_data)
                        temp_file_path = temp_file.name
                    
                    try:
                        with open(temp_file_path, 'rb') as audio_file_obj:
                            # Определяем MIME тип в зависимости от формата
                            mime_type = 'audio/mpeg'
                            if audio_format == 'wav':
                                mime_type = 'audio/wav'
                            elif audio_format == 'm4a':
                                mime_type = 'audio/mp4'
                            elif audio_format in ['ogg', 'opus']:
                                mime_type = 'audio/ogg'
                            elif audio_format == 'flac':
                                mime_type = 'audio/flac'
                            
                            file_tuple = (os.path.basename(temp_file_path), audio_file_obj, mime_type)
                            
                            # Используем Whisper с временными метками
                            # Пробуем использовать verbose_json если доступен
                            try:
                                response = whisper_client.audio.transcriptions.create(
                                    model="openai/whisper-1",
                                    file=file_tuple,
                                    language=language if language != "ru-RU" else "ru",
                                    response_format="verbose_json",
                                    timestamp_granularities=["segment"]
                                )
                                
                                # Парсим результат с сегментами
                                if isinstance(response, dict):
                                    transcript = response.get('text', '')
                                    segments = response.get('segments', [])
                                elif hasattr(response, 'text') and hasattr(response, 'segments'):
                                    transcript = response.text
                                    segments = response.segments if hasattr(response, 'segments') else []
                                elif hasattr(response, 'text'):
                                    transcript = response.text
                                    segments = []
                                else:
                                    # Если формат другой, используем строковое представление
                                    transcript = str(response)
                                    segments = []
                            
                            except Exception as verbose_error:
                                # Fallback на обычный формат если verbose_json не поддерживается
                                logger.warning(f"Verbose JSON не поддерживается, используем обычный формат: {verbose_error}")
                                audio_file_obj.seek(0)
                                file_tuple = (os.path.basename(temp_file_path), audio_file_obj, mime_type)
                                response = whisper_client.audio.transcriptions.create(
                                    model="openai/whisper-1",
                                    file=file_tuple,
                                    language=language if language != "ru-RU" else "ru",
                                    response_format="text"
                                )
                                transcript = str(response).strip()
                                segments = []
                            
                            # Форматируем расшифровку с тайм-кодами (если есть сегменты)
                            if segments:
                                formatted_transcript = self._format_transcript_with_timestamps(transcript, segments)
                            else:
                                # Если нет сегментов, используем обычный текст, но разбиваем на абзацы
                                formatted_transcript = self._format_transcript_plain(transcript)
                            
                            # Определяем длительность
                            duration = 0
                            if segments and len(segments) > 0:
                                duration = segments[-1].get('end', 0) if isinstance(segments[-1], dict) else 0
                            
                            logger.info(f"Расшифровка завершена: {len(transcript)} символов, {len(segments)} сегментов, длительность: {duration}с")
                            
                            return {
                                'transcript': formatted_transcript,
                                'raw_text': transcript,
                                'segments': segments,
                                'duration': duration,
                                'language': language
                            }
                    finally:
                        if os.path.exists(temp_file_path):
                            os.unlink(temp_file_path)
                
                except Exception as whisper_error:
                    logger.warning(f"Whisper API недоступен: {whisper_error}, используем стандартное распознавание")
                    # Fallback на стандартное распознавание
                    return await self._transcribe_with_google(audio_io, language)
            else:
                # Используем Google Speech Recognition
                return await self._transcribe_with_google(audio_io, language)
        
        except Exception as e:
            logger.error(f"Критическая ошибка расшифровки аудио: {e}", exc_info=True)
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Пробуем fallback на Google Speech Recognition если Whisper не сработал
            try:
                if 'audio_io' in locals() and audio_io is not None:
                    logger.info("Пробую fallback на Google Speech Recognition...")
                    audio_io.seek(0)
                    return await self._transcribe_with_google(audio_io, language)
            except Exception as fallback_error:
                logger.error(f"Fallback на Google Speech также не сработал: {fallback_error}")
            return None
    
    def _format_transcript_with_timestamps(self, transcript: str, segments: List[Dict]) -> str:
        """Форматирует расшифровку с тайм-кодами."""
        if not segments:
            return self._format_transcript_plain(transcript)
        
        formatted_lines = []
        
        for segment in segments:
            start_time = self._format_timestamp(segment.get('start', 0))
            text = segment.get('text', '').strip()
            
            if not text:
                continue
            
            # Если есть информация о спикере, используем её
            speaker_info = ""
            if 'speaker' in segment:
                speaker_info = f"[Спикер {segment['speaker']}] "
            elif 'speaker_id' in segment:
                speaker_info = f"[Спикер {segment['speaker_id']}] "
            
            formatted_lines.append(f"{start_time} {speaker_info}{text}")
        
        return "\n\n".join(formatted_lines)
    
    def _format_transcript_plain(self, transcript: str) -> str:
        """Форматирует расшифровку без тайм-кодов, разбивая на абзацы."""
        # Разбиваем текст на предложения и группируем в абзацы
        import re
        sentences = re.split(r'([.!?]+)\s+', transcript)
        
        # Объединяем предложения обратно
        text = transcript
        # Простая замена точек на абзацы для лучшей читаемости
        text = re.sub(r'\. ([А-Я])', r'.\n\n\1', text)
        return text
    
    def _format_timestamp(self, seconds: float) -> str:
        """Форматирует время в формат MM:SS или HH:MM:SS."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"
    
    async def _transcribe_with_google(self, audio_io: io.BytesIO, language: str) -> Optional[Dict]:
        """Fallback расшифровка через Google Speech Recognition."""
        try:
            logger.info("Начинаю расшифровку через Google Speech Recognition...")
            
            # Пробуем определить формат и конвертируем в WAV
            audio_io.seek(0)
            
            # Поддерживаемые форматы для pydub
            # M4A ставим первым, так как это популярный формат iPhone диктофона
            supported_formats = ['m4a', 'mp3', 'wav', 'ogg', 'opus', 'flac', 'aac', 'wma', 'amr', '3gp', 'mka']
            audio_data = None
            
            for fmt in supported_formats:
                try:
                    audio_io.seek(0)
                    logger.debug(f"Пробую определить формат для Google Speech как {fmt}...")
                    audio_data = AudioSegment.from_file(audio_io, format=fmt)
                    logger.info(f"✅ Определен формат для Google Speech: {fmt}, длительность: {len(audio_data)/1000:.1f} сек")
                    break
                except Exception as e:
                    logger.debug(f"Формат {fmt} не подошел для Google Speech: {str(e)[:100]}")
                    continue
            
            # Если не удалось определить, пробуем автоопределение
            if audio_data is None:
                try:
                    audio_io.seek(0)
                    logger.info("Пробую автоопределение формата для Google Speech...")
                    audio_data = AudioSegment.from_file(audio_io)
                    logger.info("Формат определен автоматически для Google Speech")
                except Exception as e:
                    logger.error(f"Не удалось определить формат аудио для Google Speech: {e}")
                    return None
            
            # Конвертируем в WAV для Google Speech Recognition
            # Создаем временный файл, так как sr.AudioFile требует реальный файл
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_wav:
                audio_data.export(temp_wav.name, format="wav")
                temp_wav_path = temp_wav.name
            
            try:
                # Проверяем, что recognizer инициализирован
                if not hasattr(self, 'recognizer') or self.recognizer is None:
                    logger.warning("recognizer не инициализирован, создаю новый...")
                    self.recognizer = sr.Recognizer()
                
                # Используем WAV файл для распознавания
                logger.info("Начинаю распознавание через Google Speech Recognition...")
                with sr.AudioFile(temp_wav_path) as source:
                    # Для длинных аудио делаем минимальную настройку шума
                    duration_seconds = len(audio_data) / 1000.0
                    noise_duration = min(1.0, duration_seconds / 10)  # Не более 1 секунды или 10% от длительности
                    self.recognizer.adjust_for_ambient_noise(source, duration=noise_duration)
                    audio = self.recognizer.record(source)
                
                logger.info(f"Аудио записано, отправляю в Google Speech Recognition...")
                text = self.recognizer.recognize_google(
                    audio,
                    language=language if language != "ru" else "ru-RU"
                )
                
                logger.info(f"Распознавание завершено. Длина текста: {len(text)} символов")
                
                return {
                    'transcript': text,
                    'raw_text': text,
                    'segments': [],
                    'duration': duration_seconds,
                    'language': language
                }
            finally:
                # Удаляем временный файл
                if os.path.exists(temp_wav_path):
                    try:
                        os.unlink(temp_wav_path)
                    except Exception as e:
                        logger.warning(f"Не удалось удалить временный файл: {e}")
        except sr.UnknownValueError:
            logger.warning("Google Speech Recognition не смог распознать речь")
            return None
        except sr.RequestError as e:
            logger.error(f"Ошибка запроса к Google Speech Recognition: {e}")
            return None
        except Exception as e:
            logger.error(f"Критическая ошибка расшифровки через Google: {e}", exc_info=True)
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None
    
    async def generate_meeting_summary(self, transcript: str, raw_text: str, language: str = "ru") -> Optional[str]:
        """
        Генерирует структурированное резюме встречи.
        
        Args:
            transcript: Полная расшифровка с тайм-кодами
            raw_text: Чистый текст без тайм-кодов
            language: Язык
        
        Returns:
            Структурированное резюме в виде текста
        """
        try:
            prompt = f"""Проанализируй расшифровку встречи и создай структурированное резюме на русском языке.

Расшифровка встречи:
{raw_text[:8000]}

Создай резюме в следующем формате:

**📋 Краткое резюме встречи**
На встрече обсуждалось: [3-5 предложений естественным языком о сути встречи, что было обсуждено, какие вопросы поднимались]

**📝 Основные темы**
• [Список основных тем, которые обсуждались, в виде маркированного списка]

**✅ Договорённости и решения**
• [Список принятых решений и договорённостей, если были]

**📌 Задачи и следующие шаги**
• [Список задач, которые нужно выполнить, с указанием ответственных, если упоминались]

**📅 Даты, дедлайны и события**
• [Все упоминания дат, дедлайнов, встреч и событий, если были]

ВАЖНО:
- Краткое описание должно начинаться с "На встрече обсуждалось:" и быть написано естественным языком, без шаблонов
- Заголовок "Краткое резюме встречи" должен быть жирным (используй **)
- Резюме должно быть полезным и структурированным, не просто пересказом. Выделяй самое важное."""
            
            response = self.nlp_client.chat.completions.create(
                model="openai/gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "Ты профессиональный ассистент для анализа встреч. Создавай структурированные, полезные резюме, выделяя ключевую информацию."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            summary = response.choices[0].message.content.strip()
            return summary
        
        except Exception as e:
            logger.error(f"Ошибка генерации резюме: {e}", exc_info=True)
            return None
    
    async def generate_extended_summary(self, transcript: str, raw_text: str, language: str = "ru") -> Optional[str]:
        """Генерирует расширенное резюме встречи."""
        try:
            prompt = f"""Проанализируй расшифровку встречи и создай подробное расширенное резюме на русском языке.

Расшифровка встречи:
{raw_text[:12000]}

Создай подробное резюме, включающее:
- Детальное описание встречи (5-8 предложений)
- Все обсуждаемые темы с подробностями
- Все договорённости и решения с контекстом
- Все задачи с приоритетами и ответственными
- Все даты, дедлайны и события
- Важные детали и нюансы обсуждения
- Любые упоминания людей, проектов, документов

Форматируй структурированно с заголовками и списками."""
            
            response = self.nlp_client.chat.completions.create(
                model="openai/gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "Ты профессиональный ассистент для анализа встреч. Создавай подробные, структурированные резюме с максимальной полезностью."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=2500
            )
            
            summary = response.choices[0].message.content.strip()
            return summary
        
        except Exception as e:
            logger.error(f"Ошибка генерации расширенного резюме: {e}", exc_info=True)
            return None
    
    async def extract_events_from_meeting(self, summary: str, transcript: str, 
                                         user_timezone: str = "Europe/Moscow") -> List[Dict]:
        """
        Извлекает события из резюме и расшифровки для создания в календаре.
        
        Args:
            summary: Резюме встречи
            transcript: Полная расшифровка
            user_timezone: Часовой пояс пользователя
        
        Returns:
            Список словарей с данными событий
        """
        try:
            prompt = f"""Проанализируй резюме и расшифровку встречи и извлеки все события, встречи, дедлайны и напоминания для добавления в календарь.

Резюме:
{summary}

Полная расшифровка:
{transcript[:4000]}

Текущая дата и время: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Часовой пояс: {user_timezone}

Верни JSON массив событий в формате:
{{
    "events": [
        {{
            "title": "название события",
            "description": "описание",
            "start_time": "YYYY-MM-DDTHH:MM:SS или null (время начала события)",
            "end_time": "YYYY-MM-DDTHH:MM:SS или null (время окончания события, если указан диапазон)",
            "location": "место или null",
            "priority": 0-5,
            "has_explicit_time": true/false
        }}
    ]
}}

ВАЖНО для диапазонов времени:
- Если указан диапазон времени ("с 11 утра до 15 часов", "с 10:00 до 14:00", "11:00-15:00", "от X до Y"), извлекай оба времени: start_time (начало) и end_time (окончание)
- Примеры: "зарядка с 11 утра до 15 часов" → start_time="11:00", end_time="15:00" (на ту же дату)
          "встреча завтра с 10:00 до 12:00" → start_time="завтра 10:00", end_time="завтра 12:00"

Извлекай только события с конкретными датами/временем. Если дата не указана явно, но есть относительная (например, "через неделю"), вычисляй конкретную дату. Если дата не определена, не включай событие."""
            
            response = self.nlp_client.chat.completions.create(
                model="openai/gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "Ты ассистент для извлечения событий из текста. Извлекай только события с конкретными датами. Верни только валидный JSON без дополнительного текста."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                response_format={"type": "json_object"},
                max_tokens=2000
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            events = result.get('events', [])
            
            # Парсим даты
            import pytz
            import dateparser
            tz = pytz.timezone(user_timezone)
            now = datetime.now(tz)
            
            parsed_events = []
            for event in events:
                # Пропускаем события без start_time
                if not event.get('start_time') or event['start_time'] == 'null' or event['start_time'] is None:
                    logger.info(f"Пропускаем событие без start_time: {event.get('title', 'Без названия')}")
                    continue
                
                try:
                    # Парсим start_time
                    start_time_str = event.get('start_time')
                    
                    # Если уже datetime объект
                    if isinstance(start_time_str, datetime):
                        parsed_start = start_time_str
                    # Если None или 'null'
                    elif not start_time_str or start_time_str == 'null' or str(start_time_str).lower() == 'null':
                        logger.info(f"Пропускаем событие без start_time: {event.get('title', 'Без названия')}")
                        continue
                    # Пробуем ISO формат сначала
                    elif 'T' in str(start_time_str) or '-' in str(start_time_str):
                        try:
                            from dateutil import parser as dateutil_parser
                            parsed_start = dateutil_parser.parse(str(start_time_str))
                        except:
                            # Fallback на dateparser
                            parsed_start = dateparser.parse(
                                str(start_time_str),
                                settings={
                                    'TIMEZONE': user_timezone,
                                    'RETURN_AS_TIMEZONE_AWARE': True,
                                    'RELATIVE_BASE': now
                                }
                            )
                    else:
                        # Используем dateparser для естественного языка
                        parsed_start = dateparser.parse(
                            str(start_time_str),
                            settings={
                                'TIMEZONE': user_timezone,
                                'RETURN_AS_TIMEZONE_AWARE': True,
                                'RELATIVE_BASE': now
                            }
                        )
                    
                    if not parsed_start:
                        logger.warning(f"Не удалось распарсить start_time '{start_time_str}' для события: {event.get('title', 'Без названия')}")
                        continue
                    
                    # Убеждаемся что дата в правильном timezone
                    if parsed_start.tzinfo is None:
                        parsed_start = tz.localize(parsed_start)
                    else:
                        parsed_start = parsed_start.astimezone(tz)
                    
                    event['start_time'] = parsed_start
                except Exception as e:
                    logger.error(f"Ошибка парсинга start_time: {e}, событие: {event.get('title', 'Без названия')}, start_time_str: {start_time_str}", exc_info=True)
                    continue
                
                # Парсим end_time если есть
                if event.get('end_time') and event['end_time'] != 'null':
                    try:
                        end_time_str = event.get('end_time')
                        if isinstance(end_time_str, datetime):
                            parsed_end = end_time_str
                        else:
                            parsed_end = dateparser.parse(
                                str(end_time_str),
                                settings={
                                    'TIMEZONE': user_timezone,
                                    'RETURN_AS_TIMEZONE_AWARE': True,
                                    'RELATIVE_BASE': now
                                }
                            )
                        
                        if parsed_end:
                            event['end_time'] = parsed_end.astimezone(tz) if parsed_end.tzinfo else tz.localize(parsed_end)
                        else:
                            event['end_time'] = None
                    except Exception as e:
                        logger.warning(f"Ошибка парсинга end_time: {e}")
                        event['end_time'] = None
                else:
                    event['end_time'] = None
                
                # Если есть start_time, но нет end_time, добавляем час по умолчанию
                if event.get('start_time') and not event.get('end_time'):
                    from datetime import timedelta
                    event['end_time'] = event['start_time'] + timedelta(hours=1)
                
                parsed_events.append(event)
            
            logger.info(f"Извлечено {len(parsed_events)} событий из встречи")
            return parsed_events
        
        except Exception as e:
            logger.error(f"Ошибка извлечения событий: {e}", exc_info=True)
            return []

