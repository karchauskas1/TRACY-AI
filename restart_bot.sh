#!/bin/bash
# Скрипт для перезапуска бота TRACY

set -e

cd "$(dirname "$0")"

echo "🔄 Перезапускаю бота TRACY..."

# Находим и останавливаем текущий процесс
BOT_PID=$(pgrep -f 'python.*bot\.py' || echo "")
if [ ! -z "$BOT_PID" ]; then
    echo "⏹️  Останавливаю текущий процесс (PID: $BOT_PID)..."
    kill $BOT_PID 2>/dev/null || true
    sleep 2
    
    # Проверяем что процесс остановлен
    if ps -p $BOT_PID > /dev/null 2>&1; then
        echo "⚠️  Процесс не остановился, принудительно завершаю..."
        kill -9 $BOT_PID 2>/dev/null || true
        sleep 1
    fi
    echo "✅ Процесс остановлен"
else
    echo "ℹ️  Бот не был запущен"
fi

# Запускаем бота заново
echo "🚀 Запускаю бота..."
nohup python3 bot.py > bot.log 2>&1 &
NEW_PID=$!
echo $NEW_PID > bot.pid

sleep 3

# Проверяем что бот запустился
if ps -p $NEW_PID > /dev/null 2>&1; then
    echo "✅ Бот успешно запущен (PID: $NEW_PID)"
    echo "📋 Последние строки лога:"
    tail -5 bot.log 2>/dev/null || echo "Лог еще не создан"
else
    echo "❌ Ошибка: бот не запустился"
    echo "📋 Лог ошибок:"
    tail -20 bot.log 2>/dev/null || echo "Лог недоступен"
    exit 1
fi

echo "✨ Перезапуск завершен!"

