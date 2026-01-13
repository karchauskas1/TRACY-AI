"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { ArrowLeft, RefreshCw, Trash2, AlertCircle, CheckCircle, Clock, XCircle } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card"
import { Button } from "../../components/ui/button"
import { getApiDebugger } from "../../lib/apiDebug"
import { getApiBaseUrl, validateApiUrl } from "../../lib/apiClient"

interface ApiDebugLog {
  url: string
  method?: string
  status?: number
  statusText?: string
  error?: string
  elapsedMs?: number
  ok?: boolean
  type?: string
  timestamp: number
  origin?: string
}

export default function DebugPage() {
  const router = useRouter()
  const [logs, setLogs] = useState<ApiDebugLog[]>([])
  const [stats, setStats] = useState<any>(null)
  const [apiUrl, setApiUrl] = useState<string>("")
  const [apiUrlValid, setApiUrlValid] = useState<boolean>(false)

  useEffect(() => {
    loadLogs()
    checkApiUrl()
    
    // Обновляем логи каждые 2 секунды
    const interval = setInterval(loadLogs, 2000)
    return () => clearInterval(interval)
  }, [])

  const loadLogs = () => {
    const apiDebug = getApiDebugger()
    setLogs(apiDebug.getLogs())
    setStats(apiDebug.getStats())
  }

  const checkApiUrl = () => {
    try {
      const url = getApiBaseUrl()
      setApiUrl(url)
      const validation = validateApiUrl()
      setApiUrlValid(validation.valid)
    } catch (e: any) {
      setApiUrl(e.message || "Ошибка получения URL")
      setApiUrlValid(false)
    }
  }

  const clearLogs = () => {
    const apiDebug = getApiDebugger()
    apiDebug.clear()
    loadLogs()
  }

  const formatTime = (timestamp: number) => {
    const date = new Date(timestamp)
    return date.toLocaleTimeString("ru-RU", { 
      hour: "2-digit", 
      minute: "2-digit", 
      second: "2-digit",
      fractionalSecondDigits: 3,
    })
  }

  const getStatusIcon = (log: ApiDebugLog) => {
    if (log.error || log.type) {
      return <XCircle className="h-4 w-4 text-destructive" />
    }
    if (log.status && log.status >= 400) {
      return <AlertCircle className="h-4 w-4 text-destructive" />
    }
    if (log.status && log.status >= 200 && log.status < 300) {
      return <CheckCircle className="h-4 w-4 text-green-500" />
    }
    if (log.elapsedMs === undefined && !log.error && !log.status) {
      return <Clock className="h-4 w-4 text-yellow-500 animate-spin" />
    }
    return null
  }

  const getStatusColor = (log: ApiDebugLog) => {
    if (log.error || log.type) {
      return "border-destructive bg-destructive/10"
    }
    if (log.status && log.status >= 400) {
      return "border-destructive bg-destructive/10"
    }
    if (log.status && log.status >= 200 && log.status < 300) {
      return "border-green-500/50 bg-green-500/10"
    }
    return "border-border"
  }

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      {/* Header */}
      <header className="sticky top-0 z-20 border-b border-border bg-background/95 backdrop-blur">
        <div className="flex h-14 items-center justify-between px-4">
          <button
            onClick={() => router.push("/assistant")}
            className="text-foreground hover:text-muted-foreground transition-colors"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-primary" />
            <span className="text-sm font-medium">API Debug</span>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="icon"
              onClick={loadLogs}
              title="Обновить"
            >
              <RefreshCw className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={clearLogs}
              title="Очистить логи"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto">
        <div className="container mx-auto max-w-4xl px-4 py-6 space-y-6">
          {/* API URL Status */}
          <Card className="border-border">
            <CardHeader>
              <CardTitle>Конфигурация API</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium">Base URL:</span>
                <code className="text-xs bg-muted px-2 py-1 rounded">
                  {apiUrl || "Не установлен"}
                </code>
                {apiUrlValid ? (
                  <CheckCircle className="h-4 w-4 text-green-500" />
                ) : (
                  <XCircle className="h-4 w-4 text-destructive" />
                )}
              </div>
              {!apiUrlValid && (
                <p className="text-sm text-destructive">
                  ⚠️ NEXT_PUBLIC_API_URL не установлен или неверен. Проверьте переменные окружения.
                </p>
              )}
              <div className="text-xs text-muted-foreground">
                Origin: {typeof window !== "undefined" ? window.location.origin : "unknown"}
              </div>
            </CardContent>
          </Card>

          {/* Statistics */}
          {stats && (
            <Card className="border-border">
              <CardHeader>
                <CardTitle>Статистика</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <div className="text-2xl font-bold">{stats.total}</div>
                    <div className="text-xs text-muted-foreground">Всего запросов</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-green-500">{stats.success}</div>
                    <div className="text-xs text-muted-foreground">Успешных</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-destructive">{stats.errors}</div>
                    <div className="text-xs text-muted-foreground">Ошибок</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-yellow-500">{stats.timeouts}</div>
                    <div className="text-xs text-muted-foreground">Таймаутов</div>
                  </div>
                </div>
                {stats.cors > 0 && (
                  <div className="mt-4 p-2 bg-destructive/10 border border-destructive/20 rounded">
                    <div className="text-sm text-destructive">
                      ⚠️ CORS ошибок: {stats.cors}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Logs */}
          <Card className="border-border">
            <CardHeader>
              <CardTitle>Последние запросы ({logs.length})</CardTitle>
            </CardHeader>
            <CardContent>
              {logs.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  Нет запросов. Откройте другие страницы приложения для генерации логов.
                </div>
              ) : (
                <div className="space-y-2">
                  {logs.map((log, index) => (
                    <div
                      key={index}
                      className={`p-3 rounded-lg border ${getStatusColor(log)}`}
                    >
                      <div className="flex items-start gap-3">
                        {getStatusIcon(log)}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-xs font-mono font-semibold">
                              {log.method || "GET"}
                            </span>
                            <span className="text-xs text-muted-foreground truncate">
                              {log.url}
                            </span>
                          </div>
                          
                          <div className="flex items-center gap-4 text-xs text-muted-foreground">
                            {log.status && (
                              <span>
                                Status: <span className="font-semibold">{log.status}</span>
                                {log.statusText && ` ${log.statusText}`}
                              </span>
                            )}
                            {log.elapsedMs !== undefined && (
                              <span>
                                Время: <span className="font-semibold">{log.elapsedMs}ms</span>
                              </span>
                            )}
                            <span>{formatTime(log.timestamp)}</span>
                          </div>
                          
                          {log.error && (
                            <div className="mt-2 p-2 bg-destructive/10 rounded text-xs">
                              <span className="font-semibold text-destructive">Ошибка:</span> {log.error}
                            </div>
                          )}
                          
                          {log.type && (
                            <div className="mt-2 p-2 bg-yellow-500/10 rounded text-xs">
                              <span className="font-semibold">Тип:</span> {log.type}
                            </div>
                          )}
                          
                          {log.origin && (
                            <div className="mt-1 text-xs text-muted-foreground">
                              Origin: {log.origin}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
