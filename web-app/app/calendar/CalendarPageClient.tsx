"use client"

import { useState, useEffect } from "react"
import { format, isSameDay } from "date-fns"
import { ru } from "date-fns/locale"
import { Settings, X, MessageCircle, Send, Calendar as CalendarIcon } from "lucide-react"
import Link from "next/link"
import { CalendarGrid } from "../../components/calendar/CalendarGrid"
import { Button } from "../../components/ui/button"
import { formatTime } from "../../lib/utils"
import { getErrorDetails, formatErrorForDisplay, type ErrorDetails } from "../../lib/error-utils"
import { apiGet, formatApiError, type ApiError } from "../../lib/apiClient"
import { useTelegramUser } from "../../lib/useTelegramUser"

interface Event {
  id: string
  title: string
  startAt: string
  endAt?: string
  allDay: boolean
  calendarSource?: {
    color: string
    name: string
  }
}

export function CalendarPageClient() {
  const [selectedDate, setSelectedDate] = useState(new Date())
  const [events, setEvents] = useState<Event[]>([])
  const [eventsByDate, setEventsByDate] = useState<Record<string, number>>({})
  const [loading, setLoading] = useState(false) // Начинаем с false, ждем user_id
  const [error, setError] = useState<string | null>(null)
  const [errorDetails, setErrorDetails] = useState<ErrorDetails | null>(null)
  
  // Используем хук для получения user_id
  const { user, userId, isLoading: userLoading, error: userError } = useTelegramUser()

  const loadEvents = async (forceRefresh: boolean = false) => {
    // Ждем, пока user_id будет получен
    if (userLoading) {
      console.log("[Calendar] Ожидание user_id...")
      return
    }
    
    if (!userId || userId === "demo" || userId === "undefined" || userId === "null") {
      console.error("[Calendar] ❌ User ID не найден или невалиден:", userId)
      if (userError) {
        setError(userError)
        setErrorDetails({
          code: "AUTH_ERROR",
          message: userError,
          context: "Загрузка событий календаря",
        })
      }
      setLoading(false)
      return
    }
    
    if (forceRefresh) {
      setLoading(true)
    }
    
    // Проверяем, открыто ли через Telegram Web App
    const tg = typeof window !== "undefined" ? (window as any).Telegram?.WebApp : null
    if (tg) {
      tg.ready()
      tg.expand()
    }
    
    // Сначала загружаем из localStorage для быстрого отображения
    const storedEvents = localStorage.getItem("tracy_events")
    if (storedEvents && !forceRefresh) {
      try {
        const parsedEvents = JSON.parse(storedEvents)
        if (Array.isArray(parsedEvents) && parsedEvents.length > 0) {
          console.log(`[Calendar] Загружено ${parsedEvents.length} событий из localStorage`)
          setEvents(parsedEvents)
          
          const counts: Record<string, number> = {}
          parsedEvents.forEach((event: Event) => {
            try {
              const dateKey = format(new Date(event.startAt), "yyyy-MM-dd")
              counts[dateKey] = (counts[dateKey] || 0) + 1
            } catch (e) {
              console.error("Error parsing event date:", e, event)
            }
          })
          setEventsByDate(counts)
          setLoading(false)
        }
      } catch (e) {
        console.error("[Calendar] Error parsing stored events:", e)
      }
    }
    
    // Используем единый API клиент
    try {
      const data = await apiGet<{ success?: boolean; events?: Event[]; error?: string; timestamp?: string }>(
        `/api/events`,
        { user_id: parseInt(userId) },
        { timeout: 15000 }
      )
      
      // Обрабатываем разные форматы ответа
      let eventsArray: Event[] = []
      if (data.success && Array.isArray(data.events)) {
        eventsArray = data.events
      } else if (Array.isArray(data.events)) {
        eventsArray = data.events
      } else if (Array.isArray(data)) {
        eventsArray = data
      } else if (data.error) {
        throw new Error(data.error)
      }
      
      if (eventsArray.length > 0) {
        console.log(`[Calendar] ✅ Получено ${eventsArray.length} событий через API`)
        setEvents(eventsArray)
        setError(null)
        setErrorDetails(null)
        
        // Сохраняем в localStorage
        localStorage.setItem("tracy_events", JSON.stringify(eventsArray))
        localStorage.setItem("tracy_events_timestamp", data.timestamp || new Date().toISOString())
        
        // Обновляем counts по датам
        const counts: Record<string, number> = {}
        eventsArray.forEach((event: Event) => {
          try {
            const dateKey = format(new Date(event.startAt), "yyyy-MM-dd")
            counts[dateKey] = (counts[dateKey] || 0) + 1
          } catch (e) {
            console.error("Error parsing event date:", e, event)
          }
        })
        setEventsByDate(counts)
      } else {
        console.log(`[Calendar] Нет событий для отображения`)
        setEvents([])
        setEventsByDate({})
        setError(null)
        setErrorDetails(null)
      }
      
      setLoading(false)
      
    } catch (error: any) {
      console.error(`[Calendar] ❌ Ошибка при запросе к API:`, error)
      
      // Если ошибка сети, используем сохраненные события
      const storedEvents = localStorage.getItem("tracy_events")
      if (storedEvents) {
        try {
          const parsedEvents = JSON.parse(storedEvents)
          if (Array.isArray(parsedEvents) && parsedEvents.length > 0) {
            console.log(`[Calendar] ⚠️ Ошибка сети, используем сохраненные события из localStorage`)
            setError(null)
            setLoading(false)
            return
          }
        } catch (e) {
          // Игнорируем ошибки парсинга
        }
      }
      
      // Показываем конкретную ошибку
      const errorMessage = error.type 
        ? formatApiError(error)
        : (error.message || "Не удалось загрузить события")
      
      setError(errorMessage)
      setErrorDetails({
        code: String(error.status || error.type || "UNKNOWN"),
        message: error.message || errorMessage,
        context: "Загрузка событий календаря",
      })
      setLoading(false)
    }
  }

  useEffect(() => {
    // Загружаем события только после получения user_id
    if (!userLoading && userId) {
      loadEvents(true)
    }
    
    // Обрабатываем события из URL параметров (если есть)
    // Это происходит, когда бот отправляет события через WebApp URL
    if (typeof window !== "undefined") {
      const urlParams = new URLSearchParams(window.location.search)
      const eventsParam = urlParams.get("events")
      if (eventsParam) {
        try {
          // Декодируем base64 данные
          const decodedData = atob(eventsParam)
          const eventsData = JSON.parse(decodedData)
          
          if (eventsData.action === 'sync_events' && Array.isArray(eventsData.events)) {
            console.log(`[Calendar] Получены события из URL параметров: ${eventsData.count} событий`)
            setEvents(eventsData.events)
            
            // Сохраняем в localStorage
            localStorage.setItem("tracy_events", JSON.stringify(eventsData.events))
            localStorage.setItem("tracy_events_timestamp", eventsData.timestamp)
            
            // Обновляем counts по датам
            const counts: Record<string, number> = {}
            eventsData.events.forEach((event: Event) => {
              try {
                const dateKey = format(new Date(event.startAt), "yyyy-MM-dd")
                counts[dateKey] = (counts[dateKey] || 0) + 1
              } catch (e) {
                console.error("Error parsing event date:", e, event)
              }
            })
            setEventsByDate(counts)
            
            // Удаляем параметр из URL после обработки
            window.history.replaceState({}, '', window.location.pathname)
            
            setLoading(false)
          }
        } catch (e) {
          console.error("[Calendar] Ошибка декодирования событий из URL:", e)
        }
      }
    }
  }, [user?.id])
  
  useEffect(() => {
    // Автоматическое обновление событий при открытом веб-приложении
    if (!userLoading && userId) {
      // Обновление каждые 30 секунд для синхронизации с ботом
      const intervalId = setInterval(() => {
        console.log(`[Calendar] Автоматическое обновление событий для пользователя ${userId}`)
        loadEvents(true)
      }, 30000) // Обновление каждые 30 секунд
      
      // Обновление при возвращении на вкладку (focus)
      const handleFocus = () => {
        console.log(`[Calendar] Обновление событий при focus`)
        loadEvents(true)
      }
      window.addEventListener("focus", handleFocus)
      
      // Обновление при видимости страницы (visibilitychange)
      const handleVisibilityChange = () => {
        if (!document.hidden) {
          console.log(`[Calendar] Обновление событий при visibility change`)
          loadEvents(true)
        }
      }
      document.addEventListener("visibilitychange", handleVisibilityChange)
      
      return () => {
        clearInterval(intervalId)
        window.removeEventListener("focus", handleFocus)
        document.removeEventListener("visibilitychange", handleVisibilityChange)
      }
    }
  }, [userId, userLoading])

  const selectedDateKey = format(selectedDate, "yyyy-MM-dd")
  const dayEvents = events.filter(
    (event) => format(new Date(event.startAt), "yyyy-MM-dd") === selectedDateKey
  )

  const botUsername = process.env.NEXT_PUBLIC_TELEGRAM_BOT_USERNAME || "tracy_aibot"
  const telegramLink = `https://t.me/${botUsername}`

  const handleClose = () => {
    if (typeof window !== "undefined" && (window as any).Telegram?.WebApp) {
      (window as any).Telegram.WebApp.close()
    }
  }

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      {/* Top Header - как на скриншоте */}
      <header className="sticky top-0 z-20 border-b border-border bg-background/95 backdrop-blur">
        <div className="flex h-14 items-center justify-between px-4">
          {/* Left: Back button and profile */}
          <div className="flex items-center gap-3">
            <Link href="/assistant">
              <button className="text-foreground hover:text-muted-foreground transition-colors">
                <X className="h-5 w-5" />
              </button>
            </Link>
            {user?.photo_url && (
              <img
                src={user.photo_url}
                alt={user.first_name || "User"}
                className="h-8 w-8 rounded-full"
              />
            )}
            <Link href="/assistant">
              <button className="px-3 py-1.5 rounded-full bg-card border border-border text-sm font-medium hover:bg-accent transition-colors">
                <span className="text-primary">TRACY</span>
              </button>
            </Link>
          </div>
          
          {/* Right: Settings and Events List */}
          <div className="flex items-center gap-3">
            <Link href="/calendar/list">
              <button className="text-foreground hover:text-muted-foreground transition-colors" title="Все события">
                <CalendarIcon className="h-5 w-5" />
              </button>
            </Link>
            <Link href="/settings">
              <button className="text-foreground hover:text-muted-foreground transition-colors">
                <Settings className="h-5 w-5" />
              </button>
            </Link>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto pb-24">
        <div className="px-4 py-4">
          <CalendarGrid
            selectedDate={selectedDate}
            onDateSelect={setSelectedDate}
            eventsByDate={eventsByDate}
          />
        </div>

        {/* Bottom Panel - Events for selected day */}
        <div className="px-4 pb-4">
          <div className="bg-card rounded-2xl p-4 border border-border">
            <h2 className="text-lg font-semibold mb-4">
              {format(selectedDate, "d MMMM", { locale: ru })}
            </h2>
            
            {loading ? (
              <div className="text-center text-muted-foreground py-8">
                Загрузка...
              </div>
            ) : dayEvents.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-muted-foreground mb-2">Сегодня нет событий</p>
                <a
                  href={telegramLink}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary hover:underline text-sm"
                >
                  Чат с TRACY для создания событий
                </a>
              </div>
            ) : (
              <div className="space-y-2">
                {dayEvents.map((event) => (
                  <div
                    key={event.id}
                    className="flex items-start gap-3 rounded-lg border border-border p-3 hover:bg-accent/50 transition-colors"
                  >
                    <div
                      className="mt-1.5 h-2 w-2 rounded-full flex-shrink-0"
                      style={{
                        backgroundColor: event.calendarSource?.color || "hsl(var(--calendar-event-dot))",
                      }}
                    />
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-sm">{event.title}</p>
                      <p className="text-xs text-muted-foreground mt-0.5">
                        {event.allDay
                          ? "Весь день"
                          : formatTime(new Date(event.startAt))}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

    </div>
  )
}
