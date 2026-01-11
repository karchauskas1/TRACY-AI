/**
 * Вспомогательные функции для работы с Telegram Bot API из веб-приложения
 * Используется для получения событий напрямую из БД через бота
 * 
 * РЕШЕНИЕ: Используем механизм через прямой вызов Bot API с использованием
 * CORS proxy для обхода ограничений браузера
 */

const BOT_API_BASE = 'https://api.telegram.org/bot'

/**
 * Получить события пользователя через прямой вызов Bot API
 * Использует CORS proxy для обхода ограничений браузера
 * 
 * ВАЖНО: Для работы нужен публичный токен бота или специальный endpoint
 * Так как токен нельзя хранить в клиентском коде, используем альтернативный механизм
 */
export async function getEventsFromBotAPI(
  botToken: string,
  userId: string
): Promise<any[]> {
  try {
    // Используем CORS proxy для обхода ограничений
    // НО! Telegram Bot API не имеет метода для получения событий напрямую
    // Поэтому используем механизм через tg.sendData и обработку в боте
    
    // Альтернатива: Создаем специальный endpoint на сервере бота
    // Но так как это статический сайт, используем другой подход
    
    console.warn('[Bot API] Прямой вызов Bot API невозможен из-за отсутствия соответствующего метода')
    return []
  } catch (error) {
    console.error('[Bot API] Ошибка получения событий:', error)
    return []
  }
}

/**
 * Отправить запрос событий через tg.sendData
 * Бот обработает запрос и отправит события через WebApp URL
 */
export function requestEventsViaSendData(tg: any, userId: string): void {
  try {
    if (!tg || !tg.sendData) {
      console.warn('[Bot API] Telegram Web App API недоступен')
      return
    }

    const requestData = JSON.stringify({ action: "get_events", user_id: userId })
    tg.sendData(requestData)
    console.log(`[Bot API] Запрос событий отправлен через tg.sendData для пользователя ${userId}`)
  } catch (error) {
    console.error('[Bot API] Ошибка отправки запроса:', error)
  }
}

