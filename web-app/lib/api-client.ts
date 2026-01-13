/**
 * Единый API клиент для всех запросов к бэкенду
 * Использует NEXT_PUBLIC_API_URL из переменных окружения
 */

export interface ApiRequestOptions extends RequestInit {
  timeout?: number // Таймаут в миллисекундах (по умолчанию 15000)
  retries?: number // Количество попыток (по умолчанию 0)
  retryDelay?: number // Задержка между попытками в мс (по умолчанию 1000)
}

export interface ApiError {
  type: 'CORS' | 'TIMEOUT' | 'NETWORK' | 'HTTP' | 'JSON' | 'ABORT' | 'UNKNOWN'
  message: string
  status?: number
  statusText?: string
  url?: string
  originalError?: any
}

export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  error?: ApiError
}

// Глобальный счетчик запросов для debug
let requestCounter = 0
export const requestLog: Array<{
  id: number
  url: string
  method: string
  status?: number
  error?: string
  elapsedMs: number
  timestamp: number
  origin: string
}> = []

const MAX_LOG_SIZE = 20

/**
 * Получает base URL API из переменных окружения
 */
function getApiBaseUrl(): string {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL
  
  if (!apiUrl || apiUrl.trim() === '') {
    const error = 'NEXT_PUBLIC_API_URL не установлен в переменных окружения'
    console.error(`[ApiClient] ❌ ${error}`)
    throw new Error(error)
  }
  
  // Убираем trailing slash
  return apiUrl.trim().replace(/\/$/, '')
}

/**
 * Создает полный URL для API запроса
 */
function buildApiUrl(endpoint: string): string {
  const baseUrl = getApiBaseUrl()
  // Убираем leading slash из endpoint, если есть
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint
  return `${baseUrl}/${cleanEndpoint}`
}

/**
 * Определяет тип ошибки из исключения
 */
function classifyError(error: any, url: string): ApiError {
  if (error.name === 'AbortError' || error.name === 'TimeoutError') {
    return {
      type: 'TIMEOUT',
      message: 'Превышено время ожидания ответа от сервера',
      url,
      originalError: error,
    }
  }
  
  if (error instanceof TypeError) {
    if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
      // Проверяем, может ли это быть CORS
      if (error.message.includes('CORS') || error.message.includes('cross-origin')) {
        return {
          type: 'CORS',
          message: 'CORS блокировка: сервер не разрешает запросы с этого домена',
          url,
          originalError: error,
        }
      }
      return {
        type: 'NETWORK',
        message: 'Не удалось подключиться к серверу. Проверьте подключение к интернету',
        url,
        originalError: error,
      }
    }
  }
  
  if (error.message && error.message.includes('JSON')) {
    return {
      type: 'JSON',
      message: 'Неверный формат ответа от сервера (не JSON)',
      url,
      originalError: error,
    }
  }
  
  return {
    type: 'UNKNOWN',
    message: error.message || 'Неизвестная ошибка',
    url,
    originalError: error,
  }
}

/**
 * Выполняет HTTP запрос с таймаутом и retry логикой
 */
