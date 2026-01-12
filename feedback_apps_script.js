/**
 * Google Apps Script для обработки обратной связи TRACY Bot
 * 
 * Инструкция по установке:
 * 1. Открой Google Sheets таблицу
 * 2. Расширения → Apps Script
 * 3. Вставь этот код
 * 4. Сохрани (Ctrl+S / Cmd+S)
 * 5. Запусти функцию onOpen() для создания меню (или она создастся автоматически)
 * 
 * Использование:
 * - Данные можно добавлять через функцию addFeedback()
 * - Или через HTTP запрос к функции doPost() (если развернуть как веб-приложение)
 */

// ID таблицы (оставь пустым, если скрипт привязан к таблице)
// Если скрипт запускается из другой таблицы, укажи ID здесь
const SPREADSHEET_ID = ''; // Оставь пустым для использования текущей таблицы

// Название листа по умолчанию
const DEFAULT_SHEET_NAME = 'Общий';

// Маппинг user_id -> название листа
const SHEET_MAPPING = {
  '332023536': 'Тестировщик Катя',
  // Добавь другие user_id здесь:
  // '123456789': 'Название листа',
};

/**
 * Получить или создать таблицу
 */
function getSpreadsheet() {
  if (!SPREADSHEET_ID || SPREADSHEET_ID === '') {
    // Если ID не указан, используем текущую таблицу (к которой привязан скрипт)
    return SpreadsheetApp.getActiveSpreadsheet();
  }
  return SpreadsheetApp.openById(SPREADSHEET_ID);
}

/**
 * Получить или создать лист
 */
function getOrCreateSheet(sheetName) {
  const ss = getSpreadsheet();
  let sheet = ss.getSheetByName(sheetName);
  
  if (!sheet) {
    // Создаем новый лист
    sheet = ss.insertSheet(sheetName);
    
    // Добавляем заголовки
    const headers = [['№', 'Дата', 'Тип', 'User ID', 'Комментарий', 'Ссылка на скриншот']];
    sheet.getRange(1, 1, 1, 6).setValues(headers);
    
    // Форматируем заголовки
    const headerRange = sheet.getRange(1, 1, 1, 6);
    headerRange.setFontWeight('bold');
    headerRange.setBackground('#4285f4');
    headerRange.setFontColor('#ffffff');
    
    // Настраиваем ширину колонок
    sheet.setColumnWidth(1, 50);  // №
    sheet.setColumnWidth(2, 150);  // Дата
    sheet.setColumnWidth(3, 100);  // Тип
    sheet.setColumnWidth(4, 100);  // User ID
    sheet.setColumnWidth(5, 400); // Комментарий
    sheet.setColumnWidth(6, 300); // Ссылка на скриншот
  }
  
  return sheet;
}

/**
 * Получить название листа для user_id
 */
function getSheetNameForUser(userId) {
  const userIdStr = String(userId);
  return SHEET_MAPPING[userIdStr] || DEFAULT_SHEET_NAME;
}

/**
 * Добавить обратную связь в таблицу
 * 
 * @param {string} feedbackType - Тип обратной связи ("баг" или "предложение")
 * @param {string} userId - Telegram user ID
 * @param {string} comment - Текст комментария
 * @param {string} screenshotUrl - Ссылка на скриншот (опционально)
 * @return {Object} Результат с номером записи и датой
 */
function addFeedback(feedbackType, userId, comment, screenshotUrl) {
  try {
    const sheetName = getSheetNameForUser(userId);
    const sheet = getOrCreateSheet(sheetName);
    
    // Получаем последний номер
    const lastRow = sheet.getLastRow();
    const nextNumber = lastRow; // Номер = номер строки (первая строка - заголовок)
    
    // Форматируем дату
    const now = new Date();
    const dateStr = Utilities.formatDate(now, Session.getScriptTimeZone(), 'yyyy-MM-dd HH:mm:ss');
    
    // Подготавливаем данные
    const rowData = [
      nextNumber,
      dateStr,
      feedbackType,
      String(userId),
      comment,
      screenshotUrl || ''
    ];
    
    // Записываем данные
    sheet.appendRow(rowData);
    
    // Форматируем строку
    const newRow = lastRow + 1;
    const rowRange = sheet.getRange(newRow, 1, 1, 6);
    
    // Добавляем ссылку на скриншот, если есть
    if (screenshotUrl) {
      const linkCell = sheet.getRange(newRow, 6);
      linkCell.setFormula('=HYPERLINK("' + screenshotUrl + '"; "Открыть скриншот")');
    }
    
    // Чередование цветов для читаемости
    if (newRow % 2 === 0) {
      rowRange.setBackground('#f8f9fa');
    }
    
    return {
      success: true,
      number: nextNumber,
      date: dateStr,
      sheet: sheetName
    };
  } catch (error) {
    Logger.log('Ошибка добавления обратной связи: ' + error.toString());
    return {
      success: false,
      error: error.toString()
    };
  }
}

