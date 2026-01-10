#!/bin/bash
# Скрипт автоматического деплоя веб-приложения

set -e

echo "🚀 Начинаю деплой веб-приложения TRACY..."

cd "$(dirname "$0")"

# Проверяем, что мы в правильной директории
if [ ! -d "web-app" ]; then
    echo "❌ Ошибка: папка web-app не найдена"
    exit 1
fi

echo "📦 Собираю веб-приложение..."
cd web-app
npm run build

if [ ! -d "out" ]; then
    echo "❌ Ошибка: сборка не создала папку out/"
    exit 1
fi

echo "✅ Сборка завершена успешно"
echo "📊 Размер сборки: $(du -sh out/ | cut -f1)"

cd ..

echo "📝 Проверяю статус git..."
git status --short

echo "📤 Пытаюсь отправить изменения в GitHub..."
if git push origin main; then
    echo "✅ Изменения успешно отправлены в GitHub"
    echo "🔗 GitHub Actions автоматически задеплоит веб-приложение"
    echo "⏳ Деплой займет несколько минут. Проверь статус здесь:"
    echo "   https://github.com/karchauskas1/TRACY-AI/actions"
else
    echo "⚠️  Push требует аутентификации. Выполните вручную:"
    echo "   git push origin main"
    echo ""
    echo "Или используйте Personal Access Token:"
    echo "   git push https://<TOKEN>@github.com/karchauskas1/TRACY-AI.git main"
fi

echo "✨ Готово!"

