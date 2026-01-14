"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { CalendarPageClient } from "./CalendarPageClient"
import { useTelegramUser } from "../../lib/useTelegramUser"

export default function CalendarPage() {
  const router = useRouter()
  const { userId, isLoading } = useTelegramUser()

  useEffect(() => {
    // Если пользователь не загружен и не загружается, перенаправляем на логин
    if (!isLoading && !userId) {
      router.push("/login")
      return
    }

    // Telegram Web App уже инициализирован через TelegramBootstrap
    // Дополнительная настройка не требуется
  }, [userId, isLoading, router])

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-primary border-r-transparent"></div>
          <p className="mt-4 text-muted-foreground">Загрузка...</p>
        </div>
      </div>
    )
  }

  if (!userId) {
    return null // Редирект на логин
  }

  return <CalendarPageClient />
}

