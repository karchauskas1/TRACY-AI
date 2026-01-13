"use client"

import { useState, useEffect } from "react"
import { format, isSameDay } from "date-fns"
import { ru } from "date-fns/locale"
import { Settings, X, MessageCircle, Send, Calendar as CalendarIcon } from "lucide-react"
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
      
      // Получаем user_id из разных источников
      let userId: string | null = null
      if (user?.id) {
        userId = user.id.toString()
      } else if (tg?.initDataUnsafe?.user?.id) {
        userId = tg.initDataUnsafe.user.id.toString()
        // Сохраняем user для будущего использования
        if (!user) {
          setUser({
            id: userId,
            first_name: tg.initDataUnsafe.user.first_name,
            last_name: tg.initDataUnsafe.user.last_name,
            username: tg.initDataUnsafe.user.username,
            photo_url: tg.initDataUnsafe.user.photo_url,
          })
        }
      } else {
        // Пробуем получить из localStorage
        const savedUser = localStorage.getItem("telegram_user")
        if (savedUser) {
          try {
            const parsedUser = JSON.parse(savedUser)
            userId = parsedUser.id?.toString() || null
          } catch (e) {
            console.error("[Calendar] Error parsing saved user:", e)
          }
        }
      }
      
      console.log(`[Calendar] User ID: ${userId}, tg: ${!!tg}, user: ${!!user}`)
      
      if (!userId) {
        console.warn("[Calendar] ⚠️ User ID не найден! Не могу загрузить события.")
        setLoading(false)
        return
      }
      
      if (tg) {
        // Если открыто через Telegram Web App
        tg.ready()
        tg.expand()
      }
      
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
      
      // ПРИОРИТЕТ 1: Прямой вызов HTTP API (основной способ)
      // Используем серверный API для получения событий
      let apiBaseUrl = "https://api.pasekaproduction.ru"
      
      if (typeof window !== 'undefined') {
        if (window.location.hostname === 'localhost') {
          apiBaseUrl = 'http://localhost:8080'
        } else {
          // Для GitHub Pages используем серверный API
          apiBaseUrl = "https://api.pasekaproduction.ru"
        }
      }
      
      // Загружаем события через HTTP API
      const apiUrl = `${apiBaseUrl}/api/events?user_id=${userId}`
      
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
          let data
          try {
            const responseText = await response.text()
            console.log(`[Calendar] Raw API Response:`, responseText.substring(0, 500))
            data = JSON.parse(responseText)
          } catch (e) {
            console.error(`[Calendar] Ошибка парсинга JSON:`, e)
            // Пробуем использовать сохраненные события
            if (storedEvents) {
              console.log(`[Calendar] Используем сохраненные события из localStorage`)
              setLoading(false)
              return
            }
            setLoading(false)
            return
          }
          
          console.log(`[Calendar] Parsed API Data:`, data)
          
          // Обрабатываем разные форматы ответа
          let eventsArray: Event[] = []
          if (data.success && Array.isArray(data.events)) {
            eventsArray = data.events
            console.log(`[Calendar] ✅ Успешно загружено ${eventsArray.length} событий (формат: success + events)`)
          } else if (Array.isArray(data.events)) {
            eventsArray = data.events
            console.log(`[Calendar] ✅ Загружено ${eventsArray.length} событий (формат: events)`)
          } else if (Array.isArray(data)) {
            eventsArray = data
            console.log(`[Calendar] ✅ Загружено ${eventsArray.length} событий (формат: array)`)
          } else if (data.error) {
            console.error(`[Calendar] ❌ API вернул ошибку:`, data.error)
            // Пробуем использовать сохраненные события
            if (storedEvents) {
              console.log(`[Calendar] Используем сохраненные события из localStorage`)
              setLoading(false)
              return
            }
            setLoading(false)
            return
          } else {
            console.warn(`[Calendar] ⚠️ API вернул неверный формат данных:`, data)
            // Пробуем использовать сохраненные события
            if (storedEvents) {
              console.log(`[Calendar] Используем сохраненные события из localStorage`)
              setLoading(false)
              return
            }
            setLoading(false)
            return
          }
          
          if (eventsArray.length > 0) {
            console.log(`[Calendar] ✅ Получено ${eventsArray.length} событий через HTTP API`)
            setEvents(eventsArray)
            
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
          }
          
          setLoading(false)
          return
        } else {
          let errorText = ""
          try {
            errorText = await response.text()
          } catch (e) {
            errorText = response.statusText
          }
          console.error(`[Calendar] ❌ API вернул ошибку: ${response.status} ${response.statusText}`, errorText)
          
          // Если API недоступен, используем сохраненные события из localStorage
          if (storedEvents) {
            console.log(`[Calendar] ⚠️ API недоступен, используем сохраненные события из localStorage`)
            setLoading(false)
            return
          }
          
          // Если нет сохраненных событий, показываем ошибку
          setLoading(false)
          return
        }
      } catch (error) {
        console.error(`[Calendar] ❌ Ошибка при запросе к HTTP API:`, error)
        
        // Если ошибка сети, используем сохраненные события
        if (storedEvents) {
          console.log(`[Calendar] ⚠️ Ошибка сети, используем сохраненные события из localStorage`)
          setLoading(false)
          return
        }
      }
      
      // Если не удалось загрузить и нет сохраненных событий
      setLoading(false)
      
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
    if (user?.id) {
      // Обновление каждые 30 секунд для синхронизации с ботом
      const intervalId = setInterval(() => {
        console.log(`[Calendar] Автоматическое обновление событий для пользователя ${user.id}`)
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
