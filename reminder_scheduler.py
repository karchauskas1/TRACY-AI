"""Модуль для отправки напоминаний о событиях."""
import logging
import asyncio
from typing import Optional
from datetime import datetime, timedelta
import pytz
from telegram.ext import ExtBot
from telegram.error import TelegramError
from database import Database
import config

logger = logging.getLogger(__name__)


class ReminderScheduler:
    """Класс для отправки напоминаний о событиях."""
    
    def __init__(self, bot: ExtBot, db: Database):
        self.bot = bot
        self.db = db
        self.running = False
        self.check_interval = 30  # Проверка каждые 30 секунд для более точной доставки
        self._task = None  # Храним ссылку на задачу
    
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

