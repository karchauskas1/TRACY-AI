export type Locale = 'ru' | 'en'

export const translations = {
  ru: {
    // Общие
    common: {
      back: 'Назад',
      save: 'Сохранить',
      cancel: 'Отмена',
      confirm: 'Подтвердить',
      close: 'Закрыть',
      delete: 'Удалить',
      edit: 'Редактировать',
      settings: 'Настройки',
      language: 'Язык',
      notifications: 'Уведомления',
    },
    // Настройки
    settings: {
      title: 'Настройки',
      general: 'Общие',
      account: 'Аккаунт',
      notifications: 'Уведомления',
      ai: 'ИИ',
      calendars: 'Календари',
      language: 'Язык',
      languageSelect: 'Выберите язык',
      notificationsTitle: 'Настройки уведомлений',
      notificationsEnable: 'Включить уведомления',
      notificationsEnableDesc: 'Получать напоминания о событиях',
      notificationsWarning: 'Если выключить уведомления, то бот перестанет их присылать вам, даже если вы будете их записывать',
      morningDigest: 'Утренний дайджест',
      morningDigestDesc: 'Время ежедневного обзора событий',
      defaultReminder: 'Напоминание по умолчанию',
      defaultReminderDesc: 'Напоминание будет установлено для всех новых событий',
      reminderAtStart: 'В момент начала',
      reminderBefore5: 'За 5 минут',
      reminderBefore15: 'За 15 минут',
      reminderBefore30: 'За 30 минут',
      reminderBefore1h: 'За 1 час',
      reminderBefore1d: 'За 1 день',
      aiTitle: 'Настройки ИИ',
      aiModel: 'Модель ИИ',
      aiModelDesc: 'Выберите модель для обработки запросов',
      aiModelGpt4Mini: 'GPT-4o Mini (быстрая, экономичная)',
      aiModelGpt4: 'GPT-4o (высокое качество)',
      aiModelGpt4Turbo: 'GPT-4 Turbo',
      aiModelClaude: 'Claude 3 Haiku',
      aiInterpretation: 'Режим интерпретации',
      aiInterpretationStrict: 'Строгий',
      aiInterpretationStrictDesc: 'Точное следование инструкциям, меньше предположений',
      aiInterpretationSoft: 'Мягкий',
      aiInterpretationSoftDesc: 'Гибкая интерпретация, больше предположений и контекста',
      aiSmartReply: 'Умный ответ',
      aiSmartReplyDesc: 'Разрешить TRACY отправлять умный ответ перед созданием или обновлением события',
      aiApiKey: 'API ключ OpenRouter настраивается на сервере бота',
      profile: 'Профиль',
      firstName: 'Имя',
      lastName: 'Фамилия',
      username: 'Username',
      id: 'ID',
      connectedCalendars: 'Подключенные календари',
      connected: 'Подключен',
      notConnected: 'Не подключен',
      googleCalendar: 'Google Calendar',
      icloudCalendar: 'iCloud Calendar',
      connectInstructions: 'Инструкция по подключению',
      showInstructions: 'Показать инструкцию по подключению',
      hideInstructions: 'Скрыть инструкцию',
      settingsTitle: 'Настройки',
      tracyAssistant: 'Tracy | умный ассистент',
    },
    // Календарь
    calendar: {
      title: 'Календарь',
      today: 'Сегодня',
      noEvents: 'Нет событий',
      eventsToday: 'События на',
    },
    // Встречи
    meetings: {
      title: 'Расшифровки встреч',
      history: 'История расшифровок',
      transcribe: 'Расшифровать встречу',
    },
  },
  en: {
    // Общие
    common: {
      back: 'Back',
      save: 'Save',
      cancel: 'Cancel',
      confirm: 'Confirm',
      close: 'Close',
      delete: 'Delete',
      edit: 'Edit',
      settings: 'Settings',
      language: 'Language',
      notifications: 'Notifications',
    },
    // Настройки
    settings: {
      title: 'Settings',
      general: 'General',
      account: 'Account',
      notifications: 'Notifications',
      ai: 'AI',
      calendars: 'Calendars',
      language: 'Language',
      languageSelect: 'Select language',
      notificationsTitle: 'Notification Settings',
      notificationsEnable: 'Enable notifications',
      notificationsEnableDesc: 'Receive event reminders',
      notificationsWarning: 'If you disable notifications, the bot will stop sending them to you, even if you record them',
      morningDigest: 'Morning digest',
      morningDigestDesc: 'Daily event review time',
      defaultReminder: 'Default reminder',
      defaultReminderDesc: 'Reminder will be set for all new events',
      reminderAtStart: 'At start time',
      reminderBefore5: '5 minutes before',
      reminderBefore15: '15 minutes before',
      reminderBefore30: '30 minutes before',
      reminderBefore1h: '1 hour before',
      reminderBefore1d: '1 day before',
      aiTitle: 'AI Settings',
      aiModel: 'AI Model',
      aiModelDesc: 'Select model for request processing',
      aiModelGpt4Mini: 'GPT-4o Mini (fast, economical)',
      aiModelGpt4: 'GPT-4o (high quality)',
      aiModelGpt4Turbo: 'GPT-4 Turbo',
      aiModelClaude: 'Claude 3 Haiku',
      aiInterpretation: 'Interpretation Mode',
      aiInterpretationStrict: 'Strict',
      aiInterpretationStrictDesc: 'Exact following of instructions, fewer assumptions',
      aiInterpretationSoft: 'Soft',
      aiInterpretationSoftDesc: 'Flexible interpretation, more assumptions and context',
      aiSmartReply: 'Smart Reply',
      aiSmartReplyDesc: 'Allow TRACY to send a smart reply before creating or updating an event',
      aiApiKey: 'OpenRouter API key is configured on the bot server',
      profile: 'Profile',
      firstName: 'First Name',
      lastName: 'Last Name',
      username: 'Username',
      id: 'ID',
      connectedCalendars: 'Connected Calendars',
      connected: 'Connected',
      notConnected: 'Not Connected',
      googleCalendar: 'Google Calendar',
      icloudCalendar: 'iCloud Calendar',
      connectInstructions: 'Connection Instructions',
      showInstructions: 'Show Connection Instructions',
      hideInstructions: 'Hide Instructions',
      settingsTitle: 'Settings',
      tracyAssistant: 'Tracy | smart assistant',
    },
    // Календарь
    calendar: {
      title: 'Calendar',
      today: 'Today',
      noEvents: 'No events',
      eventsToday: 'Events on',
    },
    // Встречи
    meetings: {
      title: 'Meeting Transcripts',
      history: 'Transcription History',
      transcribe: 'Transcribe Meeting',
    },
  },
}

export function getTranslation(locale: Locale) {
  return translations[locale]
}

export function t(locale: Locale, path: string): string {
  const keys = path.split('.')
  let value: any = translations[locale]
  
  for (const key of keys) {
    if (value && typeof value === 'object' && key in value) {
      value = value[key]
    } else {
      // Fallback to Russian if translation not found
      value = translations.ru
      for (const k of keys) {
        if (value && typeof value === 'object' && k in value) {
          value = value[k]
        } else {
          return path
        }
      }
      break
    }
  }
  
  return typeof value === 'string' ? value : path
}

