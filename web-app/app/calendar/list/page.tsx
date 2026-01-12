"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { ArrowLeft, Calendar as CalendarIcon } from "lucide-react"
import Link from "next/link"
import { Card, CardContent } from "../../../components/ui/card"
import { format } from "date-fns"
import { ru } from "date-fns/locale"

interface Event {
  id: string
  title: string
  startAt: string
  endAt?: string
  allDay: boolean
  description?: string
  location?: string
  calendarSource?: {
    color: string
    name: string
  }
}

export default function EventsListPage() {
  const router = useRouter()
  const [events, setEvents] = useState<Event[]>([])
  const [loading, setLoading] = useState(true)
  const [user, setUser] = useState<any>(null)

  useEffect(() => {
    // Загружаем данные пользователя
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
          try {
            setUser(JSON.parse(savedUser))
          } catch (e) {
            console.error("[EventsList] Error parsing saved user:", e)
          }
        }
      }
    }
  }, [])

  useEffect(() => {
    const loadEvents = async () => {
      if (!user?.id) {
        setLoading(false)
        return
      }

      const tg = typeof window !== "undefined" ? (window as any).Telegram?.WebApp : null
      
      // Используем Telegram Web App API для получения событий
      if (tg) {
        tg.ready()
        const requestData = JSON.stringify({ action: "get_events", user_id: user.id })
        tg.sendData(requestData)
        
        // Также пробуем загрузить из localStorage
        const storedEvents = localStorage.getItem("tracy_events")
        if (storedEvents) {
          try {
            const parsedEvents = JSON.parse(storedEvents)
            if (Array.isArray(parsedEvents)) {
              setEvents(parsedEvents)
              setLoading(false)
            }
          } catch (e) {
            console.error("[EventsList] Error parsing stored events:", e)
          }
        }
      }

      // Пробуем загрузить через HTTP API (для localhost или если tg недоступен)
      try {
        const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || 
          (typeof window !== 'undefined' && window.location.hostname === 'localhost' 
            ? 'http://localhost:8080' 
            : 'http://5.35.126.42')
        const apiUrl = `${apiBaseUrl}/api/events?user_id=${user.id}`
        
        const response = await fetch(apiUrl, {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' },
          mode: 'cors',
        })
        
        if (response.ok) {
          const data = await response.json()
          if (data.success && Array.isArray(data.events)) {
            setEvents(data.events)
            localStorage.setItem("tracy_events", JSON.stringify(data.events))
          }
        }
      } catch (error) {
        console.error("[EventsList] Error loading events:", error)
      } finally {
        setLoading(false)
      }
    }

    if (user?.id) {
      loadEvents()
    }
  }, [user?.id])

  // Сортируем события по дате
  const sortedEvents = [...events].sort((a, b) => 
    new Date(a.startAt).getTime() - new Date(b.startAt).getTime()
  )

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      <header className="sticky top-0 z-20 border-b border-border bg-background/95 backdrop-blur">
        <div className="flex h-14 items-center justify-between px-4">
          <Link href="/calendar">
            <button className="text-foreground hover:text-muted-foreground transition-colors">
              <ArrowLeft className="h-5 w-5" />
            </button>
          </Link>
          <h1 className="text-lg font-semibold">Все события</h1>
          <div className="w-5" />
        </div>
      </header>

      <div className="flex-1 overflow-y-auto">
        <div className="container mx-auto max-w-2xl px-4 py-6">
          {loading ? (
            <div className="text-center text-muted-foreground py-12">
              Загрузка событий...
            </div>
          ) : sortedEvents.length === 0 ? (
            <Card className="border-border">
              <CardContent className="pt-6">
                <div className="text-center py-12">
                  <CalendarIcon className="h-16 w-16 mx-auto text-muted-foreground mb-4 opacity-50" />
                  <h3 className="text-lg font-semibold mb-2">Нет событий</h3>
                  <p className="text-sm text-muted-foreground">
                    Создайте первое событие через бота TRACY
                  </p>
                </div>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-3">
              {sortedEvents.map((event) => {
                const eventDate = new Date(event.startAt)
                const dateKey = format(eventDate, "yyyy-MM-dd")
                const isToday = dateKey === format(new Date(), "yyyy-MM-dd")
                const isTomorrow = dateKey === format(new Date(Date.now() + 86400000), "yyyy-MM-dd")
                
                return (
                  <Card key={event.id} className="border-border bg-card">
                    <CardContent className="p-4">
                      <div className="flex items-start gap-3">
                        <div
                          className="mt-1.5 h-3 w-3 rounded-full flex-shrink-0"
                          style={{
                            backgroundColor: event.calendarSource?.color || "hsl(var(--primary))",
                          }}
                        />
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-base mb-1">{event.title}</p>
                          <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
                            <span>
                              {isToday ? "Сегодня" : isTomorrow ? "Завтра" : format(eventDate, "d MMMM yyyy", { locale: ru })}
                            </span>
                            {!event.allDay && (
                              <>
                                <span>•</span>
                                <span>{format(eventDate, "HH:mm")}</span>
                                {event.endAt && (
                                  <>
                                    <span>-</span>
                                    <span>{format(new Date(event.endAt), "HH:mm")}</span>
                                  </>
                                )}
                              </>
                            )}
                            {event.location && (
                              <>
                                <span>•</span>
                                <span>{event.location}</span>
                              </>
                            )}
                          </div>
                          {event.description && (
                            <p className="text-sm text-muted-foreground mt-2 line-clamp-2">
                              {event.description}
                            </p>
                          )}
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
    </div>
  )
}