export async function apiRequest<T = any>(
  endpoint: string,
  options: ApiRequestOptions = {}
): Promise<ApiResponse<T>> {
  const {
    timeout = 15000,
    retries = 0,
    retryDelay = 1000,
    ...fetchOptions
  } = options
  
  const url = buildApiUrl(endpoint)
  const method = fetchOptions.method || 'GET'
  const requestId = ++requestCounter
  const startTime = Date.now()
  
  // Логируем начало запроса
  console.log(`[ApiClient] ${method} ${url} (request #${requestId})`)
  
  const performRequest = async (attempt: number): Promise<ApiResponse<T>> => {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => {
      controller.abort()
    }, timeout)
    
    try {
      const response = await fetch(url, {
        ...fetchOptions,
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          ...fetchOptions.headers,
        },
      })
      
      clearTimeout(timeoutId)
      
      const elapsedMs = Date.now() - startTime
      
      // Логируем успешный ответ
      requestLog.push({
        id: requestId,
        url,
        method,
        status: response.status,
        elapsedMs,
        timestamp: Date.now(),
        origin: typeof window !== 'undefined' ? window.location.origin : 'server',
      })
      
      // Ограничиваем размер лога
      if (requestLog.length > MAX_LOG_SIZE) {
        requestLog.shift()
      }
      
      if (!response.ok) {
        let errorText = ''
        try {
          errorText = await response.text()
        } catch {
          errorText = response.statusText
        }
        
        let errorData: any = {}
        try {
          errorData = JSON.parse(errorText)
        } catch {
          // Игнорируем ошибку парсинга
        }
        
        const error: ApiError = {
          type: 'HTTP',
          message: errorData.error || errorText || `HTTP ${response.status}: ${response.statusText}`,
          status: response.status,
          statusText: response.statusText,
          url,
        }
        
        console.error(`[ApiClient] ❌ ${method} ${url} failed: ${response.status} ${response.statusText}`)
        
        return {
          success: false,
          error,
        }
      }
      
      // Парсим JSON ответ
      let data: T
      try {
        const text = await response.text()
        if (!text) {
          data = {} as T
        } else {
          data = JSON.parse(text)
        }
      } catch (parseError: any) {
        const error: ApiError = {
          type: 'JSON',
          message: 'Неверный формат JSON ответа от сервера',
          url,
          originalError: parseError,
        }
        
        console.error(`[ApiClient] ❌ ${method} ${url} JSON parse error:`, parseError)
        
        return {
          success: false,
          error,
        }
      }
      
      console.log(`[ApiClient] ✅ ${method} ${url} success (${elapsedMs}ms)`)
      
      return {
        success: true,
        data,
      }
    } catch (error: any) {
      clearTimeout(timeoutId)
      
      const elapsedMs = Date.now() - startTime
      const apiError = classifyError(error, url)
      
      // Логируем ошибку
      requestLog.push({
        id: requestId,
        url,
        method,
        error: apiError.message,
        elapsedMs,
        timestamp: Date.now(),
        origin: typeof window !== 'undefined' ? window.location.origin : 'server',
      })
      
      // Ограничиваем размер лога
      if (requestLog.length > MAX_LOG_SIZE) {
        requestLog.shift()
      }
      
      console.error(`[ApiClient] ❌ ${method} ${url} error (attempt ${attempt}):`, apiError)
      
      // Retry логика
      if (attempt < retries && (apiError.type === 'NETWORK' || apiError.type === 'TIMEOUT')) {
        console.log(`[ApiClient] 🔄 Retrying ${method} ${url} (attempt ${attempt + 1}/${retries})...`)
        await new Promise(resolve => setTimeout(resolve, retryDelay))
        return performRequest(attempt + 1)
      }
      
      return {
        success: false,
        error: apiError,
      }
    }
  }
  
  return performRequest(0)
}

/**
 * GET запрос
 */
export async function apiGet<T = any>(
  endpoint: string,
  params?: Record<string, string | number>,
  options?: Omit<ApiRequestOptions, 'method' | 'body'>
): Promise<ApiResponse<T>> {
  let url = endpoint
  if (params) {
    const searchParams = new URLSearchParams()
    Object.entries(params).forEach(([key, value]) => {
      searchParams.append(key, String(value))
    })
    url = `${endpoint}?${searchParams.toString()}`
  }
  
  return apiRequest<T>(url, {
    ...options,
    method: 'GET',
  })
}

/**
 * POST запрос
 */
export async function apiPost<T = any>(
  endpoint: string,
  body?: any,
  options?: Omit<ApiRequestOptions, 'method' | 'body'>
): Promise<ApiResponse<T>> {
  return apiRequest<T>(endpoint, {
    ...options,
    method: 'POST',
    body: body ? JSON.stringify(body) : undefined,
  })
}

/**
 * PUT запрос
 */
export async function apiPut<T = any>(
  endpoint: string,
  body?: any,
  options?: Omit<ApiRequestOptions, 'method' | 'body'>
): Promise<ApiResponse<T>> {
  return apiRequest<T>(endpoint, {
    ...options,
    method: 'PUT',
    body: body ? JSON.stringify(body) : undefined,
  })
}

/**
 * DELETE запрос
 */
export async function apiDelete<T = any>(
  endpoint: string,
  options?: Omit<ApiRequestOptions, 'method' | 'body'>
): Promise<ApiResponse<T>> {
  return apiRequest<T>(endpoint, {
    ...options,
    method: 'DELETE',
  })
}

/**
 * Форматирует ошибку для отображения пользователю
 */
export function formatApiError(error: ApiError): string {
  switch (error.type) {
    case 'CORS':
      return 'CORS блокировка: сервер не разрешает запросы с этого домена'
    case 'TIMEOUT':
      return 'Сервер не отвечает. Попробуйте повторить запрос'
    case 'NETWORK':
      return 'Не удалось подключиться к серверу. Проверьте подключение к интернету'
    case 'HTTP':
      return error.message || `Ошибка сервера: ${error.status} ${error.statusText}`
    case 'JSON':
      return 'Неверный формат ответа от сервера'
    case 'ABORT':
      return 'Запрос был отменен'
    default:
      return error.message || 'Неизвестная ошибка'
  }
}

