"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { CalendarPageClient } from "./CalendarPageClient"

export default function CalendarPage() {
  const router = useRouter()

  useEffect(() => {
    // Если открыто через Telegram Web App, сохраняем данные пользователя
    if (typeof window !== "undefined" && (window as any).Telegram?.WebApp) {
      const tg = (window as any).Telegram.WebApp
      tg.ready()
      const user = tg.initDataUnsafe?.user
      if (user) {
        localStorage.setItem("telegram_user", JSON.stringify({
          id: user.id.toString(),
          first_name: user.first_name,
          last_name: user.last_name,
          username: user.username,
          photo_url: user.photo_url,
        }))
      }
    }
  }, [])

  return <CalendarPageClient />
}

