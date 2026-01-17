"use client"

import { useEffect, useState } from "react"
import { useRouter, useParams } from "next/navigation"
import { useTelegramUser } from "../../../lib/useTelegramUser"
import { useNavigation } from "../../../lib/useNavigation"
import { ArrowLeft, Loader2 } from "lucide-react"
import { Card, CardContent } from "../../../components/ui/card"
import { apiGet, formatApiError } from "../../../lib/apiClient"

interface Meeting {
  id: string
  title: string
  summary?: string
  summaryExtended?: string
  transcript?: string
  createdAt: string
}

export default function MeetingDetailClient() {
  const router = useRouter()
  const params = useParams()
  const { handleBack } = useNavigation()
  const { userId, isLoading } = useTelegramUser()
  const meetingId = params?.id as string
  const [meeting, setMeeting] = useState<Meeting | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // Если пользователь не загружен и не загружается, перенаправляем на логин
    if (!isLoading && !userId) {
      router.push("/login")
      return
    }

    if (userId && meetingId) {
      loadMeeting()
    }
  }, [userId, isLoading, meetingId, router])

  const loadMeeting = async () => {
    if (!userId || !meetingId) return

    try {
      setLoading(true)
      setError(null)

      const data = await apiGet<{ success?: boolean; meeting?: Meeting; error?: string }>(
        `/api/meetings/${meetingId}`,
        { user_id: parseInt(userId) },
        { timeout: 15000 }
      )

      if (data.success && data.meeting) {
        setMeeting(data.meeting)
      } else if (data.meeting) {
        setMeeting(data.meeting)
      } else if (data.error) {
        throw new Error(data.error)
      } else {
        throw new Error("Не удалось загрузить детали встречи")
      }
    } catch (e: any) {
      console.error("Ошибка загрузки встречи:", e)
      const errorMessage = e.type 
        ? formatApiError(e)
        : (e.message || "Не удалось загрузить детали встречи")
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  if (isLoading || loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground mx-auto mb-4" />
          <p className="text-muted-foreground">Загрузка...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      <header className="sticky top-0 z-20 border-b border-border bg-background/95 backdrop-blur">
        <div className="flex h-14 items-center justify-between px-4">
          <button
            onClick={handleBack}
            className="text-foreground hover:text-muted-foreground transition-colors"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <h1 className="text-lg font-semibold">Детали встречи</h1>
          <div className="w-5" />
        </div>
      </header>

      <div className="flex-1 overflow-y-auto">
        <div className="container mx-auto max-w-2xl px-4 py-6">
          {error ? (
            <Card className="border-destructive">
              <CardContent className="pt-6">
                <p className="text-sm text-destructive">{error}</p>
              </CardContent>
            </Card>
          ) : meeting ? (
            <div className="space-y-4">
              <Card className="border-border">
                <CardContent className="pt-6">
                  <h2 className="text-xl font-semibold mb-4">{meeting.title || `Встреча #${meeting.id}`}</h2>
                  <p className="text-sm text-muted-foreground mb-4">
                    {new Date(meeting.createdAt).toLocaleString("ru-RU")}
                  </p>
                </CardContent>
              </Card>

              {meeting.summary && (
                <Card className="border-border">
                  <CardContent className="pt-6">
                    <h3 className="font-semibold mb-2">Резюме</h3>
                    <p className="text-sm whitespace-pre-wrap">{meeting.summary}</p>
                  </CardContent>
                </Card>
              )}

              {meeting.summaryExtended && (
                <Card className="border-border">
                  <CardContent className="pt-6">
                    <h3 className="font-semibold mb-2">Расширенное резюме</h3>
                    <p className="text-sm whitespace-pre-wrap">{meeting.summaryExtended}</p>
                  </CardContent>
                </Card>
              )}

              {meeting.transcript && (
                <Card className="border-border">
                  <CardContent className="pt-6">
                    <h3 className="font-semibold mb-2">Полный текст</h3>
                    <p className="text-sm whitespace-pre-wrap">{meeting.transcript}</p>
                  </CardContent>
                </Card>
              )}
            </div>
          ) : (
            <Card className="border-border">
              <CardContent className="pt-6">
                <p className="text-muted-foreground text-center">Встреча не найдена</p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}
