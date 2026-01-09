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
      router.push("/calendar")
      return
    }

    // Если уже есть сохраненный пользователь, переходим в календарь
    const savedUser = localStorage.getItem("telegram_user")
    if (savedUser) {
      router.push("/calendar")
      return
    }

    // Иначе показываем виджет авторизации (только если открыто не через Telegram Web App)
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

        <div className="space-y-4">
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

          <div className="text-center space-y-3">
            <p className="text-sm text-muted-foreground">
              Или откройте через Telegram бота
            </p>
            <a
              href={`https://t.me/${botUsername}`}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-block px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
            >
              Открыть в Telegram
            </a>
            <div className="pt-4 border-t">
              <button
                onClick={() => {
                  // Создаем демо-пользователя для просмотра интерфейса
                  localStorage.setItem("telegram_user", JSON.stringify({
                    id: "demo",
                    first_name: "Демо",
                    last_name: "Пользователь",
                    username: "demo",
                  }))
                  router.push("/calendar")
                }}
                className="text-sm text-muted-foreground hover:text-foreground underline"
              >
                Продолжить без авторизации (демо)
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

