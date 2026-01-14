/**
 * Единый API клиент для всех запросов к бэкенду
 * Использует NEXT_PUBLIC_API_URL из переменных окружения
 * Добавляет таймауты, обработку ошибок и логирование
 * 
 * Автоматически использует Telegram Proxy для Mini App
 */

const DEFAULT_TIMEOUT = 15000 // 15 секунд

// === Simple client-side GET cache (memory + sessionStorage) ===
type CacheEntry = { expiresAt: number; value: any }
const memoryGetCache = new Map<string, CacheEntry>()
const SESSION_PREFIX = 'tracy_api_cache_v1:'

function safeNow(): number {
  return Date.now()
}

function getDefaultTtlMs(endpoint: string): number {
  // Keep TTLs short to avoid stale UI while still reducing repeat loads.
  if (endpoint.startsWith('/api/events')) return 60_000
  if (endpoint.startsWith('/api/meetings')) return 60_000
  if (endpoint.startsWith('/api/todo-lists') || endpoint.startsWith('/api/todo-items')) return 30_000
  if (endpoint.startsWith('/api/chat/messages')) return 10_000
  return 0
}

function cacheKeyForGet(url: string): string {
  return `${SESSION_PREFIX}GET:${url}`
}

function readCachedGet<T>(key: string): T | null {
  const now = safeNow()

  const mem = memoryGetCache.get(key)
  if (mem && mem.expiresAt > now) return mem.value as T
  if (mem && mem.expiresAt <= now) memoryGetCache.delete(key)

  if (typeof window === 'undefined') return null
  try {
    const raw = window.sessionStorage.getItem(key)
    if (!raw) return null
    const parsed = JSON.parse(raw) as CacheEntry
    if (!parsed || typeof parsed.expiresAt !== 'number') return null
    if (parsed.expiresAt <= now) {
      window.sessionStorage.removeItem(key)
      return null
    }
    memoryGetCache.set(key, parsed)
    return parsed.value as T
  } catch {
    return null
  }
}

function writeCachedGet(key: string, value: any, ttlMs: number) {
  if (!ttlMs || ttlMs <= 0) return
  const entry: CacheEntry = { expiresAt: safeNow() + ttlMs, value }
  memoryGetCache.set(key, entry)
  if (typeof window === 'undefined') return
  try {
    window.sessionStorage.setItem(key, JSON.stringify(entry))
  } catch {
    // ignore quota / serialization errors
  }
}

/**
 * Проверяет, запущено ли приложение в Telegram Mini App
 */
function isTelegramMiniApp(): boolean {
  if (typeof window === 'undefined') return false
  
  const tg = (window as any).Telegram?.WebApp
  return !!(tg && tg.initData)
}

/**
 * Проверяет, нужно ли использовать прокси
 * На Vercel всегда используем встроенный /api/proxy для единообразия
 */
function shouldUseProxy(): boolean {
  // На Vercel всегда используем прокси (проще и одинаково для всех)
  if (typeof window !== 'undefined') {
    // В продакшене (не localhost) всегда через прокси
    return window.location.hostname !== 'localhost'
  }
  return false
}

interface RequestOptions extends RequestInit {
  timeout?: number
  skipErrorLog?: boolean
  params?: Record<string, any>
  noCache?: boolean
  cacheTtlMs?: number
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
  // В production build Next.js инжектит NEXT_PUBLIC_ переменные в runtime
  // Но для статического экспорта они должны быть доступны во время сборки
  // Используем fallback на случай, если переменная не установлена
  const apiUrl = 
    (typeof window !== 'undefined' && (window as any).__NEXT_PUBLIC_API_URL__) ||
    process.env.NEXT_PUBLIC_API_URL ||
    (typeof window !== 'undefined' && window.location.hostname === 'karchauskas1.github.io' 
      ? 'https://api.pasekaproduction.ru' 
      : 'http://localhost:8080')
  
  if (!apiUrl || apiUrl.trim() === '') {
    const error = 'NEXT_PUBLIC_API_URL не установлен в переменных окружения. Проверьте настройки деплоя.'
    console.error('[apiClient] ❌', error)
    console.error('[apiClient] process.env.NEXT_PUBLIC_API_URL:', process.env.NEXT_PUBLIC_API_URL)
    console.error('[apiClient] window.__NEXT_PUBLIC_API_URL__:', typeof window !== 'undefined' ? (window as any).__NEXT_PUBLIC_API_URL__ : 'N/A')
    // Не бросаем ошибку, используем fallback
    return 'https://api.pasekaproduction.ru'
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
 * На Vercel (production) использует /api/proxy для обхода CORS
 */
export async function apiRequest<T = any>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<T> {
  const startTime = Date.now()
  
  // На production (не localhost) используем Next.js proxy
  const isLocalhost = typeof window !== 'undefined' && window.location.hostname === 'localhost'
  
  if (!isLocalhost) {
    // Production: используем /api/proxy
    console.log('[apiClient] 🔄 Using Next.js /api/proxy')
    
    try {
      const proxyResponse = await fetch('/api/proxy', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(options.headers || {}),
        },
        body: JSON.stringify({
          path: endpoint,
          method: options.method || 'GET',
          params: options.params,
          body: options.body ? JSON.parse(options.body as string) : undefined,
        }),
        signal: options.signal,
      })
      
      if (!proxyResponse.ok) {
        throw new Error(`HTTP ${proxyResponse.status}: ${proxyResponse.statusText}`)
      }
      
      const result = await proxyResponse.json()
      
      // Логируем в debug
      if (typeof window !== 'undefined' && (window as any).__API_DEBUG__) {
        (window as any).__API_DEBUG__.log({
          url: `/api/proxy -> ${endpoint}`,
          status: proxyResponse.status,
          elapsedMs: Date.now() - startTime,
          type: 'SUCCESS',
        })
      }
      
      return result as T
    } catch (error: any) {
      // Логируем ошибку
      if (typeof window !== 'undefined' && (window as any).__API_DEBUG__) {
        (window as any).__API_DEBUG__.log({
          url: `/api/proxy -> ${endpoint}`,
          error: error.message,
          elapsedMs: Date.now() - startTime,
          status: 'ERROR',
          type: 'NETWORK',
        })
      }
      throw error
    }
  }
  
  // Localhost: прямой запрос к API
  console.log('[apiClient] 🏠 Localhost - direct request')
  
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

  const ttlMs = options?.cacheTtlMs ?? getDefaultTtlMs(endpoint)
  const canCache = !options?.noCache && ttlMs > 0
  const key = cacheKeyForGet(url)

  if (canCache) {
    const cached = readCachedGet<T>(key)
    if (cached !== null) return cached
  }

  const data = await apiRequest<T>(url, { ...options, method: 'GET' })
  if (canCache) writeCachedGet(key, data, ttlMs)
  return data
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

