"use client"

import { useEffect } from "react"
import Link from "next/link"
import { Button } from "../components/ui/button"

export default function NotFound() {
  useEffect(() => {
    // Telegram Web App уже инициализирован через TelegramBootstrap
    // Дополнительная настройка не требуется
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
          <Button asChild>
            <Link href="/">На главную</Link>
          </Button>
          <Button asChild variant="outline">
            <Link href="/assistant">К ассистенту</Link>
          </Button>
        </div>
      </div>
    </div>
  )
}

