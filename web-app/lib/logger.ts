/**
 * Структурированное логирование для диагностики
 */

interface LogEntry {
  timestamp: number
  level: 'INFO' | 'WARN' | 'ERROR' | 'DEBUG'
  category: string
  message: string
  data?: any
}

class Logger {
  private logs: LogEntry[] = []
  private maxLogs = 50 // Ограничиваем до 50 последних событий
  private consoleEnabled = true
  private lastLogTime: { [key: string]: number } = {}
  private throttleMs = 100 // Минимум 100мс между одинаковыми логами

  log(level: LogEntry['level'], category: string, message: string, data?: any) {
    const entry: LogEntry = {
      timestamp: Date.now(),
      level,
      category,
      message,
      data,
    }

    this.logs.push(entry)
    if (this.logs.length > this.maxLogs) {
      this.logs.shift()
    }

    // В консоль выводим ТОЛЬКО критичные ошибки и важные события
    // Остальное только в store для экспорта
    const shouldLogToConsole = 
      level === 'ERROR' || 
      level === 'WARN' ||
      (level === 'INFO' && (category === 'AssistantPage' && message.includes('router.push') || message.includes('Pathname changed')))

    if (shouldLogToConsole && this.consoleEnabled) {
      // Throttle для предотвращения спама одинаковых логов
      const logKey = `${category}:${message}`
      const now = Date.now()
      const lastTime = this.lastLogTime[logKey] || 0
      
      if (now - lastTime > this.throttleMs) {
        this.lastLogTime[logKey] = now
        
        const prefix = `[${new Date(entry.timestamp).toLocaleTimeString()}] [${level}] [${category}]`
        const logMethod = level === 'ERROR' ? console.error : level === 'WARN' ? console.warn : console.log
        
        if (data) {
          logMethod(`${prefix} ${message}`, data)
        } else {
          logMethod(`${prefix} ${message}`)
        }
      }
    }
  }

  info(category: string, message: string, data?: any) {
    this.log('INFO', category, message, data)
  }

  warn(category: string, message: string, data?: any) {
    this.log('WARN', category, message, data)
  }

  error(category: string, message: string, data?: any) {
    this.log('ERROR', category, message, data)
  }

  debug(category: string, message: string, data?: any) {
    this.log('DEBUG', category, message, data)
  }

  // Получить все логи в формате для отправки
  getLogs(): LogEntry[] {
    return [...this.logs]
  }

  // Получить логи в текстовом формате
  getLogsAsText(): string {
    return this.logs
      .map((entry) => {
        const time = new Date(entry.timestamp).toISOString()
        const dataStr = entry.data ? ` | Data: ${JSON.stringify(entry.data)}` : ''
        return `${time} [${entry.level}] [${entry.category}] ${entry.message}${dataStr}`
      })
      .join('\n')
  }

  // Экспорт логов для отправки
  exportLogs(): string {
    const summary = {
      totalLogs: this.logs.length,
      errors: this.logs.filter((l) => l.level === 'ERROR').length,
      warnings: this.logs.filter((l) => l.level === 'WARN').length,
      logs: this.getLogs(),
    }
    return JSON.stringify(summary, null, 2)
  }

  // Очистить логи
  clear() {
    this.logs = []
  }
}

// Глобальный экземпляр
export const logger = new Logger()

// Экспорт в window для доступа из консоли
if (typeof window !== 'undefined') {
  ;(window as any).__TRACY_LOGGER = logger
}
