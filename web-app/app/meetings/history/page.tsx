"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { ArrowLeft, History, Calendar, Clock, FileText } from "lucide-react"
import Link from "next/link"
import { Card, CardContent, CardHeader, CardTitle } from "../../../components/ui/card"
import { Button } from "../../../components/ui/button"
import { format } from "date-fns"
import { ru } from "date-fns/locale"

interface Meeting {
  id: string
  title: string
  createdAt: string
  summary?: string
  transcript?: string
}

export default function MeetingsHistoryPage() {
  const router = useRouter()
  const [meetings, setMeetings] = useState<Meeting[]>([])

  useEffect(() => {
    // Загружаем встречи из localStorage (для статического сайта)
    const storedMeetings = localStorage.getItem("tracy_meetings")
    if (storedMeetings) {
      try {
        setMeetings(JSON.parse(storedMeetings))
      } catch (e) {
        console.error("Failed to parse meetings:", e)
      }
    }
  }, [])

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      <header className="sticky top-0 z-20 border-b border-border bg-background/95 backdrop-blur">
        <div className="flex h-14 items-center justify-between px-4">
          <Link href="/assistant">
            <button className="text-foreground hover:text-muted-foreground transition-colors">
              <ArrowLeft className="h-5 w-5" />
            </button>
          </Link>
          <h1 className="text-lg font-semibold">История расшифровок</h1>
          <div className="w-5" />
        </div>
      </header>

      <div className="flex-1 overflow-y-auto">
        <div className="container mx-auto max-w-2xl px-4 py-6">
          {meetings.length === 0 ? (
            <Card className="border-border">
              <CardContent className="pt-6">
                <div className="text-center py-12">
                  <History className="h-16 w-16 mx-auto text-muted-foreground mb-4 opacity-50" />
                  <h3 className="text-lg font-semibold mb-2">
                    Пока нет расшифровок
                  </h3>
                  <p className="text-sm text-muted-foreground mb-6">
                    Загрузи первую встречу, чтобы увидеть её здесь
                  </p>
                  <Link href="/meetings/new">
                    <Button>
                      Расшифровать встречу
                    </Button>
                  </Link>
                </div>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {meetings.map((meeting) => (
                <Card
                  key={meeting.id}
                  className="border-border hover:bg-accent/50 transition-colors cursor-pointer"
                  onClick={() => router.push(`/meetings/${meeting.id}`)}
                >
                  <CardContent className="p-6">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        <h3 className="font-semibold mb-2 truncate">
                          {meeting.title || "Без названия"}
                        </h3>
                        <div className="flex items-center gap-4 text-sm text-muted-foreground mb-3">
                          <div className="flex items-center gap-1">
                            <Calendar className="h-4 w-4" />
                            {format(new Date(meeting.createdAt), "d MMMM yyyy", { locale: ru })}
                          </div>
                          <div className="flex items-center gap-1">
                            <Clock className="h-4 w-4" />
                            {format(new Date(meeting.createdAt), "HH:mm", { locale: ru })}
                          </div>
                        </div>
                        {meeting.summary && (
                          <p className="text-sm text-muted-foreground line-clamp-2">
                            {meeting.summary}
                          </p>
                        )}
                      </div>
                      <FileText className="h-5 w-5 text-muted-foreground flex-shrink-0" />
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

