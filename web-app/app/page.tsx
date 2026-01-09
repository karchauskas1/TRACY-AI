"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"

export default function HomePage() {
  const router = useRouter()

  useEffect(() => {
    // Проверяем, открыто ли приложение через Telegram Web App
    if (typeof window !== "undefined" && (window as any).Telegram?.WebApp) {
      const tg = (window as any).Telegram.WebApp
      tg.ready()
      // Настраиваем тему Telegram Web App
      tg.setHeaderColor("#1a1a20") // Темный фон
      tg.setBackgroundColor("#1a1a20")
      tg.enableClosingConfirmation()
      
      // Сохраняем данные пользователя из Telegram Web App
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
      // Сразу переходим на главный экран "Личный ассистент"
      router.push("/assistant")
    } else {
      // Проверяем, есть ли сохраненный пользователь
      const savedUser = localStorage.getItem("telegram_user")
      if (savedUser) {
        router.push("/assistant")
      } else {
        router.push("/login")
      }
    }
  }, [router])

  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <div className="text-center">
        <h1 className="text-2xl font-semibold text-foreground">TRACY</h1>
        <p className="mt-2 text-muted-foreground">Загрузка...</p>
      </div>
    </div>
  )
}

