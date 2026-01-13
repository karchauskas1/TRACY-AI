"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { ArrowLeft, X, MessageSquare, Bug, Lightbulb, Image as ImageIcon, Loader2 } from "lucide-react"
import { Card, CardContent } from "../../../components/ui/card"

interface FeedbackItem {
  id: string
  userId: string
  type: string
  comment: string
  screenshotUrl?: string
  sheetName?: string
  sheetRowNumber?: number
  createdAt: string
}

interface FeedbackPageClientProps {
  user: {
    id: string
    name: string
    avatarUrl?: string
    first_name?: string
    last_name?: string
  } | null
}

export function FeedbackPageClient({ user: initialUser }: FeedbackPageClientProps) {
  const router = useRouter()
  const [user, setUser] = useState(initialUser)
  const [feedback, setFeedback] = useState<FeedbackItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const SUPER_USER_ID = "308477378" // ID супер-пользователя

  useEffect(() => {
    // Загружаем данные пользователя из Telegram Web App или localStorage
    if (typeof window !== "undefined") {
      const tg = (window as any).Telegram?.WebApp
      if (tg) {
        tg.ready()
        const tgUser = tg.initDataUnsafe?.user
        if (tgUser) {
          const fullName = [tgUser.first_name, tgUser.last_name].filter(Boolean).join(" ")
          const userId = tgUser.id.toString()
          setUser({
            id: userId,
            name: fullName || tgUser.first_name || "Пользователь",
            avatarUrl: tgUser.photo_url,
            first_name: tgUser.first_name,
            last_name: tgUser.last_name,
          })
        }
      } else {
        const savedUser = localStorage.getItem("telegram_user")
        if (savedUser) {
          try {
            const parsed = JSON.parse(savedUser)
            const fullName = [parsed.first_name, parsed.last_name].filter(Boolean).join(" ")
            const userId = parsed.id?.toString()
            setUser({
              ...parsed,
              id: userId,
              name: fullName || parsed.first_name || "Пользователь",
            })
          } catch (e) {
            console.error("Failed to parse user:", e)
          }
        }
      }
    }
  }, [])

  useEffect(() => {
    if (user?.id) {
      loadFeedback()
    } else {
      setLoading(false)
      setError("Пользователь не найден")
    }
  }, [user])

  const loadFeedback = async () => {
    // Получаем user_id из разных источников
    let userId: string | null = null
    
    if (user?.id) {
      userId = user.id.toString()
    } else if (typeof window !== "undefined") {
      const tg = (window as any).Telegram?.WebApp
      if (tg?.initDataUnsafe?.user?.id) {
        userId = tg.initDataUnsafe.user.id.toString()
        // Сохраняем user для будущего использования
        if (!user && userId) {
          const tgUser = tg.initDataUnsafe.user
          const fullName = [tgUser.first_name, tgUser.last_name].filter(Boolean).join(" ")
          setUser({
            id: userId,
            name: fullName || tgUser.first_name || "Пользователь",
            avatarUrl: tgUser.photo_url,
            first_name: tgUser.first_name,
            last_name: tgUser.last_name,
          })
        }
      } else {
        // Пробуем получить из localStorage
        const savedUser = localStorage.getItem("telegram_user")
        if (savedUser) {
          try {
            const parsed = JSON.parse(savedUser)
            userId = parsed.id?.toString() || null
            if (userId && !user) {
              const fullName = [parsed.first_name, parsed.last_name].filter(Boolean).join(" ")
              setUser({
                ...parsed,
                id: userId,
                name: fullName || parsed.first_name || "Пользователь",
              })
            }
          } catch (e) {
            console.error("[Feedback] Error parsing saved user:", e)
          }
        }
      }
    }
    
    if (!userId || userId === "demo" || userId === "undefined" || userId === "null") {
      console.error("[Feedback] ❌ User ID не найден или невалиден:", userId)
      setError("Не удалось определить ID пользователя. Откройте приложение через Telegram.")
      setLoading(false)
      return
    }
    
    console.log(`[Feedback] User ID: ${userId}`)

    // Проверяем, является ли пользователь супер-пользователем
    if (!userId || userId !== SUPER_USER_ID) {
      setError("Доступ запрещен. Только супер-пользователь может просматривать обратную связь.")
      setLoading(false)
      return
    }

    try {
      setLoading(true)
      setError(null)

      // ПРИОРИТЕТ 1: Прямой HTTP API запрос (работает для localhost и если нет Mixed Content блокировки)
      let apiBaseUrl = "https://api.pasekaproduction.ru"
      
      if (typeof window !== "undefined") {
        if (window.location.hostname === "localhost") {
          apiBaseUrl = "http://localhost:8080"
        } else {
          // Для GitHub Pages используем серверный API
          apiBaseUrl = "https://api.pasekaproduction.ru"
        }
      }

      console.log(`[Feedback] Запрос к API: ${apiBaseUrl}/api/feedback?user_id=${userId}&limit=100`)
      
      try {
        const response = await fetch(`${apiBaseUrl}/api/feedback?user_id=${userId}&limit=100`, {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
          },
          mode: "cors",
        })

        console.log(`[Feedback] Ответ API: status=${response.status}, ok=${response.ok}`)

        if (response.ok) {
          let data
          try {
            const responseText = await response.text()
            console.log(`[Feedback] Raw API Response:`, responseText.substring(0, 500))
            data = JSON.parse(responseText)
          } catch (e) {
            console.error(`[Feedback] Ошибка парсинга JSON:`, e)
            throw new Error("Неверный формат ответа от сервера")
          }
          
          console.log(`[Feedback] Parsed API Data:`, data)
          
          if (data.success && Array.isArray(data.feedback)) {
            console.log(`[Feedback] ✅ Успешно загружено ${data.feedback.length} записей`)
            setFeedback(data.feedback)
          } else if (Array.isArray(data.feedback)) {
            console.log(`[Feedback] ✅ Загружено ${data.feedback.length} записей (без success поля)`)
            setFeedback(data.feedback)
          } else if (data.error) {
            console.error(`[Feedback] ❌ API вернул ошибку:`, data.error)
            throw new Error(data.error || "Ошибка загрузки обратной связи")
          } else {
            console.warn(`[Feedback] ⚠️ Неожиданный формат данных:`, data)
            setFeedback([])
          }
          
          setLoading(false)
          return
        } else {
          let errorMessage = "Ошибка загрузки обратной связи"
          
          if (response.status === 403) {
            errorMessage = "Доступ запрещен. Только супер-пользователь может просматривать обратную связь."
          } else if (response.status === 400) {
            let errorData
            try {
              const responseText = await response.text()
              errorData = JSON.parse(responseText)
              if (errorData.error && errorData.error.includes("Invalid user_id")) {
                errorMessage = "Не удалось определить ID пользователя. Откройте приложение через Telegram."
              } else {
                errorMessage = errorData.error || "Неверный запрос. Проверьте параметры."
              }
            } catch {
              errorMessage = "Неверный запрос. Проверьте параметры."
            }
          } else if (response.status === 500) {
            errorMessage = "Ошибка сервера. Попробуйте позже."
          } else {
            try {
              const responseText = await response.text()
              const errorData = JSON.parse(responseText)
              errorMessage = errorData.error || `Ошибка ${response.status}: ${response.statusText}`
            } catch {
              errorMessage = `Ошибка ${response.status}: ${response.statusText}`
            }
          }
          
          console.error(`[Feedback] Ошибка API: ${errorMessage}`)
          setError(errorMessage)
          setLoading(false)
          return
        }
      } catch (fetchError: any) {
        // Если HTTP запрос не удался (Mixed Content или сеть)
        console.warn(`[Feedback] HTTP запрос не удался:`, fetchError)
        
        // Проверяем тип ошибки
        let errorMessage = "Ошибка загрузки обратной связи"
        
        if (fetchError instanceof TypeError && fetchError.message.includes("Failed to fetch")) {
          // Mixed Content Policy или проблемы с сетью
          if (window.location.protocol === "https:") {
            errorMessage = "Не удалось подключиться к серверу. Откройте приложение через Telegram для доступа к обратной связи или проверьте подключение к интернету."
          } else {
            errorMessage = "Не удалось подключиться к серверу. Проверьте подключение к интернету или попробуйте позже."
          }
        } else if (fetchError.message) {
          errorMessage = fetchError.message
        }
        
        console.error(`[Feedback] Установлена ошибка: ${errorMessage}`)
        setError(errorMessage)
        setLoading(false)
      }
    } catch (e: any) {
      console.error(`[Feedback] Исключение при загрузке:`, e)
      
      // Проверяем тип ошибки
      let errorMessage = "Ошибка загрузки обратной связи"
      
      if (e instanceof TypeError && e.message.includes("Failed to fetch")) {
        errorMessage = "Не удалось подключиться к серверу. Проверьте подключение к интернету или попробуйте позже."
      } else if (e.message) {
        errorMessage = e.message
      }
      
      console.error(`[Feedback] Установлена ошибка: ${errorMessage}`)
      setError(errorMessage)
      setLoading(false)
    }
  }

  const handleBack = () => {
    router.push("/settings")
  }

  const handleClose = () => {
    if (typeof window !== "undefined" && (window as any).Telegram?.WebApp) {
      (window as any).Telegram.WebApp.close()
    } else {
      router.push("/settings")
    }
  }

  const formatDate = (dateStr: string) => {
    try {
      const date = new Date(dateStr)
      return new Intl.DateTimeFormat("ru-RU", {
        year: "numeric",
        month: "long",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      }).format(date)
    } catch {
      return dateStr
    }
  }

  const getFeedbackTypeLabel = (type: string) => {
    return type === "баг" || type === "Баг" ? "Баг" : "Предложение"
  }

  const getFeedbackTypeIcon = (type: string) => {
    return type === "баг" || type === "Баг" ? Bug : Lightbulb
  }

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      {/* Header */}
      <header className="sticky top-0 z-20 border-b border-border bg-background/95 backdrop-blur">
        <div className="flex h-14 items-center justify-between px-4">
          <button
            onClick={handleBack}
            className="text-foreground hover:text-muted-foreground transition-colors"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div className="flex items-center gap-2">
            <MessageSquare className="h-5 w-5 text-primary" />
            <span className="text-sm font-medium">Обратная связь</span>
          </div>
          <button
            onClick={handleClose}
            className="text-foreground hover:text-muted-foreground transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto">
        <div className="container mx-auto max-w-2xl px-4 py-6">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : error ? (
            <Card className="border-border">
              <CardContent className="pt-6">
                <div className="text-center space-y-2">
                  <p className="font-medium text-destructive">{error}</p>
                  {error.includes("через Telegram") && (
                    <p className="text-sm text-muted-foreground">
                      Откройте бота в Telegram и используйте меню для доступа к обратной связи.
                    </p>
                  )}
                </div>
              </CardContent>
            </Card>
          ) : feedback.length === 0 ? (
            <Card className="border-border">
              <CardContent className="pt-6">
                <div className="text-center text-muted-foreground">
                  <MessageSquare className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>Нет записей обратной связи</p>
                </div>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {feedback.map((item) => {
                const TypeIcon = getFeedbackTypeIcon(item.type)
                const typeLabel = getFeedbackTypeLabel(item.type)
                
                return (
                  <Card key={item.id} className="border-border">
                    <CardContent className="pt-6">
                      <div className="space-y-4">
                        {/* Header */}
                        <div className="flex items-start justify-between">
                          <div className="flex items-center gap-2">
                            <TypeIcon className="h-5 w-5 text-muted-foreground" />
                            <span className="font-semibold">#{item.id}</span>
                            <span className="text-sm text-muted-foreground">•</span>
                            <span className="text-sm font-medium">{typeLabel}</span>
                          </div>
                          <span className="text-xs text-muted-foreground">
                            {formatDate(item.createdAt)}
                          </span>
                        </div>

                        {/* User ID */}
                        <div className="text-sm text-muted-foreground">
                          User ID: {item.userId}
                        </div>

                        {/* Comment */}
                        <div className="text-sm">
                          <p className="whitespace-pre-wrap">{item.comment}</p>
                        </div>

                        {/* Screenshot */}
                        {item.screenshotUrl && (
                          <div>
                            <a
                              href={item.screenshotUrl}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center gap-2 text-sm text-primary hover:underline"
                            >
                              <ImageIcon className="h-4 w-4" />
                              <span>Просмотреть скриншот</span>
                            </a>
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                )
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

