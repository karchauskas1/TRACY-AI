"use client"

// Login page for TRACY web app
import { useEffect, useState, useRef, Suspense } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import Script from "next/script"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card"
import { Button } from "../../components/ui/button"
import { MessageCircle, ExternalLink, Sparkles, Loader2 } from "lucide-react"
import { useToast } from "../../hooks/use-toast"
import { logger } from "../../lib/logger"

declare global {
  interface Window {
    Telegram?: {
      WebApp: any
    }
    onTelegramAuth?: (user: any) => void
    __clientAlive?: boolean
  }
}

function LoginPageContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { toast } = useToast()
  const [isLoading, setIsLoading] = useState(true)
  const [isTelegramWebApp, setIsTelegramWebApp] = useState(false)
  const [authLoading, setAuthLoading] = useState(false)
  const [authError, setAuthError] = useState<string | null>(null)
  const botUsername = process.env.NEXT_PUBLIC_TELEGRAM_BOT_USERNAME || "tracy_aibot"
  const debugMode = searchParams.get('debug') === '1'
  const clickLogRef = useRef<Array<{ type: string; target: string; timestamp: number }>>([])

  // ClientAlive маркер
  useEffect(() => {
    if (typeof window !== 'undefined') {
      console.log('[ClientAlive] LoginPage mounted', window.location.href)
      window.__clientAlive = true
    }
  }, [])

  // Логирование кликов для диагностики (только в debug режиме)
  useEffect(() => {
    if (!debugMode || typeof window === 'undefined') return

    const handlePointerDown = (e: PointerEvent) => {
      clickLogRef.current.push({
        type: 'pointerdown',
        target: (e.target as HTMLElement)?.tagName || 'unknown',
        timestamp: Date.now(),
      })
      if (clickLogRef.current.length > 50) clickLogRef.current.shift()
      logger.debug('LoginPage', 'PointerDown captured', {
        target: (e.target as HTMLElement)?.tagName,
        className: (e.target as HTMLElement)?.className,
      })
    }

    const handleClick = (e: MouseEvent) => {
      clickLogRef.current.push({
        type: 'click',
        target: (e.target as HTMLElement)?.tagName || 'unknown',
        timestamp: Date.now(),
      })
      if (clickLogRef.current.length > 50) clickLogRef.current.shift()
      logger.debug('LoginPage', 'Click captured', {
        target: (e.target as HTMLElement)?.tagName,
        className: (e.target as HTMLElement)?.className,
      })
    }

    window.addEventListener('pointerdown', handlePointerDown, true)
    window.addEventListener('click', handleClick, true)

    return () => {
      window.removeEventListener('pointerdown', handlePointerDown, true)
      window.removeEventListener('click', handleClick, true)
    }
  }, [debugMode])

  // Автоматическая проверка авторизации при загрузке
  useEffect(() => {
    const checkTelegramAuth = () => {
      if (typeof window === "undefined") return false
      
      const tg = (window as any).Telegram?.WebApp
      if (!tg) return false
      
      setIsTelegramWebApp(true)
      
      // Пробуем получить пользователя из initDataUnsafe (быстрый путь)
      let user = tg.initDataUnsafe?.user
      
      // Если нет в initDataUnsafe, пробуем получить из initData
      if (!user && tg.initData) {
        try {
          const params = new URLSearchParams(tg.initData)
          const userStr = params.get('user')
          if (userStr) {
            user = JSON.parse(decodeURIComponent(userStr))
          }
        } catch (e) {
          logger.error('LoginPage', 'Error parsing initData', { error: e })
        }
      }
      
      if (user && user.id) {
        // Автоматическая авторизация через initDataUnsafe (без верификации на backend)
        // Это работает только если initDataUnsafe доступен
        const userData = {
          id: user.id.toString(),
          first_name: user.first_name || "",
          last_name: user.last_name || "",
          username: user.username || "",
          photo_url: user.photo_url || "",
        }
        localStorage.setItem("telegram_user", JSON.stringify(userData))
        logger.info('LoginPage', 'Auto-authenticated via Telegram WebApp', { userId: userData.id })
        router.push("/assistant")
        return true
      }
      
      return false
    }

    // Пробуем сразу
    if (checkTelegramAuth()) {
      setIsLoading(false)
      return
    }

    // Если Telegram SDK еще не загрузился, ждем
    const checkInterval = setInterval(() => {
      if (checkTelegramAuth()) {
        clearInterval(checkInterval)
        setIsLoading(false)
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
        localStorage.removeItem("telegram_user")
      }
    }

    return () => {
      clearInterval(checkInterval)
      clearTimeout(timeout)
    }

    // Настраиваем callback для Telegram Login Widget (для обычного браузера)
    window.onTelegramAuth = (user: any) => {
      logger.info('LoginPage', 'Telegram auth callback (Login Widget)', { userId: user.id })
      
      const userData = {
        id: user.id.toString(),
        first_name: user.first_name || "",
        last_name: user.last_name || "",
        username: user.username || "",
        photo_url: user.photo_url || "",
        auth_date: user.auth_date,
        hash: user.hash,
      }
      
      localStorage.setItem("telegram_user", JSON.stringify(userData))
      router.push("/assistant")
    }
    
    setIsLoading(false)
  }, [router, debugMode])

  // Обработчик клика на кнопку "Войти через Telegram" для Mini App
  const handleTelegramLogin = async () => {
    console.log('[LoginPage] Login button clicked')
    logger.info('LoginPage', 'Telegram login button clicked')
    
    if (typeof window === "undefined") return
    
    const tg = (window as any).Telegram?.WebApp
    if (!tg || !tg.initData) {
      logger.error('LoginPage', 'Telegram WebApp or initData not available')
      setAuthError("Telegram WebApp не доступен. Откройте приложение через Telegram.")
      toast({
        title: "Ошибка",
        description: "Telegram WebApp не доступен. Откройте приложение через Telegram.",
        variant: "destructive",
      })
      return
    }

    try {
      setAuthLoading(true)
      setAuthError(null)
      logger.info('LoginPage', 'Starting Telegram auth', { hasInitData: !!tg.initData })

      // Отправляем initData на backend для верификации
      const response = await fetch('/api/auth/telegram', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          initData: tg.initData,
        }),
      })

      const data = await response.json()

      if (!response.ok || !data.success) {
        throw new Error(data.error || 'Ошибка авторизации')
      }

      // Сессия установлена через httpOnly cookie
      // Проверяем что cookie установлена
      const cookies = document.cookie.split(';')
      const hasSession = cookies.some(c => c.trim().startsWith('tracy_session='))
      
      if (!hasSession) {
        logger.warn('LoginPage', 'Session cookie not found after auth')
      }

      // Сохраняем данные пользователя в localStorage для совместимости
      const userData = {
        id: data.user.id,
        first_name: data.user.first_name || "",
        last_name: data.user.last_name || "",
        username: data.user.username || "",
        photo_url: data.user.photo_url || "",
      }
      
      localStorage.setItem("telegram_user", JSON.stringify(userData))
      logger.info('LoginPage', 'Telegram auth successful via /api/auth/telegram', { userId: userData.id, hasSession })
      
      toast({
        title: "Успешно",
        description: `Добро пожаловать, ${userData.first_name}!`,
      })

      // Перенаправляем в приложение
      router.replace("/assistant")
    } catch (error: any) {
      logger.error('LoginPage', 'Telegram auth failed', { error: error.message })
      const errorMessage = error.message || "Не удалось авторизоваться через Telegram"
      setAuthError(errorMessage)
      toast({
        title: "Ошибка авторизации",
        description: errorMessage,
        variant: "destructive",
      })
    } finally {
      setAuthLoading(false)
    }
  }

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
            <div className="space-y-4">
              <div className="text-center">
                <p className="text-sm font-medium mb-2">Войти через Telegram</p>
                <p className="text-xs text-muted-foreground mb-4">
                  Авторизуйтесь, чтобы использовать все возможности TRACY
                </p>
              </div>
              
              <Button
                onClick={handleTelegramLogin}
                disabled={authLoading}
                className="w-full"
                size="lg"
              >
                {authLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Авторизация...
                  </>
                ) : (
                  <>
                    <MessageCircle className="mr-2 h-4 w-4" />
                    Войти через Telegram
                  </>
                )}
              </Button>

              {authError && (
                <div className="text-sm text-destructive text-center">
                  {authError}
                </div>
              )}

              {debugMode && clickLogRef.current.length > 0 && (
                <div className="mt-4 p-2 bg-muted rounded text-xs">
                  <p className="font-semibold mb-1">Debug: Click Logs</p>
                  <pre className="text-xs overflow-auto max-h-32">
                    {JSON.stringify(clickLogRef.current.slice(-10), null, 2)}
                  </pre>
                </div>
              )}
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

export default function LoginPage() {
  return (
    <Suspense fallback={
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-primary border-r-transparent"></div>
          <p className="mt-4 text-muted-foreground">Загрузка...</p>
        </div>
      </div>
    }>
      <LoginPageContent />
    </Suspense>
  )
}
