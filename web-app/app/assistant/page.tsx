"use client"

import { useEffect, useState, useRef, Suspense } from "react"
import { useRouter, usePathname, useSearchParams } from "next/navigation"
import Link from "next/link"
import { logger } from "../../lib/logger"
import { Calendar, Settings, Mic, FileAudio, History, Sparkles, MessageSquare, ListTodo, MessageCircle, Bug } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card"
import { Avatar, AvatarFallback, AvatarImage } from "../../components/ui/avatar"
import { Button } from "../../components/ui/button"
import { useTelegramUser } from "../../lib/useTelegramUser"

declare global {
  interface Window {
    __clientAlive?: boolean
  }
}

function AssistantPageContent() {
  const router = useRouter()
  const pathname = usePathname()
  const searchParams = useSearchParams()
  const { user: telegramUser, userId, isLoading: userLoading } = useTelegramUser()
  const [user, setUser] = useState<any>(null)
  const [isSuperUser, setIsSuperUser] = useState(false)
  const mountedRef = useRef(false)
  const lastPathnameRef = useRef<string | null>(null)
  const lastUserIdRef = useRef<string | null>(null)
  const debugMode = searchParams.get('debug') === '1'
  const eventCountsRef = useRef({ pointerdown: 0, click: 0, touchstart: 0 })
  const lastClickRef = useRef<{ target: string; timestamp: number } | null>(null)
  const lastNavAttemptRef = useRef<string | null>(null)

  // Диагностика в debug=1 режиме
  useEffect(() => {
    if (!debugMode || typeof window === 'undefined') return

    const handlePointerDown = (e: PointerEvent) => {
      eventCountsRef.current.pointerdown++
      lastClickRef.current = {
        target: (e.target as HTMLElement)?.tagName || 'unknown',
        timestamp: Date.now(),
      }
    }

    const handleClick = (e: MouseEvent) => {
      eventCountsRef.current.click++
      lastClickRef.current = {
        target: (e.target as HTMLElement)?.tagName || 'unknown',
        timestamp: Date.now(),
      }
    }

    const handleTouchStart = (e: TouchEvent) => {
      eventCountsRef.current.touchstart++
      lastClickRef.current = {
        target: (e.target as HTMLElement)?.tagName || 'unknown',
        timestamp: Date.now(),
      }
    }

    window.addEventListener('pointerdown', handlePointerDown, true)
    window.addEventListener('click', handleClick, true)
    window.addEventListener('touchstart', handleTouchStart, true)

    return () => {
      window.removeEventListener('pointerdown', handlePointerDown, true)
      window.removeEventListener('click', handleClick, true)
      window.removeEventListener('touchstart', handleTouchStart, true)
    }
  }, [debugMode])

  // ClientAlive маркер
  useEffect(() => {
    if (typeof window !== 'undefined') {
      console.log('[ClientAlive] AssistantPage mounted', window.location.href)
      window.__clientAlive = true
    }
  }, [])

  // Логируем mounted ТОЛЬКО один раз при монтировании компонента
  useEffect(() => {
    if (mountedRef.current === false) {
      logger.info('AssistantPage', 'Component mounted', { userLoading, userId })
      mountedRef.current = true
    }
  }, []) // Пустой deps - выполняется только при монтировании

  // Мониторинг изменений pathname (только при реальных изменениях)
  useEffect(() => {
    if (lastPathnameRef.current !== pathname) {
      logger.info('AssistantPage', 'Pathname changed', { pathname, windowPathname: typeof window !== 'undefined' ? window.location.pathname : 'N/A' })
      lastPathnameRef.current = pathname
    }
  }, [pathname])

  // Обработка пользователя - отдельный useEffect с правильными зависимостями
  useEffect(() => {
    // Если пользователь не загружен и не загружается, перенаправляем на логин
    if (!userLoading && !userId) {
      logger.warn('AssistantPage', 'No user, redirecting to login')
      router.push("/login")
      return
    }

    // Если пользователь загружен, обновляем состояние
    // Проверяем, что userId действительно изменился (идемпотентность)
    if (telegramUser && userId && lastUserIdRef.current !== userId) {
      const fullName = [telegramUser.first_name, telegramUser.last_name].filter(Boolean).join(" ")
      
      // Логируем только при реальном изменении userId
      logger.info('AssistantPage', 'User loaded', { userId, fullName })
      lastUserIdRef.current = userId
      
      setUser({
        id: userId,
        name: fullName || telegramUser.first_name || "Пользователь",
        avatarUrl: telegramUser.photo_url,
        first_name: telegramUser.first_name,
        last_name: telegramUser.last_name,
        username: telegramUser.username,
      })
      // Проверяем, является ли пользователь супер-пользователем (ID: 308477378)
      setIsSuperUser(userId === "308477378" || userId === "332023536")
    }

    // Telegram Web App уже инициализирован через TelegramBootstrap
    // Дополнительная настройка не требуется
  }, [userId, userLoading, telegramUser?.id, telegramUser?.first_name, telegramUser?.last_name, telegramUser?.username, telegramUser?.photo_url, router]) // Стабилизированные зависимости

  const displayName = user?.name || [user?.first_name, user?.last_name].filter(Boolean).join(" ") || "Пользователь"
  const avatarInitials = displayName
    .split(" ")
    .map((n: string) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2) || "U"

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      {/* Header */}
      <header className="sticky top-0 z-20 border-b border-border bg-background/95 backdrop-blur">
        <div className="flex h-14 items-center justify-between px-4">
          <div className="flex items-center gap-2">
            <div className="h-6 w-6 rounded-full bg-primary flex items-center justify-center">
              <span className="text-xs font-bold text-primary-foreground">T</span>
            </div>
            <span className="text-sm font-medium">TRACY</span>
          </div>
          <Link
            href="/settings"
            aria-label="Settings"
            className="text-foreground hover:text-muted-foreground transition-colors"
          >
            <Settings className="h-5 w-5" />
          </Link>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto">
        <div className="container mx-auto max-w-2xl px-4 py-6">
          <div className="mb-6">
            <h1 className="text-3xl font-semibold mb-2">Личный ассистент</h1>
            <p className="text-muted-foreground">
              Выберите инструмент для работы
            </p>
          </div>

          {/* Profile Card */}
          {user && (
            <Card className="mb-6 border-border">
              <CardContent className="pt-6">
                <div className="flex items-center gap-4">
                  <Avatar className="h-16 w-16">
                    <AvatarImage src={user?.avatarUrl || user?.photo_url} alt={displayName} />
                    <AvatarFallback className="bg-muted text-muted-foreground text-xl">
                      {avatarInitials}
                    </AvatarFallback>
                  </Avatar>
                  <div className="flex-1">
                    <h2 className="text-xl font-semibold">{displayName}</h2>
                    {user?.username && (
                      <p className="text-sm text-muted-foreground">@{user.username}</p>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Demo Mode Warning */}
          {userId === "demo" && (
            <Card className="mb-6 border-amber-500/50 bg-amber-500/10">
              <CardContent className="pt-6">
                <div className="flex items-start gap-4">
                  <div className="h-10 w-10 rounded-full bg-amber-500/20 flex items-center justify-center flex-shrink-0">
                    <MessageCircle className="h-5 w-5 text-amber-600 dark:text-amber-400" />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold mb-1 text-amber-900 dark:text-amber-100">
                      Вы в демо-режиме
                    </h3>
                    <p className="text-sm text-amber-800 dark:text-amber-200 mb-4">
                      Для полного доступа ко всем функциям и сохранения данных авторизуйтесь через Telegram
                    </p>
                    <Button asChild className="bg-amber-600 hover:bg-amber-700 text-white">
                      <Link href="/login">
                        <MessageCircle className="mr-2 h-4 w-4" />
                        Войти через Telegram
                      </Link>
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Main Features */}
          <div className="space-y-4">
            {/* Чат с Tracy */}
            <Link 
              href="/chat"
              className="block border border-border rounded-lg hover:bg-accent/50 transition-colors cursor-pointer p-6"
              onClick={() => {
                logger.info('AssistantPage', 'Card clicked: /chat')
                if (debugMode) {
                  lastNavAttemptRef.current = '/chat'
                }
              }}
            >
              <div className="flex items-center gap-4">
                <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center">
                  <MessageCircle className="h-6 w-6 text-primary" />
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold mb-1">Чат с Tracy</h3>
                  <p className="text-sm text-muted-foreground">
                    Онлайн чат с AI-ассистентом для планирования дня
                  </p>
                </div>
              </div>
            </Link>

            {/* Calendar */}
            <Link 
              href="/calendar"
              className="block border border-border rounded-lg hover:bg-accent/50 transition-colors cursor-pointer p-6"
              onClick={() => {
                logger.info('AssistantPage', 'Card clicked: /calendar')
                if (debugMode) {
                  lastNavAttemptRef.current = '/calendar'
                }
              }}
            >
              <div className="flex items-center gap-4">
                <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center">
                  <Calendar className="h-6 w-6 text-primary" />
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold mb-1">Календарь</h3>
                  <p className="text-sm text-muted-foreground">
                    Просмотр и управление событиями
                  </p>
                </div>
              </div>
            </Link>

            {/* История расшифровок */}
            <Link 
              href="/meetings/history"
              className="block border border-border rounded-lg hover:bg-accent/50 transition-colors cursor-pointer p-6"
              onClick={() => {
                logger.info('AssistantPage', 'Card clicked: /meetings/history')
                if (debugMode) {
                  lastNavAttemptRef.current = '/meetings/history'
                }
              }}
            >
              <div className="flex items-center gap-4">
                <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center">
                  <History className="h-6 w-6 text-primary" />
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold mb-1">История расшифровок</h3>
                  <p className="text-sm text-muted-foreground">
                    Просмотр всех расшифрованных встреч
                  </p>
                </div>
              </div>
            </Link>

            {/* Списки задач */}
            <Link 
              href="/todo-lists"
              className="block border border-border rounded-lg hover:bg-accent/50 transition-colors cursor-pointer p-6"
              onClick={() => {
                logger.info('AssistantPage', 'Card clicked: /todo-lists')
                if (debugMode) {
                  lastNavAttemptRef.current = '/todo-lists'
                }
              }}
            >
              <div className="flex items-center gap-4">
                <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center">
                  <ListTodo className="h-6 w-6 text-primary" />
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold mb-1">Списки задач</h3>
                  <p className="text-sm text-muted-foreground">
                    Создание и управление списками задач
                  </p>
                </div>
              </div>
            </Link>

            {/* Обратная связь (только для супер-пользователя) */}
            {isSuperUser && (
              <>
                <Link 
                  href="/settings/feedback"
                  className="block border border-border rounded-lg hover:bg-accent/50 transition-colors cursor-pointer p-6"
                  onClick={() => {
                    logger.info('AssistantPage', 'Card clicked: /settings/feedback')
                    if (debugMode) {
                      lastNavAttemptRef.current = '/settings/feedback'
                    }
                  }}
                >
                  <div className="flex items-center gap-4">
                    <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center">
                      <MessageSquare className="h-6 w-6 text-primary" />
                    </div>
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold mb-1">Обратная связь</h3>
                      <p className="text-sm text-muted-foreground">
                        Просмотр всех сообщений об ошибках и предложениях
                      </p>
                    </div>
                  </div>
                </Link>
                <Link 
                  href="/debug"
                  className="block border border-border rounded-lg hover:bg-accent/50 transition-colors cursor-pointer p-6"
                  onClick={() => {
                    logger.info('AssistantPage', 'Card clicked: /debug')
                    if (debugMode) {
                      lastNavAttemptRef.current = '/debug'
                    }
                  }}
                >
                  <div className="flex items-center gap-4">
                    <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center">
                      <Settings className="h-6 w-6 text-primary" />
                    </div>
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold mb-1">Debug: Network</h3>
                      <p className="text-sm text-muted-foreground">
                        Мониторинг сетевых запросов и диагностика ошибок
                      </p>
                    </div>
                  </div>
                </Link>
              </>
            )}
          </div>
        </div>
      </div>

      {debugMode && (
        <div className="fixed bottom-4 right-4 bg-black/90 text-white p-4 rounded-lg text-xs font-mono z-50 max-w-xs">
          <div className="mb-2 font-bold">Debug (assistant)</div>
          <div>Pathname: {pathname}</div>
          <div>Mounted: {mountedRef.current ? 'YES' : 'NO'}</div>
          <div>IsTelegram: {typeof window !== 'undefined' && (window as any).Telegram?.WebApp ? 'YES' : 'NO'}</div>
          <div>Events: p={eventCountsRef.current.pointerdown} c={eventCountsRef.current.click} t={eventCountsRef.current.touchstart}</div>
          {lastClickRef.current && (
            <div>LastClick: {lastClickRef.current.target} @ {new Date(lastClickRef.current.timestamp).toLocaleTimeString()}</div>
          )}
          {lastNavAttemptRef.current && (
            <div>LastNav: {lastNavAttemptRef.current}</div>
          )}
        </div>
      )}
    </div>
  )
}

export default function AssistantPage() {
  return (
    <Suspense fallback={
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-primary border-r-transparent"></div>
          <p className="mt-4 text-muted-foreground">Загрузка...</p>
        </div>
      </div>
    }>
      <AssistantPageContent />
    </Suspense>
  )
}

