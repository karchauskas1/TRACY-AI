/**
 * Единый API клиент для всех запросов к бэкенду
 * Использует NEXT_PUBLIC_API_URL из переменных окружения
 * Добавляет таймауты, обработку ошибок и логирование
 */

const DEFAULT_TIMEOUT = 15000 // 15 секунд

interface RequestOptions extends RequestInit {
  timeout?: number
  skipErrorLog?: boolean
}

export interface ApiError {
  type: 'CORS' | 'TIMEOUT' | 'NETWORK' | 'HTTP' | 'JSON' | 'UNKNOWN'
  message: string
  status?: number
  statusText?: string
  url?: string
}

/**
 * Получает base URL API из переменных окружения
 * @throws {Error} Если NEXT_PUBLIC_API_URL не установлен
 */
export function getApiBaseUrl(): string {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL
  
  if (!apiUrl || apiUrl.trim() === '') {
    const error = 'NEXT_PUBLIC_API_URL не установлен в переменных окружения. Проверьте настройки деплоя.'
    console.error('[apiClient] ❌', error)
    throw new Error(error)
  }
  
  // Убираем trailing slash
  return apiUrl.trim().replace(/\/$/, '')
}

/**
 * Проверяет доступность API base URL
 */
export function validateApiUrl(): { valid: boolean; error?: string } {
  try {
    const url = getApiBaseUrl()
    // Простая валидация URL
    new URL(url)
    return { valid: true }
  } catch (e: any) {
    return { 
      valid: false, 
      error: `Неверный формат API URL: ${e.message}` 
    }
  }
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
    if (error.name === 'AbortError') {
      throw new Error(`TIMEOUT: Запрос превысил таймаут ${timeout}ms`)
    }
    throw error
  }
}

/**
 * Парсит ошибку и определяет её тип
 */
function parseError(error: any, url: string, response?: Response): ApiError {
  // Таймаут
  if (error.message?.includes('TIMEOUT')) {
    return {
      type: 'TIMEOUT',
      message: 'Сервер не отвечает. Попробуйте позже.',
      url,
    }
  }
  
  // CORS ошибка
  if (error instanceof TypeError && error.message.includes('Failed to fetch')) {
    // Проверяем, может ли это быть CORS
    if (url.startsWith('http://') && typeof window !== 'undefined' && window.location.protocol === 'https:') {
      return {
        type: 'CORS',
        message: 'Mixed Content: HTTP запрос заблокирован. Используйте HTTPS.',
        url,
      }
    }
    return {
      type: 'CORS',
      message: 'CORS ошибка: сервер не разрешает запросы с этого домена.',
      url,
    }
  }
  
  // HTTP ошибка
  if (response) {
    return {
      type: 'HTTP',
      message: `HTTP ${response.status}: ${response.statusText || 'Ошибка сервера'}`,
      status: response.status,
      statusText: response.statusText,
      url,
    }
  }
  
  // Сетевая ошибка
  if (error instanceof TypeError) {
    return {
      type: 'NETWORK',
      message: 'Не удалось подключиться к серверу. Проверьте подключение к интернету.',
      url,
    }
  }
  
  // Неизвестная ошибка
  return {
    type: 'UNKNOWN',
    message: error.message || 'Неизвестная ошибка',
    url,
  }
}

/**
 * Форматирует ошибку для отображения пользователю
 */
export function formatApiError(error: ApiError): string {
  const parts: string[] = []
  
  switch (error.type) {
    case 'CORS':
      parts.push('Ошибка CORS')
      break
    case 'TIMEOUT':
      parts.push('Таймаут запроса')
      break
    case 'NETWORK':
      parts.push('Сетевая ошибка')
      break
    case 'HTTP':
      parts.push(`HTTP ${error.status}`)
      break
    case 'JSON':
      parts.push('Ошибка парсинга ответа')
      break
    default:
      parts.push('Ошибка запроса')
  }
  
  if (error.message) {
    parts.push(error.message)
  }
  
  return parts.join(': ')
}

/**
 * Основная функция для выполнения API запросов
 */
