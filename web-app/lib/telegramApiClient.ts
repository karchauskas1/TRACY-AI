/**
 * API клиент специально для Telegram Mini App
 * Использует прокси-сервер для обхода CORS ограничений WebView
 */

const DEFAULT_TIMEOUT = 15000 // 15 секунд

interface RequestOptions extends RequestInit {
  timeout?: number
}

export interface ApiError {
  type: 'PROXY' | 'TIMEOUT' | 'NETWORK' | 'HTTP' | 'JSON' | 'UNKNOWN'
  message: string
  status?: number
  url?: string
}

/**
 * Получает base URL API из переменных окружения
 */
export function getApiBaseUrl(): string {
  const apiUrl = 
    (typeof window !== 'undefined' && (window as any).__NEXT_PUBLIC_API_URL__) ||
    process.env.NEXT_PUBLIC_API_URL ||
    (typeof window !== 'undefined' && window.location.hostname === 'karchauskas1.github.io' 
      ? 'https://api.pasekaproduction.ru' 
      : 'http://localhost:8080')
  
  return apiUrl.trim().replace(/\/$/, '')
}

/**
 * Проверяет, запущено ли приложение в Telegram Mini App
 */
export function isTelegramMiniApp(): boolean {
  if (typeof window === 'undefined') return false
  
  const tg = (window as any).Telegram?.WebApp
  return !!(tg && tg.initData)
}

/**
 * Создает fetch с таймаутом через AbortController
 */
async function fetchWithTimeout(
  url: string,
  options: RequestOptions = {}
): Promise<Response> {
  const timeout = options.timeout || DEFAULT_TIMEOUT
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), timeout)
  
  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    })
    clearTimeout(timeoutId)
    return response
  } catch (error: any) {
    clearTimeout(timeoutId)
    throw error
  }
}

/**
 * Выполняет GET запрос через Telegram Proxy
 */
export async function telegramApiGet<T = any>(
  endpoint: string,
  params?: Record<string, any>,
  options: RequestOptions = {}
): Promise<T> {
  const baseUrl = getApiBaseUrl()
  const proxyUrl = `${baseUrl}/api/telegram-proxy`
  
  console.log('[telegramApiClient] GET:', endpoint, params)
  
  try {
    const response = await fetchWithTimeout(proxyUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        endpoint,
        method: 'GET',
        params: params || {},
        data: null,
      }),
      ...options,
    })
    
    if (!response.ok) {
      const error: ApiError = {
        type: 'HTTP',
        message: `HTTP ${response.status}: ${response.statusText}`,
        status: response.status,
        url: proxyUrl,
      }
      console.error('[telegramApiClient] HTTP Error:', error)
      throw error
    }
    
    const result = await response.json()
    console.log('[telegramApiClient] ✅ Response:', result)
    return result as T
  } catch (error: any) {
    if (error.name === 'AbortError') {
      const timeoutError: ApiError = {
        type: 'TIMEOUT',
        message: 'Сервер не отвечает. Повторите попытку.',
        url: proxyUrl,
      }
      console.error('[telegramApiClient] Timeout:', timeoutError)
      throw timeoutError
    }
    
    if (error.type) {
      throw error
    }
    
    const networkError: ApiError = {
      type: 'NETWORK',
      message: error.message || 'Не удалось подключиться к серверу',
      url: proxyUrl,
    }
    console.error('[telegramApiClient] Network Error:', networkError)
    throw networkError
  }
}

/**
 * Выполняет POST запрос через Telegram Proxy
 */
export async function telegramApiPost<T = any>(
  endpoint: string,
  data?: any,
  params?: Record<string, any>,
  options: RequestOptions = {}
): Promise<T> {
  const baseUrl = getApiBaseUrl()
  const proxyUrl = `${baseUrl}/api/telegram-proxy`
  
  console.log('[telegramApiClient] POST:', endpoint, data, params)
  
  try {
    const response = await fetchWithTimeout(proxyUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        endpoint,
        method: 'POST',
        params: params || {},
        data: data || null,
      }),
      ...options,
    })
    
    if (!response.ok) {
      const error: ApiError = {
        type: 'HTTP',
        message: `HTTP ${response.status}: ${response.statusText}`,
        status: response.status,
        url: proxyUrl,
      }
      console.error('[telegramApiClient] HTTP Error:', error)
      throw error
    }
    
    const result = await response.json()
    console.log('[telegramApiClient] ✅ Response:', result)
    return result as T
  } catch (error: any) {
    if (error.name === 'AbortError') {
      const timeoutError: ApiError = {
        type: 'TIMEOUT',
        message: 'Сервер не отвечает. Повторите попытку.',
        url: proxyUrl,
      }
      console.error('[telegramApiClient] Timeout:', timeoutError)
      throw timeoutError
    }
    
    if (error.type) {
      throw error
    }
    
    const networkError: ApiError = {
        type: 'NETWORK',
      message: error.message || 'Не удалось подключиться к серверу',
      url: proxyUrl,
    }
    console.error('[telegramApiClient] Network Error:', networkError)
    throw networkError
  }
}

