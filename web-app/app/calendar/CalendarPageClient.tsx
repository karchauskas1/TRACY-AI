"use client"

import { useState, useEffect } from "react"
import { format, isSameDay } from "date-fns"
import { ru } from "date-fns/locale"
import { Settings, X, MessageCircle, Send } from "lucide-react"
import Link from "next/link"
import { CalendarGrid } from "../../components/calendar/CalendarGrid"
import { Button } from "../../components/ui/button"
import { formatTime } from "../../lib/utils"

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
  const [loading, setLoading] = useState(true)
  const [user, setUser] = useState<any>(null)

  useEffect(() => {
    // Загружаем данные пользователя из Telegram Web App или localStorage
    if (typeof window !== "undefined") {
      const tg = (window as any).Telegram?.WebApp
      if (tg) {
        tg.ready()
        const tgUser = tg.initDataUnsafe?.user
        if (tgUser) {
          setUser({
            id: tgUser.id.toString(),
            first_name: tgUser.first_name,
            last_name: tgUser.last_name,
            username: tgUser.username,
            photo_url: tgUser.photo_url,
          })
        }
      } else {
        const savedUser = localStorage.getItem("telegram_user")
        if (savedUser) {
          setUser(JSON.parse(savedUser))
        }
      }
    }
  }, [])

  const loadEvents = async (forceRefresh: boolean = false) => {
    try {
      if (forceRefresh) {
        setLoading(true)
      }
      
      // Проверяем, открыто ли через Telegram Web App
      const tg = typeof window !== "undefined" ? (window as any).Telegram?.WebApp : null
      
      if (tg && user?.id) {
        // Если открыто через Telegram Web App, запрашиваем события через бота
        tg.ready()
        tg.expand()
        
        // Сначала загружаем из localStorage для быстрого отображения
        const storedEvents = localStorage.getItem("tracy_events")
        if (storedEvents) {
          try {
            const parsedEvents = JSON.parse(storedEvents)
            if (Array.isArray(parsedEvents)) {
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
              
              // Если есть сохраненные события, не показываем loading сразу (только при forceRefresh)
              if (!forceRefresh && parsedEvents.length > 0) {
                setLoading(false)
              }
            }
          } catch (e) {
            console.error("[Calendar] Error parsing stored events:", e)
          }
        } else {
          console.log(`[Calendar] Нет сохраненных событий в localStorage`)
        }
        
        // НОВОЕ РЕШЕНИЕ: Используем прямой вызов HTTP API бота для получения событий
        // Для production используем Render.com API, для локальной разработки - localhost:8080
        const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080'
        const apiUrl = `${apiBaseUrl}/api/events?user_id=${user.id}`
        
        try {
          console.log(`[Calendar] Запрос к API: ${apiUrl}`)
          const response = await fetch(apiUrl, {
            method: 'GET',
            headers: {
              'Content-Type': 'application/json',
            },
            mode: 'cors',
          })
          
          console.log(`[Calendar] Ответ API: status=${response.status}, ok=${response.ok}`)
          
          if (response.ok) {
            const data = await response.json()
            console.log(`[Calendar] Данные API:`, data)
            if (data.success && Array.isArray(data.events)) {
              console.log(`[Calendar] Получено ${data.events.length} событий через HTTP API`)
              setEvents(data.events)
              
              // Сохраняем в localStorage
              localStorage.setItem("tracy_events", JSON.stringify(data.events))
              localStorage.setItem("tracy_events_timestamp", data.timestamp)
              
              // Обновляем counts по датам
              const counts: Record<string, number> = {}
              data.events.forEach((event: Event) => {
                try {
                  const dateKey = format(new Date(event.startAt), "yyyy-MM-dd")
                  counts[dateKey] = (counts[dateKey] || 0) + 1
                } catch (e) {
                  console.error("Error parsing event date:", e, event)
                }
              })
              setEventsByDate(counts)
              
              setLoading(false)
              return
            } else {
              console.warn(`[Calendar] API вернул неверный формат данных:`, data)
            }
          } else {
            const errorText = await response.text()
            console.error(`[Calendar] API вернул ошибку: ${response.status} ${response.statusText}`, errorText)
          }
        } catch (error) {
          console.error(`[Calendar] Ошибка при запросе к HTTP API:`, error)
          console.warn(`[Calendar] HTTP API недоступен (${error}), используем fallback механизм через tg.sendData`)
        }
        
        // Fallback: Используем старый механизм через tg.sendData
        const requestData = JSON.stringify({ action: "get_events", user_id: user.id })
        tg.sendData(requestData)
        console.log(`[Calendar] Отправлен запрос событий через tg.sendData для пользователя ${user.id}`)
        
        // Устанавливаем таймер для завершения loading
        if (!storedEvents || forceRefresh) {
          setTimeout(() => {
            setLoading(false)
            console.log(`[Calendar] Loading завершен. Событий в состоянии: ${events.length}`)
          }, 3000)
        } else {
          setLoading(false)
        }
        
      } else {
        // Если не через Telegram Web App, используем только localStorage
        const storedEvents = localStorage.getItem("tracy_events")
        if (storedEvents) {
          try {
            const parsedEvents = JSON.parse(storedEvents)
            if (Array.isArray(parsedEvents)) {
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
            }
          } catch (e) {
            console.error("Error parsing stored events:", e)
            setEvents([])
            setEventsByDate({})
          }
        } else {
          setEvents([])
          setEventsByDate({})
        }
        setLoading(false)
      }
      
      // Всегда завершаем loading после попытки загрузки
      setTimeout(() => {
        setLoading(false)
      }, 2000)
      
    } catch (error) {
      console.error("Failed to load events:", error)
      setEvents([])
      setEventsByDate({})
      setLoading(false)
    }
  }

  useEffect(() => {
    // Загружаем события при монтировании компонента
    if (user?.id) {
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
    const tg = typeof window !== "undefined" ? (window as any).Telegram?.WebApp : null
    if (tg && user?.id) {
      // Обновление каждые 10 секунд (более частое для лучшей синхронизации)
      const intervalId = setInterval(() => {
        console.log(`[Calendar] Автоматическое обновление событий для пользователя ${user.id}`)
        loadEvents(true)
      }, 10000) // Обновление каждые 10 секунд для лучшей синхронизации
      
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
      
      // Обновление при открытии веб-приложения (viewportChanged)
      if (tg.onEvent) {
        tg.onEvent("viewportChanged", () => {
          console.log(`[Calendar] Обновление событий при viewport changed`)
          loadEvents(true)
        })
      }
      
      return () => {
        clearInterval(intervalId)
        window.removeEventListener("focus", handleFocus)
        document.removeEventListener("visibilitychange", handleVisibilityChange)
      }
    }
  }, [user?.id])

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
          
          {/* Right: Settings */}
          <Link href="/settings">
            <button className="text-foreground hover:text-muted-foreground transition-colors">
              <Settings className="h-5 w-5" />
            </button>
          </Link>
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

      {/* Floating Button - Bottom Right (как на скриншоте) */}
      <a
        href={telegramLink}
        target="_blank"
        rel="noopener noreferrer"
        className="fixed bottom-6 right-6 z-30"
      >
        <button className="flex items-center gap-2 px-4 py-3 rounded-full bg-primary text-primary-foreground shadow-lg hover:bg-primary/90 transition-colors">
          <Send className="h-4 w-4" />
          <span className="font-medium">TRACY</span>
        </button>
      </a>
    </div>
  )
}
