"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import Script from "next/script"

declare global {
  interface Window {
    Telegram?: {
      WebApp: any
    }
    onTelegramAuth?: (user: any) => void
  }
}

export default function LoginPage() {
  const router = useRouter()
  const botUsername = process.env.NEXT_PUBLIC_TELEGRAM_BOT_USERNAME || "tracy_aibot"

  useEffect(() => {
    // Если открыто через Telegram Web App, сразу переходим в календарь
    if (typeof window !== "undefined" && (window as any).Telegram?.WebApp) {
      const tg = (window as any).Telegram.WebApp
      tg.ready()
      router.push("/calendar")
      return
    }

    // Иначе показываем виджет авторизации
    window.onTelegramAuth = (user: any) => {
      // Сохраняем данные пользователя в localStorage
      localStorage.setItem("telegram_user", JSON.stringify(user))
      router.push("/calendar")
    }
  }, [router])

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <div className="w-full max-w-md space-y-8 rounded-2xl bg-card p-8 shadow-sm">
        <div className="text-center">
          <h1 className="text-3xl font-semibold">TRACY</h1>
          <p className="mt-2 text-muted-foreground">
            Войдите через Telegram
          </p>
        </div>

        <div
          id="telegram-login"
          data-telegram-login={botUsername}
          data-size="large"
          data-onauth="onTelegramAuth(user)"
          data-request-access="write"
          className="flex justify-center"
        />

        <Script
          src="https://telegram.org/js/telegram-widget.js?22"
          strategy="afterInteractive"
        />
      </div>
    </div>
  )
}

