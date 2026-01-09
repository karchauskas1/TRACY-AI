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

  const loadEvents = async () => {
    try {
      // Для статического экспорта используем Telegram Web App API или localStorage
      const storedEvents = localStorage.getItem("tracy_events")
      if (storedEvents) {
        const parsedEvents = JSON.parse(storedEvents)
        setEvents(parsedEvents)

        // Count events by date
        const counts: Record<string, number> = {}
        parsedEvents.forEach((event: Event) => {
          const dateKey = format(new Date(event.startAt), "yyyy-MM-dd")
          counts[dateKey] = (counts[dateKey] || 0) + 1
        })
        setEventsByDate(counts)
      } else {
        // Если нет данных, показываем пустой календарь
        setEvents([])
        setEventsByDate({})
      }
    } catch (error) {
      console.error("Failed to load events:", error)
      setEvents([])
      setEventsByDate({})
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadEvents()
  }, [selectedDate])

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
          {/* Left: Close button and profile */}
          <div className="flex items-center gap-3">
            <button
              onClick={handleClose}
              className="text-foreground hover:text-muted-foreground transition-colors"
            >
              <X className="h-5 w-5" />
            </button>
            {user?.photo_url && (
              <img
                src={user.photo_url}
                alt={user.first_name || "User"}
                className="h-8 w-8 rounded-full"
              />
            )}
            <button className="px-3 py-1.5 rounded-full bg-card border border-border text-sm font-medium hover:bg-accent transition-colors">
              <span className="text-primary">TRACY</span>
            </button>
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