/**
 * HTTP POST обработчик для веб-запросов
 * Можно использовать как webhook из Python бота
 * 
 * Формат запроса:
 * POST с JSON:
 * {
 *   "type": "баг" или "предложение",
 *   "user_id": "123456789",
 *   "comment": "Текст комментария",
 *   "screenshot_url": "https://..." (опционально)
 * }
 */
function doPost(e) {
  try {
    // Парсим JSON из запроса
    const data = JSON.parse(e.postData.contents);
    
    const feedbackType = data.type || data.feedback_type;
    const userId = data.user_id || data.userId;
    const comment = data.comment;
    const screenshotUrl = data.screenshot_url || data.screenshotUrl || '';
    
    // Валидация
    if (!feedbackType || !userId || !comment) {
      return ContentService.createTextOutput(JSON.stringify({
        success: false,
        error: 'Недостаточно данных: требуется type, user_id, comment'
      })).setMimeType(ContentService.MimeType.JSON);
    }
    
    // Добавляем обратную связь
    const result = addFeedback(feedbackType, userId, comment, screenshotUrl);
    
    return ContentService.createTextOutput(JSON.stringify(result))
      .setMimeType(ContentService.MimeType.JSON);
      
  } catch (error) {
    Logger.log('Ошибка обработки POST запроса: ' + error.toString());
    return ContentService.createTextOutput(JSON.stringify({
      success: false,
      error: error.toString()
    })).setMimeType(ContentService.MimeType.JSON);
  }
}

/**
 * HTTP GET обработчик (для тестирования)
 */
function doGet(e) {
  const params = e.parameter;
  
  if (params.action === 'test') {
    // Тестовая функция
    const result = addFeedback(
      'тест',
      '332023536',
      'Тестовое сообщение из Apps Script',
      'https://example.com/test.jpg'
    );
    
    return ContentService.createTextOutput(JSON.stringify(result))
      .setMimeType(ContentService.MimeType.JSON);
  }
  
  return ContentService.createTextOutput('TRACY Feedback Apps Script\n\nИспользуй POST запрос для добавления обратной связи.')
    .setMimeType(ContentService.MimeType.TEXT);
}

/**
 * Создает меню в Google Sheets
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('TRACY Feedback')
    .addItem('Добавить тестовую запись', 'testAddFeedback')
    .addItem('Создать лист "Тестировщик Катя"', 'createTestSheet')
    .addSeparator()
    .addItem('Показать маппинг user_id', 'showMapping')
    .addToUi();
}

/**
 * Тестовая функция для добавления обратной связи
 */
function testAddFeedback() {
  const result = addFeedback(
    'предложение',
    '332023536',
    'Тестовое сообщение из меню Apps Script',
    'https://example.com/test.jpg'
  );
  
  SpreadsheetApp.getUi().alert(
    result.success 
      ? '✅ Запись добавлена!\n\nНомер: #' + result.number + '\nЛист: ' + result.sheet
      : '❌ Ошибка: ' + result.error
  );
}

/**
 * Создать лист "Тестировщик Катя"
 */
function createTestSheet() {
  const sheet = getOrCreateSheet('Тестировщик Катя');
  SpreadsheetApp.getUi().alert('✅ Лист "Тестировщик Катя" создан или уже существует');
}

/**
 * Показать текущий маппинг user_id
 */
function showMapping() {
  const mappingText = Object.entries(SHEET_MAPPING)
    .map(([userId, sheetName]) => `User ID: ${userId} → Лист: "${sheetName}"`)
    .join('\n');
  
  SpreadsheetApp.getUi().alert(
    'Текущий маппинг user_id:\n\n' + 
    mappingText + 
    '\n\nОстальные → "' + DEFAULT_SHEET_NAME + '"'
  );
}

/**
 * Получить URL веб-приложения (для использования как webhook)
 * 
 * Инструкция:
 * 1. В редакторе Apps Script: Развернуть → Новое развертывание
 * 2. Тип: Веб-приложение
 * 3. Выполнять от имени: Меня
 * 4. У кого есть доступ: Все
 * 5. Скопируй URL развертывания
 * 6. Используй этот URL в Python боте для отправки данных
 */
function getWebAppUrl() {
  // Эта функция просто для справки
  // Реальный URL получишь после развертывания веб-приложения
  Logger.log('Для получения URL веб-приложения:');
  Logger.log('1. Развернуть → Новое развертывание');
  Logger.log('2. Тип: Веб-приложение');
  Logger.log('3. Скопируй URL');
}

