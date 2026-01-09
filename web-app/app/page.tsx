"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"

export default function HomePage() {
  const router = useRouter()

  useEffect(() => {
    // Проверяем, открыто ли приложение через Telegram Web App
    if (typeof window !== "undefined" && (window as any).Telegram?.WebApp) {
      router.push("/calendar")
    } else {
      router.push("/login")
    }
  }, [router])

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="text-center">
        <h1 className="text-2xl font-semibold">TRACY</h1>
        <p className="mt-2 text-muted-foreground">Загрузка...</p>
      </div>
    </div>
  )
}

