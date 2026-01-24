"""
==============================================================================
MAIN.PY - ТОЧКА ВХОДА С DEPENDENCY INJECTION
==============================================================================

Новая точка входа для TRACY бота с использованием DI контейнера.
Может использоваться параллельно с существующим bot.py для постепенной миграции.

ИСПОЛЬЗОВАНИЕ:
    # Прямой запуск
    python -m tracy.main

    # Или через импорт
    from tracy.main import run_bot
    asyncio.run(run_bot())

ПРЕИМУЩЕСТВА ПЕРЕД bot.py:
    - DI контейнер для управления зависимостями
    - Отдельные модули для handlers
    - Кэширование и персистентное состояние
    - JWT аутентификация для API

==============================================================================
"""
import asyncio
import logging
import sys
import os
from typing import Optional

# Добавляем родительскую директорию в path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telegram import Update, BotCommand, MenuButtonWebApp, WebAppInfo
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)

import config
from tracy.core.container import Container, set_container
from tracy.handlers.commands import register_command_handlers, get_reply_keyboard

logger = logging.getLogger(__name__)


# =============================================================================
# Application Setup
# =============================================================================

async def setup_bot_commands(application: Application) -> None:
    """Установить команды бота в меню Telegram."""
    commands = [
        BotCommand("start", "Начать работу с ботом"),
        BotCommand("menu", "Главное меню"),
        BotCommand("help", "Справка по командам"),
        BotCommand("settings", "Настройки"),
        BotCommand("web", "Открыть веб-приложение"),
        BotCommand("search", "Поиск событий"),
        BotCommand("share", "Поделиться ботом"),
    ]

    await application.bot.set_my_commands(commands)
    logger.info("✓ Bot commands установлены")


async def setup_menu_button(application: Application) -> None:
    """Установить кнопку меню с веб-приложением."""
    if config.WEB_APP_URL and config.is_valid_production_url(config.WEB_APP_URL):
        import datetime
        version = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        web_url = f"{config.WEB_APP_URL}?v={version}"

        menu_button = MenuButtonWebApp(
            text="📅 Открыть TRACY",
            web_app=WebAppInfo(url=web_url)
        )
        await application.bot.set_chat_menu_button(menu_button=menu_button)
        logger.info(f"✓ Menu button установлен: {web_url}")


async def post_init(application: Application) -> None:
    """Действия после инициализации приложения."""
    # Получаем контейнер
    container: Container = application.bot_data.get('container')

    if container:
        # Инициализируем bot-зависимые сервисы
        container.initialize_bot_services(application.bot)

        # Запускаем фоновые сервисы
        await container.start_background_services()

    # Устанавливаем команды и меню
    await setup_bot_commands(application)
    await setup_menu_button(application)

    logger.info("✓ Post-init completed")


async def post_shutdown(application: Application) -> None:
    """Действия при остановке приложения."""
    container: Container = application.bot_data.get('container')

    if container:
        await container.stop_background_services()

    logger.info("✓ Post-shutdown completed")


# =============================================================================
# Message Handler (temporary wrapper to existing bot.py)
# =============================================================================

async def handle_message_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Временная обёртка для handle_message из bot.py.

    Позволяет использовать существующую логику обработки сообщений
    пока идёт миграция на новую архитектуру.
    """
    # Импортируем существующий handler
    try:
        from bot import handle_message
        await handle_message(update, context)
    except ImportError:
        # Fallback: простой ответ
        await update.message.reply_text(
            "Сообщение получено. Обработка сообщений в процессе миграции.",
            reply_markup=get_reply_keyboard(context)
        )


async def handle_callback_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Временная обёртка для callback handler из bot.py."""
    try:
        from bot import settings_callback
        await settings_callback(update, context)
    except ImportError:
        await update.callback_query.answer("Callback обработка в процессе миграции")


# =============================================================================
# HTTP Server Integration
# =============================================================================

async def start_http_server_with_container(container: Container):
    """Запустить HTTP сервер с контейнером."""
    try:
        from http_server import start_http_server, set_database

        # Устанавливаем database для http_server
        if container.legacy_db:
            set_database(container.legacy_db)

        # Запускаем сервер
        host = config.HOST or 'localhost'
        port = int(config.PORT) if config.PORT else 8080

        await start_http_server(host, port)

    except Exception as e:
        logger.error(f"❌ Ошибка запуска HTTP сервера: {e}")


# =============================================================================
# Main Entry Point
# =============================================================================

def create_application(container: Optional[Container] = None) -> Application:
    """
    Создать Telegram Application с DI контейнером.

    Args:
        container: DI контейнер (создаётся если не передан)

    Returns:
        Настроенное Telegram Application
    """
    # Создаём контейнер если не передан
    if container is None:
        container = Container.create()
        set_container(container)

    # Создаём application
    application = (
        Application.builder()
        .token(config.TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )

    # Сохраняем контейнер в bot_data
    application.bot_data['container'] = container

    # Регистрируем handlers из нового модуля
    register_command_handlers(application, container)

    # Регистрируем message и callback handlers (временно используем обёртки)
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_message_wrapper
    ))

    application.add_handler(MessageHandler(
        filters.VOICE | filters.AUDIO | filters.PHOTO | filters.Document.AUDIO,
        handle_message_wrapper
    ))

    application.add_handler(CallbackQueryHandler(handle_callback_wrapper))

    return application


async def run_bot() -> None:
    """Запустить бота с полной инфраструктурой."""
    # Настраиваем логирование
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )

    logger.info("=" * 60)
    logger.info("🚀 TRACY Bot запускается с новой архитектурой")
    logger.info("=" * 60)

    # Создаём контейнер
    container = Container.create()
    set_container(container)

    logger.info("✓ DI Container создан")

    # Создаём application
    application = create_application(container)

    logger.info("✓ Telegram Application создан")

    # Запускаем HTTP сервер в фоне
    asyncio.create_task(start_http_server_with_container(container))

    # Запускаем polling
    logger.info("🤖 Запуск polling...")

    await application.initialize()
    await application.start()
    await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)

    # Держим бота запущенным
    try:
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        pass
    finally:
        await application.updater.stop()
        await application.stop()
        await application.shutdown()


def main():
    """Entry point для запуска через python -m tracy.main"""
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
