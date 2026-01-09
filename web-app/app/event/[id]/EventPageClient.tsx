"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { format } from "date-fns"
import { Save, Trash2, Share2 } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { useToast } from "@/hooks/use-toast"
import { formatTime } from "@/lib/utils"

interface Event {
  id: string
  title: string
  description?: string
  location?: string
  startAt: string
  endAt?: string
  allDay: boolean
  reminders: Array<{ id: string; minutesBefore: number }>
}

export function EventPageClient({ eventId }: { eventId: string }) {
  const router = useRouter()
  const { toast } = useToast()
  const [event, setEvent] = useState<Event | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    loadEvent()
  }, [eventId])

  const loadEvent = async () => {
    try {
      const response = await fetch(`/api/events/${eventId}`)
      if (response.ok) {
        const data = await response.json()
        setEvent(data.event)
      }
    } catch (error) {
      console.error("Failed to load event:", error)
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    if (!event) return

    setSaving(true)
    try {
      const response = await fetch(`/api/events/${eventId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: event.title,
          description: event.description,
          location: event.location,
          startAt: event.startAt,
          endAt: event.endAt,
          allDay: event.allDay,
          reminders: event.reminders.map((r) => r.minutesBefore),
        }),
      })

      if (response.ok) {
        toast({
          title: "Событие сохранено",
          description: "Изменения успешно применены",
        })
        router.push("/calendar")
      } else {
        throw new Error("Failed to save")
      }
    } catch (error) {
      toast({
        title: "Ошибка",
        description: "Не удалось сохранить событие",
        variant: "destructive",
      })
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    if (!confirm("Удалить это событие?")) return

    try {
      const response = await fetch(`/api/events/${eventId}`, {
        method: "DELETE",
      })

      if (response.ok) {
        toast({
          title: "Событие удалено",
        })
        router.push("/calendar")
      }
    } catch (error) {
      toast({
        title: "Ошибка",
        description: "Не удалось удалить событие",
        variant: "destructive",
      })
    }
  }

  const handleShare = async () => {
    if (!event) return

    // Generate ICS file
    const icsContent = generateICS(event)
    const blob = new Blob([icsContent], { type: "text/calendar" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `${event.title}.ics`
    a.click()
    URL.revokeObjectURL(url)

    toast({
      title: "Файл скачан",
      description: "Событие экспортировано в .ics",
    })
  }

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center">Загрузка...</div>
      </div>
    )
  }

  if (!event) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center">Событие не найдено</div>
      </div>
    )
  }

  return (
    <div className="container mx-auto max-w-2xl px-4 py-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-3xl font-semibold">Событие</h1>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleShare}>
            <Share2 className="mr-2 h-4 w-4" />
            Поделиться
          </Button>
          <Button variant="destructive" onClick={handleDelete}>
            <Trash2 className="mr-2 h-4 w-4" />
            Удалить
          </Button>
          <Button onClick={handleSave} disabled={saving}>
            <Save className="mr-2 h-4 w-4" />
            Сохранить
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Детали</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm font-medium">Название</label>
            <Input
              value={event.title}
              onChange={(e) =>
                setEvent({ ...event, title: e.target.value })
              }
              className="mt-1"
            />
          </div>

          <div>
            <label className="text-sm font-medium">Дата и время</label>
            <div className="mt-1 flex gap-2">
              <Input
                type="datetime-local"
                value={format(new Date(event.startAt), "yyyy-MM-dd'T'HH:mm")}
                onChange={(e) =>
                  setEvent({
                    ...event,
                    startAt: new Date(e.target.value).toISOString(),
                  })
                }
              />
            </div>
          </div>

          <div>
            <label className="text-sm font-medium">Место</label>
            <Input
              value={event.location || ""}
              onChange={(e) =>
                setEvent({ ...event, location: e.target.value })
              }
              className="mt-1"
              placeholder="Опционально"
            />
          </div>

          <div>
            <label className="text-sm font-medium">Описание</label>
            <Textarea
              value={event.description || ""}
              onChange={(e) =>
                setEvent({ ...event, description: e.target.value })
              }
              className="mt-1"
              rows={4}
              placeholder="Опционально"
            />
          </div>

          <div>
            <label className="text-sm font-medium">Напоминания</label>
            <div className="mt-1 space-y-2">
              {event.reminders.map((reminder) => (
                <div key={reminder.id} className="text-sm">
                  За {formatReminder(reminder.minutesBefore)}
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

function formatReminder(minutes: number): string {
  if (minutes < 60) return `${minutes} минут`
  if (minutes < 1440) return `${Math.floor(minutes / 60)} часов`
  return `${Math.floor(minutes / 1440)} дней`
}

function generateICS(event: Event): string {
  const start = format(new Date(event.startAt), "yyyyMMdd'T'HHmmss")
  const end = event.endAt
    ? format(new Date(event.endAt), "yyyyMMdd'T'HHmmss")
    : start

  return `BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//TRACY//Calendar//EN
BEGIN:VEVENT
UID:${event.id}@tracy
DTSTART:${start}
DTEND:${end}
SUMMARY:${event.title}
${event.description ? `DESCRIPTION:${event.description}` : ""}
${event.location ? `LOCATION:${event.location}` : ""}
END:VEVENT
END:VCALENDAR`
}

