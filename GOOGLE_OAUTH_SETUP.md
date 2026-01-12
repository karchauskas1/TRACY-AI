# 🔐 Инструкция по настройке Google OAuth (GOOGLE_CLIENT_ID и GOOGLE_CLIENT_SECRET)

Эта инструкция поможет вам получить `GOOGLE_CLIENT_ID` и `GOOGLE_CLIENT_SECRET` для работы с Google Calendar, Google Sheets и Google Drive.

---

## 📋 Шаг 1: Создание проекта в Google Cloud Console

1. Перейдите на [Google Cloud Console](https://console.cloud.google.com/)
2. Войдите в свой Google аккаунт
3. Нажмите на выпадающий список проектов вверху (рядом с логотипом Google Cloud)
4. Нажмите **"Новый проект"** (или **"New Project"**)
5. Введите название проекта (например, "TRACY AI Bot")
6. Нажмите **"Создать"** (или **"Create"**)
7. Дождитесь создания проекта (обычно несколько секунд)

---

## 🔧 Шаг 2: Включение необходимых API

После создания проекта нужно включить API, которые использует бот:

### 2.1. Google Calendar API

1. В меню слева выберите **"APIs & Services"** → **"Library"** (или **"API и сервисы"** → **"Библиотека"**)
2. В поиске введите **"Google Calendar API"**
3. Нажмите на **"Google Calendar API"**
4. Нажмите кнопку **"Enable"** (или **"Включить"**)
5. Дождитесь активации

### 2.2. Google Sheets API

1. В той же библиотеке API найдите **"Google Sheets API"**
2. Нажмите на **"Google Sheets API"**
3. Нажмите **"Enable"** (или **"Включить"**)
4. Дождитесь активации

### 2.3. Google Drive API

1. В библиотеке API найдите **"Google Drive API"**
2. Нажмите на **"Google Drive API"**
3. Нажмите **"Enable"** (или **"Включить"**)
4. Дождитесь активации

---

## 🔑 Шаг 3: Создание OAuth 2.0 Credentials

1. В меню слева выберите **"APIs & Services"** → **"Credentials"** (или **"API и сервисы"** → **"Учетные данные"**)
2. Нажмите кнопку **"+ CREATE CREDENTIALS"** (или **"+ СОЗДАТЬ УЧЕТНЫЕ ДАННЫЕ"**)
3. Выберите **"OAuth client ID"** (или **"Идентификатор клиента OAuth"**)

### 3.1. Настройка экрана согласия OAuth (если требуется)

Если вы впервые создаете OAuth credentials, Google попросит настроить экран согласия:

1. Выберите тип пользователя:
   - **"External"** (Внешний) - для личного использования или тестирования
   - **"Internal"** (Внутренний) - только для Google Workspace организаций
2. Заполните обязательные поля:
   - **"App name"** (Название приложения): например, "TRACY AI Bot"
   - **"User support email"** (Email поддержки): ваш email
   - **"Developer contact information"** (Контактная информация разработчика): ваш email
3. Нажмите **"Save and Continue"** (или **"Сохранить и продолжить"**)
4. На шаге **"Scopes"** (Области доступа) нажмите **"Save and Continue"** (можно пропустить, scopes будут указаны в коде)
5. На шаге **"Test users"** (Тестовые пользователи) добавьте свой Google email, если выбрали "External"
6. Нажмите **"Save and Continue"**
7. Нажмите **"Back to Dashboard"** (или **"Вернуться на панель управления"**)

### 3.2. Создание OAuth Client ID

1. Вернитесь в **"APIs & Services"** → **"Credentials"**
2. Нажмите **"+ CREATE CREDENTIALS"** → **"OAuth client ID"**
3. Выберите **"Application type"** (Тип приложения): **"Web application"** (Веб-приложение)
4. Введите **"Name"** (Название): например, "TRACY Bot Web Client"
5. В разделе **"Authorized redirect URIs"** (Разрешенные URI перенаправления) добавьте:
   - Для локальной разработки: `http://localhost:8080/callback`
   - Для production (GitHub Pages): `https://karchauskas1.github.io/TRACY-AI/`
   - Или ваш production URL, если отличается
6. Нажмите **"Create"** (или **"Создать"**)

---

## 📝 Шаг 4: Копирование Client ID и Client Secret

После создания OAuth Client ID откроется окно с данными:

1. **Client ID** - длинная строка, начинающаяся с цифр и заканчивающаяся `.apps.googleusercontent.com`
2. **Client secret** - строка из букв, цифр и символов

**⚠️ ВАЖНО:** Сохраните эти данные в безопасном месте! Client Secret показывается только один раз.

---

## ⚙️ Шаг 5: Добавление в .env файл

1. Откройте файл `.env` в корне проекта (или создайте его, если нет)
2. Добавьте следующие строки:

```bash
GOOGLE_CLIENT_ID=ваш_client_id_здесь
GOOGLE_CLIENT_SECRET=ваш_client_secret_здесь
GOOGLE_REDIRECT_URI=https://karchauskas1.github.io/TRACY-AI/
```

**Пример:**
```bash
GOOGLE_CLIENT_ID=123456789-abcdefghijklmnop.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-abcdefghijklmnopqrstuvwxyz
GOOGLE_REDIRECT_URI=https://karchauskas1.github.io/TRACY-AI/
```

3. Сохраните файл

---

## 🔄 Шаг 6: Перезапуск бота

После добавления credentials в `.env` файл:

1. Перезапустите бота
2. Теперь пользователи смогут авторизоваться в Google для доступа к Calendar, Sheets и Drive

---

## ✅ Проверка настройки

После настройки вы можете проверить:

1. **Google Calendar**: Попросите пользователя подключить календарь через `/settings` → "Подключить Google Calendar"
2. **Обратная связь**: Попросите пользователя отправить обратную связь со скриншотом - бот запросит авторизацию Google

---

## 🆘 Решение проблем

### Проблема: "redirect_uri_mismatch"

**Решение:** Убедитесь, что `GOOGLE_REDIRECT_URI` в `.env` точно совпадает с одним из URI в "Authorized redirect URIs" в Google Cloud Console.

### Проблема: "access_denied" или "invalid_client"

**Решение:** 
- Проверьте, что `GOOGLE_CLIENT_ID` и `GOOGLE_CLIENT_SECRET` скопированы правильно (без лишних пробелов)
- Убедитесь, что API включены (Calendar, Sheets, Drive)

### Проблема: API не работает

**Решение:**
- Проверьте, что все три API включены (Calendar, Sheets, Drive)
- Убедитесь, что выбран правильный проект в Google Cloud Console

---

## 📚 Дополнительные ресурсы

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Google Calendar API Quickstart](https://developers.google.com/calendar/api/quickstart/python)
- [Google Sheets API Documentation](https://developers.google.com/sheets/api)
- [Google Drive API Documentation](https://developers.google.com/drive/api)

---

**Готово!** Теперь у вас есть все необходимое для работы с Google API. 🎉

