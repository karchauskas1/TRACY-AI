#!/bin/bash

# Скрипт автоматического деплоя TRACY AI Bot
# Выполняет: коммит изменений, push в GitHub, перезапуск бота, деплой на Vercel

set -e  # Остановка при ошибке

echo "🚀 Начинаем автоматический деплой TRACY AI Bot..."

# Цвета для вывода
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Переходим в корневую директорию проекта
cd "$(dirname "$0")"

# 1. Добавляем все изменения
echo -e "${BLUE}📦 Добавляем изменения в git...${NC}"
git add .

# 2. Коммитим изменения
echo -e "${BLUE}💾 Создаем коммит...${NC}"
COMMIT_MSG="${1:-Auto deploy: $(date '+%Y-%m-%d %H:%M:%S')}"
git commit -m "$COMMIT_MSG" || {
    echo -e "${YELLOW}⚠️  Нет изменений для коммита${NC}"
}

# 3. Пушим в GitHub
echo -e "${BLUE}📤 Отправляем изменения в GitHub...${NC}"
git push origin main || {
    echo -e "${YELLOW}⚠️  Ошибка при push в GitHub${NC}"
    exit 1
}

echo -e "${GREEN}✅ Изменения отправлены в GitHub${NC}"

# 4. Перезапускаем бота на сервере
echo -e "${BLUE}🔄 Перезапускаем бота на сервере...${NC}"
REMOTE_CMD="cd /opt/tracy-ai-bot && systemctl restart tracy-bot.service && systemctl status tracy-bot.service --no-pager -l"

# ВАЖНО: Никаких паролей в репозитории.
# Если нужен non-interactive режим, задайте SSHPASS в окружении и установите sshpass локально.
if [ -n "$SSHPASS" ] && command -v sshpass >/dev/null 2>&1; then
    sshpass -e ssh -o StrictHostKeyChecking=no root@5.35.126.42 "$REMOTE_CMD" || {
        echo -e "${YELLOW}⚠️  Ошибка при перезапуске бота${NC}"
    }
else
    ssh -o StrictHostKeyChecking=no root@5.35.126.42 "$REMOTE_CMD" || {
        echo -e "${YELLOW}⚠️  Ошибка при перезапуске бота${NC}"
    }
fi

echo -e "${GREEN}✅ Бот перезапущен${NC}"

# 5. Деплой на Vercel (если проект подключен через GitHub, произойдет автоматически)
echo -e "${BLUE}🌐 Проверяем деплой на Vercel...${NC}"
echo -e "${YELLOW}ℹ️  Если проект подключен к Vercel через GitHub, деплой произойдет автоматически${NC}"
echo -e "${YELLOW}ℹ️  Проверьте статус деплоя: https://vercel.com/dashboard${NC}"

# Опционально: можно попробовать деплой через CLI, если есть токен
if [ -n "$VERCEL_TOKEN" ]; then
    echo -e "${BLUE}🔐 Используем VERCEL_TOKEN для деплоя...${NC}"
    cd web-app
    VERCEL_TOKEN="$VERCEL_TOKEN" npx vercel --yes --prod --token "$VERCEL_TOKEN" || {
        echo -e "${YELLOW}⚠️  Ошибка при деплое через CLI (возможно, деплой уже идет через GitHub)${NC}"
    }
    cd ..
else
    echo -e "${YELLOW}ℹ️  VERCEL_TOKEN не установлен. Деплой через GitHub должен произойти автоматически.${NC}"
fi

echo -e "${GREEN}🎉 Деплой завершен!${NC}"
echo -e "${BLUE}📊 Проверьте:${NC}"
echo -e "   - GitHub: https://github.com/karchauskas1/TRACY-AI"
echo -e "   - Vercel: https://vercel.com/dashboard"
