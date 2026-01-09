#!/bin/bash

echo "🚀 Запуск TRACY Web App"
echo ""

# Проверка .env.local
if [ ! -f .env.local ]; then
    echo "⚠️  Файл .env.local не найден!"
    echo "📝 Создаю из примера..."
    cp .env.local.example .env.local
    echo "✅ Файл создан. Пожалуйста, отредактируйте .env.local и заполните необходимые значения."
    echo ""
    echo "Минимально необходимые переменные:"
    echo "  - DATABASE_URL"
    echo "  - NEXTAUTH_SECRET"
    echo "  - TELEGRAM_BOT_TOKEN"
    echo "  - NEXT_PUBLIC_TELEGRAM_BOT_USERNAME"
    echo ""
    read -p "Нажмите Enter после настройки .env.local..."
fi

# Проверка базы данных
echo "🔍 Проверка базы данных..."
if ! npm run db:generate > /dev/null 2>&1; then
    echo "❌ Ошибка генерации Prisma Client"
    exit 1
fi

# Применение схемы
echo "📊 Применение схемы базы данных..."
if ! npm run db:push > /dev/null 2>&1; then
    echo "⚠️  Предупреждение: не удалось применить схему"
    echo "   Убедитесь, что PostgreSQL запущен и DATABASE_URL правильный"
fi

# Запуск
echo ""
echo "✅ Запуск сервера разработки..."
echo "🌐 Приложение будет доступно по адресу: http://localhost:3000"
echo ""
npm run dev
