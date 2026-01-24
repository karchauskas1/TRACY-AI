"""
==============================================================================
CONTAINER.PY - DEPENDENCY INJECTION КОНТЕЙНЕР
==============================================================================

Централизованное управление зависимостями приложения.
Заменяет глобальные переменные в bot.py на управляемые зависимости.

ИСПОЛЬЗОВАНИЕ:
    from tracy.core.container import Container

    # Создание контейнера
    container = Container.create()

    # Доступ к сервисам
    db = container.database
    nlp = container.nlp_extractor

    # В Telegram handlers (через context.bot_data)
    container = context.bot_data['container']
    result = await container.intent_processor.process(...)

ПРЕИМУЩЕСТВА:
    - Все зависимости в одном месте
    - Легко подменять для тестов
    - Контроль порядка инициализации
    - Управление жизненным циклом

==============================================================================
"""
import logging
from dataclasses import dataclass, field
from typing import Optional, Any, TYPE_CHECKING

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from telegram.ext import Application
    from tracy.core.database import DatabaseService
    from tracy.core.cache import CacheService
    from tracy.core.security import TokenEncryption
    from tracy.api.auth import JWTAuthService


@dataclass
class Container:
    """
    Контейнер зависимостей приложения.

    Содержит все сервисы, необходимые для работы бота.
    Создаётся один раз при запуске и передаётся через context.bot_data.
    """

    # ==========================================================================
    # Core Services
    # ==========================================================================

    # Legacy Database (существующий класс)
    legacy_db: Any = None

    # New DatabaseService с context managers
    database: Optional['DatabaseService'] = None

    # Кэширование
    cache: Optional['CacheService'] = None

    # Шифрование токенов
    token_encryption: Optional['TokenEncryption'] = None

    # JWT аутентификация
    auth_service: Optional['JWTAuthService'] = None

    # ==========================================================================
    # Integration Services (AI, Calendar)
    # ==========================================================================

    # NLP для извлечения intent
    nlp_extractor: Any = None

    # Обработка медиа (voice, image)
    media_processor: Any = None

    # Расшифровка встреч
    meeting_processor: Any = None

    # ==========================================================================
    # Business Logic Services
    # ==========================================================================

    # Планировщик напоминаний
    reminder_scheduler: Any = None

    # Обработчик intent-ов (decision engine)
    intent_processor: Any = None

    # Память диалога
    conversation_memory: Any = None

    # Multi-turn диалоги
    conversation_handler: Any = None

    # ==========================================================================
    # Telegram Application
    # ==========================================================================

    # Telegram bot application
    telegram_app: Optional['Application'] = None

    # ==========================================================================
    # Configuration
    # ==========================================================================

    # Config объект
    config: Any = None

    # ==========================================================================
    # Factory Methods
    # ==========================================================================

    @classmethod
    def create(
        cls,
        config: Any = None,
        use_cache: bool = True,
        use_encryption: bool = True
    ) -> 'Container':
        """
        Создать контейнер с инициализированными сервисами.

        Args:
            config: Объект конфигурации (по умолчанию из config.py)
            use_cache: Использовать кэширование
            use_encryption: Использовать шифрование токенов

        Returns:
            Инициализированный Container
        """
        logger.info("Создание DI контейнера...")

        # Импорты внутри метода для избежания циклических зависимостей
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

        # Config
        if config is None:
            import config as app_config
            config = app_config

        # Legacy Database
        from database import Database
        legacy_db = Database()
        logger.info("✓ Database инициализирован")

        # New DatabaseService
        from tracy.core.database import DatabaseService
        database = DatabaseService(legacy_db)
        logger.info("✓ DatabaseService инициализирован")

        # Cache (опционально)
        cache = None
        if use_cache:
            try:
                from tracy.core.cache import InMemoryCache
                cache = InMemoryCache()
                logger.info("✓ Cache инициализирован (InMemory)")
            except Exception as e:
                logger.warning(f"Cache не инициализирован: {e}")

        # Token Encryption (опционально)
        token_encryption = None
        if use_encryption:
            try:
                from tracy.core.security import TokenEncryption
                token_encryption = TokenEncryption()
                logger.info("✓ TokenEncryption инициализирован")
            except Exception as e:
                logger.warning(f"TokenEncryption не инициализирован: {e}")

        # JWT Auth Service
        auth_service = None
        try:
            from tracy.api.auth import JWTAuthService
            auth_service = JWTAuthService()
            logger.info("✓ JWTAuthService инициализирован")
        except Exception as e:
            logger.warning(f"JWTAuthService не инициализирован: {e}")

        # NLP Extractor
        nlp_extractor = None
        try:
            from nlp_extractor import NLPExtractor
            nlp_extractor = NLPExtractor()
            logger.info("✓ NLPExtractor инициализирован")
        except Exception as e:
            logger.warning(f"NLPExtractor не инициализирован: {e}")

        # Media Processor
        media_processor = None
        try:
            from media_processor import MediaProcessor
            media_processor = MediaProcessor()
            logger.info("✓ MediaProcessor инициализирован")
        except Exception as e:
            logger.warning(f"MediaProcessor не инициализирован: {e}")

        # Meeting Processor
        meeting_processor = None
        try:
            from meeting_processor import MeetingProcessor
            if nlp_extractor and hasattr(nlp_extractor, 'client'):
                meeting_processor = MeetingProcessor(nlp_extractor.client)
                logger.info("✓ MeetingProcessor инициализирован")
        except Exception as e:
            logger.warning(f"MeetingProcessor не инициализирован: {e}")

        container = cls(
            config=config,
            legacy_db=legacy_db,
            database=database,
            cache=cache,
            token_encryption=token_encryption,
            auth_service=auth_service,
            nlp_extractor=nlp_extractor,
            media_processor=media_processor,
            meeting_processor=meeting_processor,
        )

        logger.info("✓ DI контейнер создан")
        return container

    def initialize_bot_services(self, telegram_bot: Any) -> None:
        """
        Инициализировать сервисы, требующие Telegram bot.

        Вызывается после создания Telegram Application.

        Args:
            telegram_bot: Telegram Bot object
        """
        logger.info("Инициализация bot-зависимых сервисов...")

        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

        # Reminder Scheduler
        try:
            from reminder_scheduler import ReminderScheduler
            self.reminder_scheduler = ReminderScheduler(self.legacy_db, telegram_bot)
            logger.info("✓ ReminderScheduler инициализирован")
        except Exception as e:
            logger.warning(f"ReminderScheduler не инициализирован: {e}")

        # Decision Engine (Intent Processor)
        try:
            from decision_engine import DecisionEngine
            ai_client = self.nlp_extractor.client if self.nlp_extractor else None
            self.intent_processor = DecisionEngine(
                self.legacy_db,
                self.reminder_scheduler,
                ai_client
            )
            logger.info("✓ DecisionEngine (IntentProcessor) инициализирован")
        except Exception as e:
            logger.warning(f"DecisionEngine не инициализирован: {e}")

        # Conversation Memory
        try:
            from conversation_memory import ConversationMemory
            self.conversation_memory = ConversationMemory(self.legacy_db)
            logger.info("✓ ConversationMemory инициализирован")
        except Exception as e:
            logger.warning(f"ConversationMemory не инициализирован: {e}")

        # Conversation Handler
        try:
            from conversation_handler import ConversationHandler
            self.conversation_handler = ConversationHandler(
                self.nlp_extractor,
                self.intent_processor,
                self.conversation_memory
            )
            logger.info("✓ ConversationHandler инициализирован")
        except Exception as e:
            logger.warning(f"ConversationHandler не инициализирован: {e}")

        logger.info("✓ Bot-зависимые сервисы инициализированы")

    async def start_background_services(self) -> None:
        """Запустить фоновые сервисы (reminder scheduler и т.д.)."""
        if self.reminder_scheduler:
            try:
                self.reminder_scheduler.start()
                logger.info("✓ ReminderScheduler запущен")
            except Exception as e:
                logger.error(f"Ошибка запуска ReminderScheduler: {e}")

    async def stop_background_services(self) -> None:
        """Остановить фоновые сервисы."""
        if self.reminder_scheduler:
            try:
                self.reminder_scheduler.stop()
                logger.info("✓ ReminderScheduler остановлен")
            except Exception as e:
                logger.error(f"Ошибка остановки ReminderScheduler: {e}")

    # ==========================================================================
    # Convenience Properties
    # ==========================================================================

    @property
    def db(self) -> Any:
        """Алиас для legacy_db (обратная совместимость)."""
        return self.legacy_db

    @property
    def decision_engine(self) -> Any:
        """Алиас для intent_processor (обратная совместимость)."""
        return self.intent_processor


# =============================================================================
# Global Container Instance
# =============================================================================

_global_container: Optional[Container] = None


def get_container() -> Optional[Container]:
    """Получить глобальный экземпляр контейнера."""
    return _global_container


def set_container(container: Container) -> None:
    """Установить глобальный экземпляр контейнера."""
    global _global_container
    _global_container = container


def create_container(**kwargs) -> Container:
    """Создать и установить глобальный контейнер."""
    container = Container.create(**kwargs)
    set_container(container)
    return container