/**
 * Выполняет PUT запрос через Telegram Proxy
 */
export async function telegramApiPut<T = any>(
  endpoint: string,
  data?: any,
  params?: Record<string, any>,
  options: RequestOptions = {}
): Promise<T> {
  const baseUrl = getApiBaseUrl()
  const proxyUrl = `${baseUrl}/api/telegram-proxy`
  
  console.log('[telegramApiClient] PUT:', endpoint, data, params)
  
  try {
    const response = await fetchWithTimeout(proxyUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        endpoint,
        method: 'PUT',
        params: params || {},
        data: data || null,
      }),
      ...options,
    })
    
    if (!response.ok) {
      const error: ApiError = {
        type: 'HTTP',
        message: `HTTP ${response.status}: ${response.statusText}`,
        status: response.status,
        url: proxyUrl,
      }
      console.error('[telegramApiClient] HTTP Error:', error)
      throw error
    }
    
    const result = await response.json()
    console.log('[telegramApiClient] ✅ Response:', result)
    return result as T
  } catch (error: any) {
    if (error.name === 'AbortError') {
      const timeoutError: ApiError = {
        type: 'TIMEOUT',
        message: 'Сервер не отвечает. Повторите попытку.',
        url: proxyUrl,
      }
      console.error('[telegramApiClient] Timeout:', timeoutError)
      throw timeoutError
    }
    
    if (error.type) {
      throw error
    }
    
    const networkError: ApiError = {
      type: 'NETWORK',
      message: error.message || 'Не удалось подключиться к серверу',
      url: proxyUrl,
    }
    console.error('[telegramApiClient] Network Error:', networkError)
    throw networkError
  }
}

/**
 * Выполняет DELETE запрос через Telegram Proxy
 */
export async function telegramApiDelete<T = any>(
  endpoint: string,
  params?: Record<string, any>,
  options: RequestOptions = {}
): Promise<T> {
  const baseUrl = getApiBaseUrl()
  const proxyUrl = `${baseUrl}/api/telegram-proxy`
  
  console.log('[telegramApiClient] DELETE:', endpoint, params)
  
  try {
    const response = await fetchWithTimeout(proxyUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        endpoint,
        method: 'DELETE',
        params: params || {},
        data: null,
      }),
      ...options,
    })
    
    if (!response.ok) {
      const error: ApiError = {
        type: 'HTTP',
        message: `HTTP ${response.status}: ${response.statusText}`,
        status: response.status,
        url: proxyUrl,
      }
      console.error('[telegramApiClient] HTTP Error:', error)
      throw error
    }
    
    const result = await response.json()
    console.log('[telegramApiClient] ✅ Response:', result)
    return result as T
  } catch (error: any) {
    if (error.name === 'AbortError') {
      const timeoutError: ApiError = {
        type: 'TIMEOUT',
        message: 'Сервер не отвечает. Повторите попытку.',
        url: proxyUrl,
      }
      console.error('[telegramApiClient] Timeout:', timeoutError)
      throw timeoutError
    }
    
    if (error.type) {
      throw error
    }
    
    const networkError: ApiError = {
      type: 'NETWORK',
      message: error.message || 'Не удалось подключиться к серверу',
      url: proxyUrl,
    }
    console.error('[telegramApiClient] Network Error:', networkError)
    throw networkError
  }
}

/**
 * Форматирует ошибку API для отображения пользователю
 */
export function formatTelegramApiError(error: ApiError): string {
  switch (error.type) {
    case 'TIMEOUT':
      return 'Сервер не отвечает. Проверьте подключение к интернету и повторите попытку.'
    case 'NETWORK':
      return `Сетевая ошибка: ${error.message}. Проверьте подключение к интернету.`
    case 'HTTP':
      return `Ошибка сервера (${error.status}): ${error.message}`
    case 'PROXY':
      return `Ошибка прокси: ${error.message}`
    case 'JSON':
      return 'Ошибка обработки данных от сервера.'
    default:
      return `Неизвестная ошибка: ${error.message}`
  }
}

