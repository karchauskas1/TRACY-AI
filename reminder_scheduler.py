"""Модуль для отправки напоминаний о событиях."""
import logging
import asyncio
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import pytz
from telegram.ext import ExtBot
from telegram.error import TelegramError
from database import Database
from openai import OpenAI
import config

logger = logging.getLogger(__name__)


class ReminderScheduler:
    """Класс для отправки напоминаний о событиях."""
    
    def __init__(self, bot: ExtBot, db: Database, ai_client: Optional[OpenAI] = None):
        self.bot = bot
        self.db = db
        self.running = False
        self.check_interval = 30  # Проверка каждые 30 секунд для более точной доставки
        self._task = None  # Храним ссылку на задачу
        self._morning_digest_last_check = {}  # {user_id: last_check_date} для отслеживания отправленных дайджестов
        # Инициализируем AI клиент для генерации мотивационных цитат
        if ai_client:
            self.ai_client = ai_client
        else:
            try:
                self.ai_client = OpenAI(
                    api_key=config.OPENROUTER_API_KEY,
                    base_url=config.OPENROUTER_BASE_URL
                )
            except Exception as e:
                logger.warning(f"Не удалось инициализировать AI клиент для утреннего дайджеста: {e}")
                self.ai_client = None
    
    async def start(self):
        """Запустить планировщик напоминаний."""
        if self.running:
            logger.warning("ReminderScheduler уже запущен")
            return
        
        self.running = True
        logger.info("Запуск ReminderScheduler...")
        
        # Запускаем фоновую задачу в фоне
        # Используем ensure_future для совместимости
        task = asyncio.ensure_future(self._check_reminders_loop())
        # Сохраняем ссылку на задачу, чтобы не потерять её
        self._task = task
        logger.info("✓ ReminderScheduler задача запущена")
    
    async def stop(self):
        """Остановить планировщик напоминаний."""
        self.running = False
        logger.info("Остановка ReminderScheduler...")
    
    async def _check_reminders_loop(self):
        """Основной цикл проверки напоминаний."""
        logger.info(f"✓ Цикл проверки напоминаний запущен (интервал: {self.check_interval} сек)")
        iteration = 0
        while self.running:
            try:
                iteration += 1
                if iteration % 20 == 0:  # Логируем каждые 20 итераций (каждые ~10 минут)
                    logger.info(f"✓ Планировщик работает, итерация #{iteration}")
                await self._check_and_send_reminders()
                # Проверяем утренний дайджест каждые 5 минут (iteration % 10)
                if iteration % 10 == 0:
                    await self._check_and_send_morning_digests()
            except asyncio.CancelledError:
                logger.info("Цикл проверки напоминаний отменен")
                break
            except Exception as e:
                logger.error(f"❌ Ошибка в цикле проверки напоминаний: {e}", exc_info=True)
            
            # Ждем перед следующей проверкой
            await asyncio.sleep(self.check_interval)
        
        logger.info("Цикл проверки напоминаний завершен")
    
    async def _check_and_send_reminders(self):
        """Проверить и отправить напоминания, которые должны быть отправлены сейчас."""
        try:
            # Получаем текущее время в UTC
            current_time = datetime.now(pytz.UTC)
            
            # Получаем ВСЕ неотправленные напоминания (фильтрация по времени происходит в get_pending_reminders)
            # Передаем текущее время + окно для просроченных (30 минут)
            threshold_time = current_time + timedelta(seconds=30)  # Небольшой буфер для задержек
            pending_reminders = self.db.get_pending_reminders(threshold_time)
            
            if not pending_reminders:
                # Логируем только каждую минуту, чтобы не спамить
                if not hasattr(self, '_last_log_time') or (current_time - self._last_log_time).total_seconds() > 60:
                    logger.debug(f"ℹ️ Нет напоминаний для отправки (время проверки: {current_time.isoformat()})")
                    self._last_log_time = current_time
                return
            
            # Дополнительная фильтрация: только те, которые уже наступили, но не старше 30 минут
            filtered_reminders = []
            for reminder in pending_reminders:
                reminder_time_str = reminder.get('reminder_time')
                if not reminder_time_str:
                    continue
                
                try:
                    # Парсим время напоминания (get_pending_reminders уже конвертировал в UTC)
                    if isinstance(reminder_time_str, str):
                        reminder_time_clean = reminder_time_str.replace('Z', '+00:00')
                        reminder_time = datetime.fromisoformat(reminder_time_clean)
                        if reminder_time.tzinfo is None:
                            reminder_time = pytz.UTC.localize(reminder_time)
                        elif reminder_time.tzinfo != pytz.UTC:
                            reminder_time = reminder_time.astimezone(pytz.UTC)
                    else:
                        reminder_time = reminder_time_str
                    
                    # Проверяем, что время напоминания уже наступило, но не старше 30 минут
                    time_diff = (current_time - reminder_time).total_seconds()
                    if -30 <= time_diff <= 1800:  # От -30 секунд до 30 минут
                        filtered_reminders.append(reminder)
                        if time_diff > 60:
                            logger.info(f"✓ Найдено напоминание {reminder['id']} (просрочено на {time_diff/60:.1f} мин): reminder_time={reminder_time.isoformat()}, current={current_time.isoformat()}")
                        else:
                            logger.info(f"✓ Найдено напоминание {reminder['id']}: reminder_time={reminder_time.isoformat()}, current={current_time.isoformat()}, diff={time_diff:.1f}с")
                    else:
                        if time_diff > 1800:
                            logger.debug(f"⏭️ Пропущено напоминание {reminder['id']} (слишком старое, {time_diff/60:.1f} мин)")
                        elif time_diff < -30:
                            logger.debug(f"⏭️ Пропущено напоминание {reminder['id']} (еще не наступило, через {-time_diff/60:.1f} мин)")
                except Exception as e:
                    logger.error(f"❌ Ошибка парсинга времени напоминания {reminder.get('id')}: {e}", exc_info=True)
                    continue
            
            pending_reminders = filtered_reminders
            
            if not pending_reminders:
                return
            
            logger.info(f"Найдено {len(pending_reminders)} напоминаний для отправки (время проверки: {current_time.isoformat()})")
            
            # Логируем детали для отладки
            for reminder in pending_reminders:
                reminder_time_str = reminder.get('reminder_time', 'N/A')
                event_title = reminder.get('title', 'N/A')
                logger.info(f"Напоминание для отправки: ID={reminder['id']}, время={reminder_time_str}, событие={event_title}")
            
            for reminder in pending_reminders:
                reminder_id = reminder.get('id')
                user_id = reminder.get('user_id')
                
                if not reminder_id:
                    logger.error(f"❌ Нет ID у напоминания: {reminder}")
                    continue
                
                if not user_id:
                    logger.error(f"❌ Нет user_id у напоминания {reminder_id}")
                    continue
                
                try:
                    logger.info(f"📤 Попытка отправить напоминание {reminder_id} пользователю {user_id}")
                    # Пытаемся отправить напоминание
                    await self._send_reminder(reminder)
                    
                    # Помечаем как отправленное ТОЛЬКО после успешной отправки
                    # Используем задержку, чтобы убедиться, что сообщение действительно отправлено
                    self.db.mark_reminder_sent(reminder_id)
                    logger.info(f"✅ Напоминание {reminder_id} успешно отправлено и помечено как отправленное пользователю {user_id}")
                    
                except Exception as e:
                    logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА отправки напоминания {reminder_id} пользователю {user_id}: {e}", exc_info=True)
                    # НЕ помечаем как отправленное при ошибке, чтобы попробовать снова
                    # Логируем детали ошибки для отладки
                    import traceback
                    logger.error(f"Трассировка ошибки отправки напоминания {reminder_id}:\n{traceback.format_exc()}")
                    # Продолжаем обработку следующих напоминаний
                    continue
        
        except Exception as e:
            logger.error(f"Ошибка проверки напоминаний: {e}", exc_info=True)
    
    async def _send_reminder(self, reminder: dict):
        """Отправить напоминание пользователю."""
        user_id = reminder.get('user_id')
        event_title = reminder.get('title', 'Событие')
        event_start_time_str = reminder.get('event_start_time')
        reminder_type = reminder.get('reminder_type', 'before')
        minutes_before = reminder.get('minutes_before')
        
        if not user_id:
            logger.error(f"❌ Нет user_id в напоминании {reminder.get('id')}")
            raise ValueError(f"Нет user_id в напоминании {reminder.get('id')}")
        
        logger.info(f"📤 Начало отправки напоминания {reminder.get('id')} пользователю {user_id}")
        
        try:
            # Парсим время начала события
            if isinstance(event_start_time_str, str):
                event_start_time = datetime.fromisoformat(event_start_time_str.replace('Z', '+00:00'))
            else:
                event_start_time = event_start_time_str
            
            # Формируем сообщение в зависимости от типа напоминания
            if reminder_type == 'before':
                # Напоминание за X времени до события
                if minutes_before:
                    if minutes_before >= 60:
                        hours = minutes_before // 60
                        time_str = f"{hours} {self._pluralize(hours, 'час', 'часа', 'часов')}"
                    else:
                        time_str = f"{minutes_before} {self._pluralize(minutes_before, 'минуту', 'минуты', 'минут')}"
                else:
                    time_str = "некоторое время"
                
                message = (
                    f"🔔 **Напоминание**\n\n"
                    f"Через {time_str} у тебя событие:\n\n"
                    f"📅 **{event_title}**\n"
                    f"🕐 {self._format_datetime(event_start_time)}"
                )
            else:
                # Напоминание о начале события
                message = (
                    f"⏰ **Событие начинается сейчас**\n\n"
                    f"📅 **{event_title}**\n"
                    f"🕐 {self._format_datetime(event_start_time)}"
                )
            
            # Добавляем дополнительную информацию, если есть
            if reminder.get('location'):
                message += f"\n📍 {reminder['location']}"
            
            if reminder.get('description'):
                desc = reminder['description']
                if len(desc) > 200:
                    desc = desc[:200] + "..."
                message += f"\n\n📝 {desc}"
            
            # Отправляем сообщение пользователю
            logger.info(f"Отправка сообщения пользователю {user_id} (chat_id={user_id}): {message[:100]}...")
            
            # Проверяем, что бот существует
            if not self.bot:
                error_msg = f"❌ Бот не инициализирован! Не могу отправить напоминание {reminder.get('id')}"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            try:
                # Пытаемся отправить сообщение
                result = await self.bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode="Markdown"
                )
                
                if result and result.message_id:
                    logger.info(f"✅ Сообщение успешно отправлено пользователю {user_id}, message_id: {result.message_id}")
                else:
                    logger.warning(f"⚠️ Сообщение отправлено, но result не содержит message_id: {result}")
                    
            except TelegramError as e:
                error_msg = f"❌ Telegram error при отправке напоминания {reminder.get('id')} пользователю {user_id}: {e}"
                logger.error(error_msg)
                logger.error(f"Тип ошибки: {type(e).__name__}")
                raise
            except Exception as e:
                error_msg = f"❌ Неожиданная ошибка при отправке сообщения пользователю {user_id}: {e}"
                logger.error(error_msg, exc_info=True)
                raise
        
        except Exception as e:
            logger.error(f"Ошибка отправки напоминания: {e}", exc_info=True)
            raise
    
    def _format_datetime(self, dt: datetime) -> str:
        """Форматирует дату и время для сообщения."""
        # Конвертируем в локальное время (Moscow)
        try:
            moscow_tz = pytz.timezone('Europe/Moscow')
            if dt.tzinfo is None:
                dt = pytz.UTC.localize(dt)
            local_dt = dt.astimezone(moscow_tz)
            
            # Формат: "Понедельник, 15 января 16:30"
            weekdays = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
            months = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
                     'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']
            
            weekday = weekdays[local_dt.weekday()]
            day = local_dt.day
            month = months[local_dt.month - 1]
            time_str = local_dt.strftime('%H:%M')
            
            return f"{weekday}, {day} {month} {time_str}"
        except:
            # Fallback на ISO формат
            return dt.strftime('%Y-%m-%d %H:%M')
    
    def _pluralize(self, num: int, one: str, few: str, many: str) -> str:
        """Правильное склонение для русского языка."""
        if num % 10 == 1 and num % 100 != 11:
            return one
        elif 2 <= num % 10 <= 4 and (num % 100 < 10 or num % 100 >= 20):
            return few
        else:
            return many
    
    def create_reminders_for_event(self, user_id: int, event_id: int, 
                                   event_start_time: datetime, 
                                   reminder_minutes: list = [15]) -> list:
        """
        Создать напоминания для события.
        
        Args:
            user_id: ID пользователя
            event_id: ID события
            event_start_time: Время начала события
            reminder_minutes: Список минут до события для напоминаний (например, [15, 60])
        
        Returns:
            Список созданных напоминаний
        """
        reminders = []
        
        # Убеждаемся, что event_start_time в UTC
        if event_start_time.tzinfo is None:
            event_start_time = pytz.UTC.localize(event_start_time)
        elif event_start_time.tzinfo != pytz.UTC:
            event_start_time = event_start_time.astimezone(pytz.UTC)
        
        current_time_utc = datetime.now(pytz.UTC)
        
        # Создаем напоминания за указанное время до события
        for minutes in reminder_minutes:
            reminder_time = event_start_time - timedelta(minutes=minutes)
            
            # Создаем напоминание только если время еще не прошло
            if reminder_time > current_time_utc:
                # Убеждаемся, что reminder_time в UTC
                if reminder_time.tzinfo is None:
                    reminder_time = pytz.UTC.localize(reminder_time)
                elif reminder_time.tzinfo != pytz.UTC:
                    reminder_time = reminder_time.astimezone(pytz.UTC)
                
                reminder_id = self.db.save_reminder(
                    user_id=user_id,
                    event_id=event_id,
                    reminder_time=reminder_time,
                    event_start_time=event_start_time,
                    reminder_type='before',
                    minutes_before=minutes
                )
                reminders.append(reminder_id)
                logger.info(f"Создано напоминание за {minutes} минут до события {event_id} (reminder_time: {reminder_time.isoformat()}, event_start: {event_start_time.isoformat()})")
        
        # Создаем напоминание о начале события (в момент начала)
        if event_start_time > current_time_utc:
            reminder_id = self.db.save_reminder(
                user_id=user_id,
                event_id=event_id,
                reminder_time=event_start_time,
                event_start_time=event_start_time,
                reminder_type='start',
                minutes_before=None
            )
            reminders.append(reminder_id)
            logger.info(f"✓ Создано напоминание о начале события {event_id} (reminder_time: {event_start_time.isoformat()}, event_start: {event_start_time.isoformat()})")
        else:
            logger.warning(f"⚠️ Не создано напоминание о начале события {event_id}: событие уже в прошлом (event_start_time: {event_start_time.isoformat()}, current: {current_time_utc.isoformat()})")
        
        logger.info(f"✓ Всего создано {len(reminders)} напоминаний для события {event_id}")
        return reminders
    
    async def _check_and_send_morning_digests(self):
        """Проверить и отправить утренние дайджесты для всех пользователей."""
        try:
            current_time_utc = datetime.now(pytz.UTC)
            # Получаем всех пользователей с включенными уведомлениями
            # Для простоты проверяем всех пользователей из БД
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            try:
                if self.db.use_postgresql:
                    cursor.execute("""
                        SELECT user_id, morning_digest_time, web_notifications_enabled, timezone
                        FROM users
                        WHERE morning_digest_time IS NOT NULL
                    """)
                else:
                    cursor.execute("""
                        SELECT user_id, morning_digest_time, web_notifications_enabled, timezone
                        FROM users
                        WHERE morning_digest_time IS NOT NULL
                    """)
                
                rows = cursor.fetchall()
                
                # Преобразуем результаты в словари для единообразной обработки
                users = []
                for row in rows:
                    if self.db.use_postgresql:
                        users.append(dict(row))
                    else:
                        # SQLite возвращает кортежи или Row объекты
                        users.append({
                            'user_id': row[0],
                            'morning_digest_time': row[1] if row[1] else '09:00',
                            'web_notifications_enabled': bool(row[2]) if row[2] is not None else True,
                            'timezone': row[3] if row[3] else 'Europe/Moscow'
                        })
                
                for user_row in users:
                    user_id = user_row['user_id']
                    digest_time_str = user_row.get('morning_digest_time', '09:00')
                    web_notifications_enabled = user_row.get('web_notifications_enabled', True)
                    user_timezone = user_row.get('timezone', 'Europe/Moscow')
                    
                    # Проверяем, включены ли уведомления (веб-настройки имеют приоритет)
                    if not web_notifications_enabled:
                        continue
                    
                    # Парсим время дайджеста (формат "HH:MM")
                    try:
                        digest_hour, digest_minute = map(int, digest_time_str.split(':'))
                    except:
                        digest_hour, digest_minute = 9, 0
                    
                    # Конвертируем текущее время в часовой пояс пользователя
                    try:
                        user_tz = pytz.timezone(user_timezone)
                        user_current_time = current_time_utc.astimezone(user_tz)
                    except:
                        user_tz = pytz.timezone('Europe/Moscow')
                        user_current_time = current_time_utc.astimezone(user_tz)
                    
                    # Проверяем, нужно ли отправить дайджест сейчас (в пределах 5 минут от заданного времени)
                    current_hour = user_current_time.hour
                    current_minute = user_current_time.minute
                    
                    # Проверяем, что мы в нужное время (с окном ±5 минут)
                    time_diff_minutes = (current_hour * 60 + current_minute) - (digest_hour * 60 + digest_minute)
                    if abs(time_diff_minutes) > 5:
                        continue
                    
                    # Проверяем, не отправляли ли мы уже дайджест сегодня
                    today_str = user_current_time.strftime('%Y-%m-%d')
                    last_check_key = f"{user_id}_{today_str}"
                    if last_check_key in self._morning_digest_last_check:
                        continue
                    
                    # Отправляем дайджест
                    await self._send_morning_digest(user_id, user_timezone, user_current_time)
                    self._morning_digest_last_check[last_check_key] = True
                    
                    # Очищаем старые записи (старше 2 дней)
                    keys_to_remove = [k for k in self._morning_digest_last_check.keys() 
                                     if not k.startswith(f"{user_id}_")]
                    for k in keys_to_remove:
                        del self._morning_digest_last_check[k]
                
            finally:
                cursor.close()
                self.db.return_connection(conn)
        
        except Exception as e:
            logger.error(f"Ошибка проверки утренних дайджестов: {e}", exc_info=True)
    
    async def _send_morning_digest(self, user_id: int, user_timezone: str, current_time: datetime):
        """Отправить утренний дайджест пользователю."""
        try:
            # Получаем события на сегодня
            start_of_day = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = current_time.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            # Конвертируем в UTC для запроса к БД
            start_of_day_utc = start_of_day.astimezone(pytz.UTC)
            end_of_day_utc = end_of_day.astimezone(pytz.UTC)
            
            events = self.db.get_events(user_id, limit=50, start_from=start_of_day_utc, start_to=end_of_day_utc)
            
            # Формируем список событий для сообщения
            if not events:
                message = (
                    "☀️ **Доброе утро!**\n\n"
                    "У тебя нет запланированных событий на сегодня. Отличный день для отдыха или спонтанных планов!"
                )
            else:
                # Генерируем мотивационную цитату на основе событий
                motivational_quote = await self._generate_motivational_quote(events, user_timezone)
                
                events_text = "**📅 События на сегодня:**\n\n"
                for event in events:
                    title = event.get('title', 'Без названия')
                    start_time = event.get('start_time')
                    if start_time:
                        if isinstance(start_time, str):
                            start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                        # Конвертируем в часовой пояс пользователя
                        if start_time.tzinfo:
                            start_time = start_time.astimezone(pytz.timezone(user_timezone))
                        time_str = start_time.strftime('%H:%M')
                        events_text += f"🕐 {time_str} - {title}\n"
                    else:
                        events_text += f"📅 {title}\n"
                
                message = (
                    f"☀️ **Доброе утро!**\n\n"
                    f"{motivational_quote}\n\n"
                    f"{events_text}"
                )
            
            # Отправляем сообщение
            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode="Markdown"
            )
            logger.info(f"✅ Утренний дайджест отправлен пользователю {user_id}")
        
        except Exception as e:
            logger.error(f"Ошибка отправки утреннего дайджеста пользователю {user_id}: {e}", exc_info=True)
    
    async def _generate_motivational_quote(self, events: List[Dict], timezone: str) -> str:
        """Генерирует контекстную мотивационную цитату на основе событий дня."""
        if not self.ai_client:
            return "У тебя сегодня отличный день! Всё будет супер!"
        
        try:
            # Формируем список событий для контекста
            events_summary = []
            for event in events[:10]:  # Берем первые 10 событий
                title = event.get('title', '')
                start_time = event.get('start_time')
                if start_time:
                    if isinstance(start_time, str):
                        start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    if start_time.tzinfo:
                        start_time = start_time.astimezone(pytz.timezone(timezone))
                    time_str = start_time.strftime('%H:%M')
                    events_summary.append(f"{time_str} - {title}")
                else:
                    events_summary.append(title)
            
            events_text = "\n".join(events_summary) if events_summary else "Нет событий"
            
            # Генерируем мотивационную цитату
            prompt = f"""Ты мотивационный ассистент. На основе событий пользователя на сегодня, создай короткую (2-3 предложения), позитивную и контекстную мотивационную цитату. 
            
События пользователя:
{events_text}

Цитата должна быть:
- Позитивной и мотивирующей
- Связанной с событиями (например, если есть спорт - упомяни об этом, если есть работа - поддержи, если есть развлечения - пожелай отлично провести время)
- Естественной на русском языке
- Без эмодзи в начале

Примеры:
- Если есть футбол и стрижка: "У тебя сегодня отличный день! Ты будешь свеж и активен, спорт - это жизнь! Следи за своим состоянием, ты красавчик!"
- Если есть работа: "Сегодня продуктивный день! Ты справишься со всеми задачами, главное - действовать!"
- Если есть отдых: "Сегодня день для восстановления сил! Наслаждайся моментом!"

Напиши только мотивационную цитату, без дополнительных комментариев."""
            
            response = self.ai_client.chat.completions.create(
                model=config.OPENROUTER_MODEL,
                messages=[
                    {"role": "system", "content": "Ты мотивационный ассистент. Создаешь короткие, позитивные и контекстные цитаты на основе событий пользователя."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=150
            )
            
            quote = response.choices[0].message.content.strip()
            return quote
        
        except Exception as e:
            logger.error(f"Ошибка генерации мотивационной цитаты: {e}", exc_info=True)
            return "У тебя сегодня отличный день! Всё будет супер!"

