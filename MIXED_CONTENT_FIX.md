# Исправление проблемы Mixed Content Policy

## Проблема
Веб-приложение открывается через HTTPS (GitHub Pages), но API работает на HTTP (`http://5.35.126.42:8080`). Браузер блокирует HTTP запросы из HTTPS страниц из-за Mixed Content Policy.

## Решение
Использовать Telegram WebApp API (`tg.sendData`) для передачи данных, как это сделано для feedback. Это обходит проблему Mixed Content Policy.

## Что нужно сделать
1. Добавить обработчики в bot.py для `get_todo_lists` и `get_chat_data`
2. Обновить веб-приложение для использования Telegram WebApp API вместо прямых HTTP запросов

## Альтернативное решение
Настроить HTTPS для API через nginx с SSL сертификатом (требует настройки домена в DNS).

