"use client"

import { useState, useEffect } from "react"
import { FeedbackPageClient } from "./FeedbackPageClient"

export default function FeedbackPage() {
  const [user, setUser] = useState<any>(null)

  useEffect(() => {
    // Загружаем данные пользователя из Telegram Web App или localStorage
    if (typeof window !== "undefined") {
      const tg = (window as any).Telegram?.WebApp
      if (tg) {
        tg.ready()
        const tgUser = tg.initDataUnsafe?.user
        if (tgUser) {
          const fullName = [tgUser.first_name, tgUser.last_name].filter(Boolean).join(" ")
          setUser({
            id: tgUser.id.toString(),
            name: fullName || tgUser.first_name || "Пользователь",
            avatarUrl: tgUser.photo_url,
            first_name: tgUser.first_name,
            last_name: tgUser.last_name,
            username: tgUser.username
          })
        }
      } else {
        const savedUser = localStorage.getItem("telegram_user")
        if (savedUser) {
          try {
            const parsed = JSON.parse(savedUser)
            const fullName = [parsed.first_name, parsed.last_name].filter(Boolean).join(" ")
            setUser({
              ...parsed,
              name: fullName || parsed.first_name || "Пользователь",
            })
          } catch (e) {
            console.error("Error parsing saved user:", e)
          }
        }
      }
    }
  }, [])

  return <FeedbackPageClient user={user} />
}

