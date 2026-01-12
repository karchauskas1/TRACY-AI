"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { ArrowLeft, X, MessageSquare, Bug, Lightbulb, Image as ImageIcon, Loader2 } from "lucide-react"
import { Card, CardContent } from "../../../components/ui/card"

interface FeedbackItem {
  id: number
  user_id: number
  feedback_type: string
  comment: string
  screenshot_url?: string
  created_at: string
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
    if (!user?.id) {
      setError("Пользователь не найден")
      setLoading(false)
      return
    }

    // Проверяем, является ли пользователь супер-пользователем
    if (user.id !== SUPER_USER_ID) {
      setError("Доступ запрещен. Только супер-пользователь может просматривать обратную связь.")
      setLoading(false)
      return
    }

    try {
      setLoading(true)
      setError(null)

      // Получаем API URL
      let apiBaseUrl = "http://5.35.126.42:8080"
      
      // Если открыто через Telegram Web App, используем серверный API
      if (typeof window !== "undefined" && (window as any).Telegram?.WebApp) {
        apiBaseUrl = "http://5.35.126.42:8080"
      } else if (typeof window !== "undefined" && window.location.hostname === "localhost") {
        apiBaseUrl = "http://localhost:8080"
      }

      console.log(`[Feedback] Запрос к API: ${apiBaseUrl}/api/feedback?user_id=${user.id}&limit=100`)
      
      const response = await fetch(`${apiBaseUrl}/api/feedback?user_id=${user.id}&limit=100`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
        mode: "cors",
      })

      console.log(`[Feedback] Ответ API: status=${response.status}, ok=${response.ok}`)

      if (!response.ok) {
        let errorMessage = "Ошибка загрузки обратной связи"
        
        if (response.status === 403) {
          errorMessage = "Доступ запрещен. Только супер-пользователь может просматривать обратную связь."
        } else if (response.status === 400) {
          errorMessage = "Неверный запрос. Проверьте параметры."
        } else if (response.status === 500) {
          errorMessage = "Ошибка сервера. Попробуйте позже."
        } else {
          try {
            const errorData = await response.json()
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

      const data = await response.json()
      console.log(`[Feedback] Получено данных:`, data)
      setFeedback(data.feedback || [])
      setLoading(false)
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
                <div className="text-center text-destructive">
                  <p className="font-medium">{error}</p>
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
                const TypeIcon = getFeedbackTypeIcon(item.feedback_type)
                const typeLabel = getFeedbackTypeLabel(item.feedback_type)
                
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
                            {formatDate(item.created_at)}
                          </span>
                        </div>

                        {/* User ID */}
                        <div className="text-sm text-muted-foreground">
                          User ID: {item.user_id}
                        </div>

                        {/* Comment */}
                        <div className="text-sm">
                          <p className="whitespace-pre-wrap">{item.comment}</p>
                        </div>

                        {/* Screenshot */}
                        {item.screenshot_url && (
                          <div>
                            <a
                              href={item.screenshot_url}
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

