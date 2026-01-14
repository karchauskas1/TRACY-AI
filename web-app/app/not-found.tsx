"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { Button } from "../components/ui/button"

export default function NotFound() {
  const router = useRouter()

  useEffect(() => {
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
  }, [])

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <div className="text-center max-w-md">
        <h1 className="text-4xl font-bold mb-4">404</h1>
        <h2 className="text-2xl font-semibold mb-2">Страница не найдена</h2>
        <p className="text-muted-foreground mb-6">
          Запрашиваемая страница не существует или была перемещена.
        </p>
        <div className="flex gap-4 justify-center">
          <Button onClick={() => router.push("/")}>
            На главную
          </Button>
          <Button onClick={() => router.push("/assistant")} variant="outline">
            К ассистенту
          </Button>
        </div>
      </div>
    </div>
  )
}

