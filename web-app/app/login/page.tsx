"use client"

// Login page for TRACY web app
import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import Script from "next/script"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card"
import { Button } from "../../components/ui/button"
import { MessageCircle, ExternalLink, Sparkles } from "lucide-react"

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
  const [isLoading, setIsLoading] = useState(true)
  const [isTelegramWebApp, setIsTelegramWebApp] = useState(false)
  const botUsername = process.env.NEXT_PUBLIC_TELEGRAM_BOT_USERNAME || "tracy_aibot"

  useEffect(() => {
    // Функция для проверки и авторизации через Telegram WebApp
    const checkTelegramAuth = () => {
      if (typeof window === "undefined") return false
      
      const tg = (window as any).Telegram?.WebApp
      if (!tg) return false
      
      // Telegram WebApp уже инициализирован через TelegramBootstrap
      setIsTelegramWebApp(true)
      
      // Пробуем получить пользователя из initDataUnsafe
      let user = tg.initDataUnsafe?.user
      
      // Если нет в initDataUnsafe, пробуем получить из initData
      if (!user && tg.initData) {
        try {
          // Парсим initData (формат: key=value&key2=value2)
          const params = new URLSearchParams(tg.initData)
          const userStr = params.get('user')
          if (userStr) {
            user = JSON.parse(decodeURIComponent(userStr))
          }
        } catch (e) {
          console.error('[Login] Error parsing initData:', e)
        }
      }
      
      if (user && user.id) {
        const userData = {
          id: user.id.toString(),
          first_name: user.first_name || "",
          last_name: user.last_name || "",
          username: user.username || "",
          photo_url: user.photo_url || "",
        }
        localStorage.setItem("telegram_user", JSON.stringify(userData))
        console.log('[Login] ✅ User authenticated via Telegram WebApp:', userData)
        router.push("/assistant")
        return true
      }
      
      return false
    }

    // Пробуем сразу
    if (checkTelegramAuth()) {
      return
    }

    // Если Telegram SDK еще не загрузился, ждем
    const checkInterval = setInterval(() => {
      if (checkTelegramAuth()) {
        clearInterval(checkInterval)
      }
    }, 100)

    // Останавливаем проверку через 3 секунды
    const timeout = setTimeout(() => {
      clearInterval(checkInterval)
      setIsLoading(false)
    }, 3000)

    // Если уже есть сохраненный пользователь, переходим
    const savedUser = localStorage.getItem("telegram_user")
    if (savedUser) {
      try {
        const parsed = JSON.parse(savedUser)
        if (parsed.id && parsed.id !== "demo") {
          clearInterval(checkInterval)
          clearTimeout(timeout)
          router.push("/assistant")
          return
        }
      } catch (e) {
        // Невалидные данные, удаляем
        localStorage.removeItem("telegram_user")
      }
    }

    return () => {
      clearInterval(checkInterval)
      clearTimeout(timeout)
    }

    // Настраиваем callback для Telegram Login Widget
    window.onTelegramAuth = (user: any) => {
      console.log("[Login] Telegram auth callback:", user)
      
      // Преобразуем данные пользователя в нужный формат
      const userData = {
        id: user.id.toString(), // Важно: преобразуем в строку
        first_name: user.first_name || "",
        last_name: user.last_name || "",
        username: user.username || "",
        photo_url: user.photo_url || "",
        auth_date: user.auth_date,
        hash: user.hash,
      }
      
      // Сохраняем в localStorage
      localStorage.setItem("telegram_user", JSON.stringify(userData))
      
      // Перенаправляем в приложение
      router.push("/assistant")
    }
    
    setIsLoading(false)
  }, [router])

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-primary border-r-transparent"></div>
          <p className="mt-4 text-muted-foreground">Загрузка...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center space-y-2">
          <div className="mx-auto h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center mb-4">
            <Sparkles className="h-8 w-8 text-primary" />
          </div>
          <CardTitle className="text-3xl">TRACY</CardTitle>
          <CardDescription className="text-base">
            AI-ассистент для управления календарем
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {!isTelegramWebApp && (
            <div className="space-y-4">
              <div className="text-center">
                <p className="text-sm font-medium mb-2">Войдите через Telegram</p>
                <p className="text-xs text-muted-foreground mb-4">
                  Авторизуйтесь, чтобы использовать все возможности TRACY
                </p>
              </div>
              
              {/* Telegram Login Widget */}
              <div className="flex justify-center">
                <div
                  id="telegram-login"
                  data-telegram-login={botUsername}
                  data-size="large"
                  data-onauth="onTelegramAuth(user)"
                  data-request-access="write"
                  data-userpic="true"
                  data-radius="8"
                />
              </div>

              <Script
                src="https://telegram.org/js/telegram-widget.js?22"
                strategy="afterInteractive"
              />

              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <span className="w-full border-t" />
                </div>
                <div className="relative flex justify-center text-xs uppercase">
                  <span className="bg-card px-2 text-muted-foreground">или</span>
                </div>
              </div>

              <Button
                variant="outline"
                className="w-full"
                onClick={() => {
                  window.open(`https://t.me/${botUsername}`, '_blank')
                }}
              >
                <MessageCircle className="mr-2 h-4 w-4" />
                Открыть в Telegram
                <ExternalLink className="ml-2 h-4 w-4" />
              </Button>
            </div>
          )}

          {isTelegramWebApp && (
            <div className="text-center space-y-4">
              <p className="text-sm text-muted-foreground">
                Приложение открыто через Telegram. Авторизация выполняется автоматически...
              </p>
            </div>
          )}

          <div className="pt-4 border-t">
            <div className="text-center">
              <button
                onClick={() => {
                  // Создаем демо-пользователя для просмотра интерфейса
                  localStorage.setItem("telegram_user", JSON.stringify({
                    id: "demo",
                    first_name: "Демо",
                    last_name: "Пользователь",
                    username: "demo",
                  }))
                  router.push("/assistant")
                }}
                className="text-xs text-muted-foreground hover:text-foreground underline transition-colors"
              >
                Продолжить без авторизации (демо-режим)
              </button>
              <p className="text-xs text-muted-foreground mt-2">
                В демо-режиме данные не сохраняются
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

