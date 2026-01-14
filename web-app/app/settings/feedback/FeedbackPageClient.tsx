"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { ArrowLeft, X, MessageSquare, Bug, Lightbulb, Image as ImageIcon, Loader2 } from "lucide-react"
import { Card, CardContent } from "../../../components/ui/card"
import { Button } from "../../../components/ui/button"
import { getErrorDetails, formatErrorForDisplay, type ErrorDetails } from "../../../lib/error-utils"
import { apiGet, apiPost, formatApiError, type ApiError } from "../../../lib/apiClient"
import { useNavigation } from "../../../lib/useNavigation"

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
  const { handleBack } = useNavigation()
  const [user, setUser] = useState(initialUser)
  const [feedback, setFeedback] = useState<FeedbackItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [errorDetails, setErrorDetails] = useState<ErrorDetails | null>(null)
  const [selected, setSelected] = useState<FeedbackItem | null>(null)
  const SUPER_USER_ID = "308477378" // ID супер-пользователя

  useEffect(() => {
    // Загружаем данные пользователя из Telegram Web App или localStorage
    if (typeof window !== "undefined") {
      const tg = (window as any).Telegram?.WebApp
      if (tg) {
        // Telegram WebApp уже инициализирован через TelegramBootstrap
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

      // Используем единый API клиент
      const data = await apiGet<{ success?: boolean; feedback?: FeedbackItem[]; error?: string }>(
        `/api/feedback`,
        { user_id: parseInt(userId), limit: 100 },
        { timeout: 15000 }
      )
      
      if (data.success && Array.isArray(data.feedback)) {
        console.log(`[Feedback] ✅ Успешно загружено ${data.feedback.length} записей`)
        setFeedback(data.feedback)
        setError(null)
        setErrorDetails(null)
      } else if (Array.isArray(data.feedback)) {
        console.log(`[Feedback] ✅ Загружено ${data.feedback.length} записей (без success поля)`)
        setFeedback(data.feedback)
        setError(null)
        setErrorDetails(null)
      } else if (data.error) {
        console.error(`[Feedback] ❌ API вернул ошибку:`, data.error)
        throw new Error(data.error || "Ошибка загрузки обратной связи")
      } else {
        console.warn(`[Feedback] ⚠️ Неожиданный формат данных:`, data)
        setFeedback([])
        setError(null)
        setErrorDetails(null)
      }
      
      setLoading(false)
    } catch (e: any) {
      console.error(`[Feedback] Ошибка загрузки:`, e)
      
      const errorMessage = e.type 
        ? formatApiError(e)
        : (e.message || "Не удалось загрузить обратную связь")
      
      setError(errorMessage)
      setErrorDetails({
        code: String(e.status || e.type || "UNKNOWN"),
        message: e.message || errorMessage,
        context: "Загрузка обратной связи",
      })
      setLoading(false)
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
    const t = String(type || "").toLowerCase()
    if (t.includes("баг")) return "Баг"
    if (t.includes("предлож")) return "Предложение"
    if (t.includes("коммент") || t.includes("comment")) return "Комментарий"
    return type || "Сообщение"
  }

  const getFeedbackTypeIcon = (type: string) => {
    const t = String(type || "").toLowerCase()
    if (t.includes("баг")) return Bug
    if (t.includes("предлож")) return Lightbulb
    return MessageSquare
  }

  const truncate = (text: string, max = 180) => {
    const s = String(text || "")
    if (s.length <= max) return s
    return s.slice(0, max).trimEnd() + "…"
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
          <div className="w-5" /> {/* Spacer */}
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
                          <p className="whitespace-pre-wrap">{truncate(item.comment)}</p>
                        </div>

                        {/* Screenshot */}
                        {item.screenshotUrl && (
                          <button
                            type="button"
                            onClick={() => setSelected(item)}
                            className="flex items-center gap-2 text-sm text-primary hover:underline"
                          >
                            <ImageIcon className="h-4 w-4" />
                            <span>Скриншот (открыть)</span>
                          </button>
                        )}

                        <div className="pt-2">
                          <Button variant="outline" size="sm" onClick={() => setSelected(item)}>
                            Подробнее
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )
              })}
            </div>
          )}
        </div>
      </div>

      {/* Details modal */}
      {selected && (
        <div className="fixed inset-0 z-[100000] bg-black/60 flex items-center justify-center p-4">
          <div className="w-full max-w-2xl rounded-lg bg-background border border-border shadow-lg">
            <div className="flex items-center justify-between p-4 border-b border-border">
              <div className="flex items-center gap-2">
                {(() => {
                  const Icon = getFeedbackTypeIcon(selected.type)
                  return <Icon className="h-5 w-5 text-muted-foreground" />
                })()}
                <div className="font-semibold">#{selected.id} • {getFeedbackTypeLabel(selected.type)}</div>
              </div>
              <button
                type="button"
                onClick={() => setSelected(null)}
                className="text-muted-foreground hover:text-foreground transition-colors"
                aria-label="Close"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="p-4 space-y-4 max-h-[80vh] overflow-auto">
              <div className="text-sm text-muted-foreground">
                <div><span className="font-medium">User ID:</span> {selected.userId}</div>
                <div><span className="font-medium">Created:</span> {formatDate(selected.createdAt)}</div>
                {selected.sheetName && (
                  <div><span className="font-medium">Sheet:</span> {selected.sheetName}{selected.sheetRowNumber ? ` #${selected.sheetRowNumber}` : ""}</div>
                )}
              </div>

              <div className="text-sm">
                <div className="font-medium mb-2">Текст</div>
                <p className="whitespace-pre-wrap">{selected.comment}</p>
              </div>

              {selected.screenshotUrl && (
                <div className="space-y-2">
                  <div className="font-medium text-sm">Скриншот</div>
                  <a
                    href={selected.screenshotUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 text-sm text-primary hover:underline"
                  >
                    <ImageIcon className="h-4 w-4" />
                    <span>Открыть в новой вкладке</span>
                  </a>
                  <div className="rounded-md border border-border overflow-hidden bg-muted">
                    <img
                      src={selected.screenshotUrl}
                      alt="Screenshot"
                      loading="lazy"
                      className="w-full h-auto object-contain"
                    />
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

