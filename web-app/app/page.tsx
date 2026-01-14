"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"

export default function HomePage() {
  const router = useRouter()
  const [debug, setDebug] = useState<string[]>([])

  useEffect(() => {
    const log = (msg: string) => {
      console.log(`[HomePage] ${msg}`)
      setDebug(prev => [...prev, msg])
    }

    const navigate = (path: string) => {
      try {
        log(`Navigating to ${path}`)
        router.push(path)
      } catch (error) {
        log(`Navigation error: ${error}`)
        // Fallback: используем window.location
        window.location.href = path
      }
    }

    log("Initializing...")
    log(`URL: ${window.location.href}`)

    // Проверяем, открыто ли приложение через Telegram Web App
    // Примечание: Telegram WebApp уже инициализирован через TelegramBootstrap
    if (typeof window !== "undefined" && (window as any).Telegram?.WebApp) {
      const tg = (window as any).Telegram.WebApp
      log("Telegram WebApp detected")
      
      // Дополнительные настройки (если нужно)
      tg.enableClosingConfirmation()
      
      // Сохраняем данные пользователя из Telegram Web App
      const user = tg.initDataUnsafe?.user
      if (user) {
        log(`User found: ${user.first_name}`)
        localStorage.setItem("telegram_user", JSON.stringify({
          id: user.id.toString(),
          first_name: user.first_name,
          last_name: user.last_name,
          username: user.username,
          photo_url: user.photo_url,
        }))
        // Сразу переходим на главный экран "Личный ассистент"
        setTimeout(() => navigate("/assistant"), 100)
      } else {
        // Если нет пользователя в WebApp, проверяем localStorage
        const savedUser = localStorage.getItem("telegram_user")
        if (savedUser) {
          log("Saved user found, navigating to /assistant")
          setTimeout(() => navigate("/assistant"), 100)
        } else {
          log("No user, navigating to /login")
          setTimeout(() => navigate("/login"), 100)
        }
      }
    } else {
      log("Regular browser detected")
      // Проверяем, есть ли сохраненный пользователь
      const savedUser = localStorage.getItem("telegram_user")
      if (savedUser) {
        try {
          const parsed = JSON.parse(savedUser)
          log(`Saved user: ${parsed.first_name || parsed.id}`)
          if (parsed.id && parsed.id !== "demo") {
            setTimeout(() => navigate("/assistant"), 100)
          } else {
            log("Demo user, navigating to /login")
            setTimeout(() => navigate("/login"), 100)
          }
        } catch (e) {
          log("Error parsing user, navigating to /login")
          setTimeout(() => navigate("/login"), 100)
        }
      } else {
        log("No saved user, navigating to /login")
        setTimeout(() => navigate("/login"), 100)
      }
    }
  }, [router])

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <div className="text-center max-w-md">
        <h1 className="text-2xl font-semibold text-foreground">TRACY</h1>
        <p className="mt-2 text-muted-foreground">Загрузка...</p>
        {debug.length > 0 && (
          <div className="mt-4 p-4 bg-muted rounded text-left text-xs">
            {debug.map((msg, i) => (
              <div key={i} className="text-muted-foreground">{msg}</div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

