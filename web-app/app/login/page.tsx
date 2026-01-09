"use client"

import { useEffect } from "react"
import Script from "next/script"

declare global {
  interface Window {
    onTelegramAuth?: (user: any) => void
  }
}

export default function LoginPage() {
  const botUsername = process.env.NEXT_PUBLIC_TELEGRAM_BOT_USERNAME || "tracy_aibot"

  useEffect(() => {
    window.onTelegramAuth = async (user: any) => {
      try {
        const response = await fetch("/api/auth/telegram", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(user),
        })

        if (response.ok) {
          window.location.href = "/calendar"
        } else {
          alert("Ошибка авторизации")
        }
      } catch (error) {
        console.error("Auth error:", error)
        alert("Ошибка авторизации")
      }
    }
  }, [])

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

