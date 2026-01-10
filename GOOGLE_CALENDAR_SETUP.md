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

### 3. Настройка OAuth Consent Screen (ВАЖНО!)

**⚠️ Это нужно сделать ПЕРЕД созданием OAuth credentials!**

1. Перейди в "APIs & Services" → "OAuth consent screen"
2. Если еще не настроен, выбери "External" (для личного использования)
3. Заполни обязательные поля на шаге "OAuth consent screen":
   - **App name**: "TRACY Bot"
   - **User support email**: твой email (например, karchauskas7889@gmail.com)
   - **Developer contact email**: твой email
   - **App domain** (опционально): karchauskas1.github.io
4. Нажми "Save and Continue"
5. На шаге "Scopes":
   - Нажми "Add or Remove Scopes"
   - Выбери "Google Calendar API" → `/auth/calendar`
   - Нажми "Update" → "Save and Continue"
6. На шаге "Test users":
   - Нажми "+ ADD USERS"
   - Добавь свой Google email: karchauskas7889@gmail.com
   - Нажми "Add" → "Save and Continue"
7. На шаге "Summary":
   - Проверь все настройки
   - Нажми "Back to Dashboard"

4. Создание OAuth 2.0 credentials

1. Перейди в "APIs & Services" → "Credentials"
2. Нажми "Create Credentials" → "OAuth client ID"
3. Выбери тип приложения: **"Web application"**
4. Заполни поля:
   - **Name**: "TRACY Bot Web Client"
   - **Authorized redirect URIs**: 
     - Нажми "+ ADD URI"
     - Добавь: `https://karchauskas1.github.io/TRACY-AI/oauth-callback.html`
5. Нажми "Create"
6. **ВАЖНО**: Скопируй **Client ID** и **Client Secret** - они понадобятся дальше!

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

### Ошибка: "redirect_uri_mismatch" (Error 400)

**Причина**: Redirect URI в запросе авторизации не совпадает с тем, что указан в Google Cloud Console.

**Решение**:
1. Открой [Google Cloud Console - Credentials](https://console.cloud.google.com/apis/credentials)
2. Найди свой OAuth 2.0 Client ID (тот, который ты создал для бота)
3. Нажми на название или иконку редактирования (карандаш)
4. В разделе **"Authorized redirect URIs"** нажми **"+ ADD URI"**
5. Добавь следующий URI:
   ```
   https://karchauskas1.github.io/TRACY-AI/oauth-callback.html
   ```
6. Если нужно тестировать локально, также добавь:
   ```
   http://localhost:8080/callback
   ```
7. Нажми **"SAVE"**
8. Подожди 1-2 минуты для применения изменений
9. Попробуй снова подключить календарь в боте

**Важно:**
- URI должен точно совпадать (включая `https://`, без завершающего слеша после `.html`)
- Если используешь другой домен для веб-приложения, измени URI соответственно
- Изменения в Google Cloud Console применяются не мгновенно, подожди пару минут

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

