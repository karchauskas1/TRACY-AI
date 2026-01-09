#!/bin/bash
echo "🔧 Настройка базы данных для TRACY Web App"
echo ""

# Проверка PostgreSQL
if command -v psql &> /dev/null; then
    echo "✅ PostgreSQL найден"
    echo "📊 Создаю базу данных tracy..."
    createdb tracy 2>/dev/null && echo "✅ База данных создана" || echo "⚠️  База данных уже существует или ошибка"
else
    echo "❌ PostgreSQL не найден"
    echo ""
    echo "Установите PostgreSQL одним из способов:"
    echo ""
    echo "1. Через Homebrew:"
    echo "   brew install postgresql@15"
    echo "   brew services start postgresql@15"
    echo ""
    echo "2. Через Docker:"
    echo "   docker run --name tracy-postgres -e POSTGRES_PASSWORD=password -e POSTGRES_DB=tracy -p 5432:5432 -d postgres:15"
    echo ""
    echo "3. Скачайте с официального сайта: https://www.postgresql.org/download/"
    exit 1
fi

echo ""
echo "📦 Применяю схему базы данных..."
cd "$(dirname "$0")"
npm run db:generate
npm run db:push

echo ""
echo "✅ База данных настроена!"
