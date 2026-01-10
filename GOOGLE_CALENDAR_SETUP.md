# Настройка Google Calendar OAuth

Для подключения Google Calendar к боту TRACY необходимо настроить OAuth 2.0 credentials в Google Cloud Console.

## Пошаговая инструкция

### 1. Создание проекта в Google Cloud Console

1. Перейди на [Google Cloud Console](https://console.cloud.google.com/)
2. Войди в свой Google аккаунт
3. Создай новый проект:
   - Нажми на выпадающий список проектов вверху страницы
   - Нажми "New Project"
   - Введи название проекта (например, "TRACY Bot")
   - Нажми "Create"

### 2. Включение Google Calendar API

1. В меню слева выбери "APIs & Services" → "Library"
2. В поиске введи "Google Calendar API"
3. Нажми на результат "Google Calendar API"
4. Нажми кнопку "Enable"

### 3. Создание OAuth 2.0 credentials

1. Перейди в "APIs & Services" → "Credentials"
2. Нажми "Create Credentials" → "OAuth client ID"
3. Если появится предупреждение о consent screen:
   - Выбери "External" (для личного использования)
   - Заполни обязательные поля:
     - App name: "TRACY Bot"
     - User support email: твой email
     - Developer contact email: твой email
   - Нажми "Save and Continue"
   - На шаге "Scopes" нажми "Save and Continue"
   - На шаге "Test users" добавь свой Google email, нажми "Save and Continue"
   - Нажми "Back to Dashboard"

4. Снова нажми "Create Credentials" → "OAuth client ID"
5. Выбери тип приложения: **"Web application"**
6. Заполни поля:
   - **Name**: "TRACY Bot Web Client"
   - **Authorized redirect URIs**: 
     - Добавь: `http://localhost:8080/callback`
     - (Для продакшена добавь реальный URL callback)
7. Нажми "Create"
8. **ВАЖНО**: Скопируй **Client ID** и **Client Secret** - они понадобятся дальше!

### 4. Настройка переменных окружения

Открой файл `.env` в корне проекта и добавь (или обнови) следующие строки:

```env
GOOGLE_CLIENT_ID=твой_client_id_здесь
GOOGLE_CLIENT_SECRET=твой_client_secret_здесь
GOOGLE_REDIRECT_URI=http://localhost:8080/callback
```

**ВАЖНО:**
- Не оставляй пробелы вокруг знака `=`
- Не заключай значения в кавычки
- Убедись, что значения скопированы полностью

Пример:
```env
GOOGLE_CLIENT_ID=123456789-abcdefghijklmnop.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-abcdefghijklmnopqrstuvwxyz
GOOGLE_REDIRECT_URI=http://localhost:8080/callback
```

### 5. Перезапуск бота

После настройки переменных окружения необходимо перезапустить бота:

```bash
./restart_bot.sh
```

Или вручную:
```bash
# Остановить текущий процесс
pkill -f "python.*bot.py"

# Запустить заново
nohup python3 bot.py > bot.log 2>&1 &
```

### 6. Проверка работы

1. Открой бота в Telegram
2. Нажми `/start` или `/menu`
3. Выбери "⚙️ Настройки"
4. Выбери "Google Calendar"
5. Если все настроено правильно, появится кнопка "🔗 Открыть ссылку авторизации"

## Решение проблем

### Ошибка: "Google OAuth не настроен"

**Причина**: Переменные окружения не установлены или пустые.

**Решение**:
1. Проверь, что файл `.env` существует в корне проекта
2. Убедись, что переменные `GOOGLE_CLIENT_ID` и `GOOGLE_CLIENT_SECRET` заполнены
3. Проверь, что нет пробелов вокруг знака `=`
4. Перезапусти бота после изменения `.env`

### Ошибка: "Access blocked" при авторизации

**Причина**: Приложение находится в статусе "Testing" и доступно только тестовым пользователям.

**Решение** (ВАЖНО - сделать это сейчас):
1. Перейди в [Google Cloud Console](https://console.cloud.google.com/)
2. Убедись, что выбран правильный проект (тот, где создан OAuth client)
3. Перейди в **"APIs & Services"** → **"OAuth consent screen"**
4. Прокрути вниз до раздела **"Test users"**
5. Нажми кнопку **"+ ADD USERS"**
6. Добавь свой Google email: **karchauskas7889@gmail.com**
7. Нажми **"Add"**
8. Попробуй снова подключить календарь в боте

**После добавления email:**
- Перезапускать бота НЕ нужно
- Просто попробуй снова нажать "Открыть ссылку авторизации" в боте
- Теперь должно работать!

### Ошибка: "redirect_uri_mismatch"

**Причина**: Redirect URI в credentials не совпадает с `GOOGLE_REDIRECT_URI` в `.env`.

**Решение**:
1. Проверь `GOOGLE_REDIRECT_URI` в файле `.env`
2. Убедись, что в Google Cloud Console в OAuth credentials добавлен точно такой же Redirect URI
3. Обрати внимание на `http://` vs `https://` и наличие/отсутствие завершающего слеша

### Ошибка: "invalid_client"

**Причина**: Неправильный Client ID или Client Secret.

**Решение**:
1. Проверь, что значения скопированы полностью
2. Убедись, что нет лишних пробелов или переносов строк
3. Проверь, что используешь правильные credentials (для Web application, а не Desktop или Mobile)

## Дополнительные ресурсы

- [Google Calendar API Documentation](https://developers.google.com/calendar/api/guides/overview)
- [OAuth 2.0 для веб-серверных приложений](https://developers.google.com/identity/protocols/oauth2/web-server)
- [Google Cloud Console](https://console.cloud.google.com/)

