"use client"

import { useEffect } from "react"
import { useRouter, useParams } from "next/navigation"
import { useTelegramUser } from "../../../lib/useTelegramUser"

export default function MeetingDetailPage() {
  const router = useRouter()
  const params = useParams()
  const { userId, isLoading } = useTelegramUser()
  const meetingId = params?.id as string

  useEffect(() => {
    // Если пользователь не загружен и не загружается, перенаправляем на логин
    if (!isLoading && !userId) {
      router.push("/login")
      return
    }

    // Настраиваем Telegram Web App, если доступен
    if (typeof window !== "undefined") {
      const tg = (window as any).Telegram?.WebApp
      if (tg) {
        tg.ready()
        tg.expand()
        tg.setHeaderColor("#1a1a20")
        tg.setBackgroundColor("#1a1a20")
      }
    }
  }, [userId, isLoading, router])

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="text-center">
          <p className="text-muted-foreground">Загрузка...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background text-foreground p-4">
      <div className="container mx-auto max-w-2xl">
        <h1 className="text-2xl font-semibold mb-4">Встреча #{meetingId}</h1>
        <p className="text-muted-foreground">
          Детали встречи будут отображаться здесь.
        </p>
      </div>
    </div>
  )
}