export async function apiRequest<T = any>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<T> {
  const startTime = Date.now()
  
  // Получаем base URL
  let baseUrl: string
  try {
    baseUrl = getApiBaseUrl()
  } catch (e: any) {
    // Логируем в debug систему если доступна
    if (typeof window !== 'undefined' && (window as any).__API_DEBUG__) {
      (window as any).__API_DEBUG__.log({
        url: endpoint,
        error: e.message,
        elapsedMs: 0,
        status: 'ERROR',
        type: 'CONFIG',
      })
    }
    throw e
  }
  
  // Формируем полный URL
  const url = endpoint.startsWith('http') 
    ? endpoint 
    : `${baseUrl}${endpoint.startsWith('/') ? endpoint : '/' + endpoint}`
  
  // Логируем запрос в debug систему
  if (typeof window !== 'undefined' && (window as any).__API_DEBUG__) {
    (window as any).__API_DEBUG__.log({
      url,
      method: options.method || 'GET',
      startTime,
    })
  }
  
  try {
    // Выполняем запрос с таймаутом
    const response = await fetchWithTimeout(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      mode: 'cors',
    })
    
    const elapsedMs = Date.now() - startTime
    
    // Логируем ответ
    if (typeof window !== 'undefined' && (window as any).__API_DEBUG__) {
      (window as any).__API_DEBUG__.log({
        url,
        status: response.status,
        statusText: response.statusText,
        elapsedMs,
        ok: response.ok,
      })
    }
    
    // Проверяем статус ответа
    if (!response.ok) {
      let errorText = ''
      try {
        errorText = await response.text()
      } catch {
        errorText = response.statusText
      }
      
      let errorData: any = null
      try {
        errorData = JSON.parse(errorText)
      } catch {
        // Не JSON, используем текст как есть
      }
      
      const apiError: ApiError = {
        type: 'HTTP',
        message: errorData?.error || errorData?.message || errorText || `HTTP ${response.status}`,
        status: response.status,
        statusText: response.statusText,
        url,
      }
      
      if (!options.skipErrorLog) {
        console.error(`[apiClient] ❌ HTTP ${response.status} ${url}:`, apiError.message)
      }
      
      throw apiError
    }
    
    // Парсим JSON
    let data: T
    try {
      const text = await response.text()
      if (!text) {
        data = {} as T
      } else {
        data = JSON.parse(text)
      }
    } catch (e: any) {
      const apiError: ApiError = {
        type: 'JSON',
        message: `Ошибка парсинга JSON: ${e.message}`,
        url,
      }
      
      if (!options.skipErrorLog) {
        console.error(`[apiClient] ❌ JSON parse error ${url}:`, e)
      }
      
      throw apiError
    }
    
    return data
    
  } catch (error: any) {
    const elapsedMs = Date.now() - startTime
    const apiError = parseError(error, url)
    
    // Логируем ошибку
    if (typeof window !== 'undefined' && (window as any).__API_DEBUG__) {
      (window as any).__API_DEBUG__.log({
        url,
        error: apiError.message,
        elapsedMs,
        status: 'ERROR',
        type: apiError.type,
      })
    }
    
    if (!options.skipErrorLog) {
      console.error(`[apiClient] ❌ ${apiError.type} ${url}:`, apiError.message)
    }
    
    throw apiError
  }
}

/**
 * GET запрос
 */
export async function apiGet<T = any>(
  endpoint: string,
  params?: Record<string, any>,
  options?: RequestOptions
): Promise<T> {
  // Добавляем query параметры к URL
  let url = endpoint
  if (params && Object.keys(params).length > 0) {
    const queryString = new URLSearchParams(
      Object.entries(params).reduce((acc, [key, value]) => {
        if (value !== null && value !== undefined) {
          acc[key] = String(value)
        }
        return acc
      }, {} as Record<string, string>)
    ).toString()
    url = `${endpoint}${endpoint.includes('?') ? '&' : '?'}${queryString}`
  }
  
  return apiRequest<T>(url, { ...options, method: 'GET' })
}

/**
 * POST запрос
 */
export async function apiPost<T = any>(
  endpoint: string,
  data?: any,
  options?: RequestOptions
): Promise<T> {
  return apiRequest<T>(endpoint, {
    ...options,
    method: 'POST',
    body: data ? JSON.stringify(data) : undefined,
  })
}

/**
 * PUT запрос
 */
export async function apiPut<T = any>(
  endpoint: string,
  data?: any,
  options?: RequestOptions
): Promise<T> {
  return apiRequest<T>(endpoint, {
    ...options,
    method: 'PUT',
    body: data ? JSON.stringify(data) : undefined,
  })
}

/**
 * DELETE запрос
 */
export async function apiDelete<T = any>(endpoint: string, options?: RequestOptions): Promise<T> {
  return apiRequest<T>(endpoint, { ...options, method: 'DELETE' })
}

