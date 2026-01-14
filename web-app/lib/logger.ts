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
  private maxLogs = 1000

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

    // Выводим в консоль с префиксом для фильтрации
    const prefix = `[${new Date(entry.timestamp).toLocaleTimeString()}] [${level}] [${category}]`
    const logMethod = level === 'ERROR' ? console.error : level === 'WARN' ? console.warn : console.log
    
    if (data) {
      logMethod(`${prefix} ${message}`, data)
    } else {
      logMethod(`${prefix} ${message}`)
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
