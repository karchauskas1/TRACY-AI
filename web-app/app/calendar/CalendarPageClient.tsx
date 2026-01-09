"use client"

import { useState, useEffect } from "react"
import { format, startOfMonth, endOfMonth, isSameDay } from "date-fns"
import { Settings, MessageCircle } from "lucide-react"
import Link from "next/link"
import { CalendarGrid } from "@/components/calendar/CalendarGrid"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { formatTime } from "@/lib/utils"

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

  const loadEvents = async () => {
    try {
      const monthStart = startOfMonth(selectedDate)
      const monthEnd = endOfMonth(selectedDate)

      const response = await fetch(
        `/api/events?from=${format(monthStart, "yyyy-MM-dd")}&to=${format(monthEnd, "yyyy-MM-dd")}`
      )

      if (response.ok) {
        const data = await response.json()
        setEvents(data.events || [])

        // Count events by date
        const counts: Record<string, number> = {}
        data.events?.forEach((event: Event) => {
          const dateKey = format(new Date(event.startAt), "yyyy-MM-dd")
          counts[dateKey] = (counts[dateKey] || 0) + 1
        })
        setEventsByDate(counts)
      }
    } catch (error) {
      console.error("Failed to load events:", error)
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

  const telegramLink = process.env.NEXT_PUBLIC_TELEGRAM_DEEP_LINK || "https://t.me/your_bot"

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-10 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-16 items-center justify-between px-4">
          <div className="flex items-center gap-4">
            <h1 className="text-lg font-semibold">Календарь</h1>
          </div>
          <div className="flex items-center gap-2">
            <Link href={telegramLink} target="_blank">
              <Button variant="outline" size="sm">
                <MessageCircle className="mr-2 h-4 w-4" />
                Открыть чат с TRACY
              </Button>
            </Link>
            <Link href="/settings">
              <Button variant="ghost" size="icon">
                <Settings className="h-5 w-5" />
              </Button>
            </Link>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        <div className="grid gap-8 lg:grid-cols-3">
          {/* Calendar */}
          <div className="lg:col-span-2">
            <CalendarGrid
              selectedDate={selectedDate}
              onDateSelect={setSelectedDate}
              eventsByDate={eventsByDate}
            />
          </div>

          {/* Events Panel */}
          <div className="lg:col-span-1">
            <Card>
              <CardHeader>
                <CardTitle>
                  {format(selectedDate, "d MMMM", { locale: require("date-fns/locale/ru") })}
                </CardTitle>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <div className="text-center text-muted-foreground py-8">
                    Загрузка...
                  </div>
                ) : dayEvents.length === 0 ? (
                  <div className="text-center text-muted-foreground py-8">
                    В этот день нет событий
                  </div>
                ) : (
                  <div className="space-y-2">
                    {dayEvents.map((event) => (
                      <Link
                        key={event.id}
                        href={`/event/${event.id}`}
                        className="block"
                      >
                        <div
                          className="group flex items-start gap-3 rounded-lg border p-3 transition-colors hover:bg-accent"
                        >
                          <div
                            className="mt-1 h-1 w-1 rounded-full"
                            style={{
                              backgroundColor: event.calendarSource?.color || "#3b82f6",
                            }}
                          />
                          <div className="flex-1 min-w-0">
                            <p className="font-medium truncate">{event.title}</p>
                            <p className="text-sm text-muted-foreground">
                              {event.allDay
                                ? "Весь день"
                                : formatTime(new Date(event.startAt))}
                            </p>
                          </div>
                        </div>
                      </Link>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}

