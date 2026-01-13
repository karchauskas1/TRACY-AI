/**
 * Система отладки API запросов
 * Логирует все сетевые запросы для диагностики
 */

interface ApiDebugLog {
  url: string
  method?: string
  status?: number
  statusText?: string
  error?: string
  elapsedMs?: number
  ok?: boolean
  type?: string
  startTime?: number
  timestamp: number
  origin?: string
}

class ApiDebugger {
  private logs: ApiDebugLog[] = []
  private maxLogs = 20

  log(entry: Partial<ApiDebugLog>) {
    const logEntry: ApiDebugLog = {
      ...entry,
      timestamp: Date.now(),
      origin: typeof window !== 'undefined' ? window.location.origin : 'unknown',
    } as ApiDebugLog

    this.logs.unshift(logEntry)
    
    // Ограничиваем количество логов
    if (this.logs.length > this.maxLogs) {
      this.logs = this.logs.slice(0, this.maxLogs)
    }

    // Логируем в консоль для разработки
    if (process.env.NODE_ENV === 'development') {
      console.log('[API Debug]', logEntry)
    }
  }

  getLogs(): ApiDebugLog[] {
    return [...this.logs]
  }

  clear() {
    this.logs = []
  }

  getStats() {
    const total = this.logs.length
    const errors = this.logs.filter(l => l.error || (l.status && l.status >= 400)).length
    const timeouts = this.logs.filter(l => l.type === 'TIMEOUT').length
    const cors = this.logs.filter(l => l.type === 'CORS').length
    
    return {
      total,
      errors,
      timeouts,
      cors,
      success: total - errors,
    }
  }
}

// Создаем глобальный экземпляр
if (typeof window !== 'undefined') {
  (window as any).__API_DEBUG__ = new ApiDebugger()
}

export function getApiDebugger(): ApiDebugger {
  if (typeof window !== 'undefined' && (window as any).__API_DEBUG__) {
    return (window as any).__API_DEBUG__
  }
  return new ApiDebugger()
}

