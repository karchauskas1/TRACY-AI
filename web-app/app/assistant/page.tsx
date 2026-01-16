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

          {/* Profile Card - MODERNIZED */}
          {user && (
            <Card variant="gradient" className="mb-6 border-0 overflow-hidden relative">
              {/* Animated gradient background */}
              <div className="absolute inset-0 bg-gradient-to-br from-primary/20 via-purple-500/10 to-pink-500/20 opacity-50" />

              <CardContent className="pt-6 relative z-10">
                <div className="flex items-center gap-4">
                  <div className="relative">
                    <Avatar className="h-20 w-20 ring-4 ring-white/20 shadow-xl">
                      <AvatarImage src={user?.avatarUrl || user?.photo_url} alt={displayName} />
                      <AvatarFallback className="bg-gradient-to-br from-primary to-purple-600 text-white text-2xl font-bold">
                        {avatarInitials}
                      </AvatarFallback>
                    </Avatar>
                    {/* Online indicator */}
                    <div className="absolute bottom-0 right-0 h-5 w-5 bg-green-500 rounded-full border-4 border-white dark:border-card shadow-lg" />
                  </div>
                  <div className="flex-1">
                    <h2 className="text-2xl font-bold bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text">
                      {displayName}
                    </h2>
                    {user?.username && (
                      <p className="text-sm text-muted-foreground mt-1">@{user.username}</p>
                    )}
                    <div className="flex items-center gap-2 mt-2">
                      <div className="px-3 py-1 bg-gradient-to-r from-primary/20 to-purple-500/20 border border-primary/30 text-primary dark:text-primary-foreground rounded-full text-xs font-semibold backdrop-blur-sm shadow-sm">
                        ✨ Premium
                      </div>
                    </div>
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
            {/* Чат с Tracy - MODERNIZED */}
            <Link
              href="/chat"
              className="block group"
              onClick={() => {
                logger.info('AssistantPage', 'Card clicked: /chat')
                if (debugMode) {
                  lastNavAttemptRef.current = '/chat'
                }
              }}
            >
              <div className="relative overflow-hidden rounded-3xl border-0 bg-card shadow-lg hover:shadow-2xl transition-all duration-300 hover:-translate-y-1">
                {/* Gradient line on top */}
                <div className="h-1 bg-gradient-to-r from-primary via-purple-500 to-pink-500" />

                <div className="p-6">
                  <div className="flex items-center gap-4">
                    {/* Icon with gradient and glow */}
                    <div className="relative">
                      <div className="absolute inset-0 bg-gradient-to-br from-primary to-purple-600 rounded-2xl blur-lg opacity-50 group-hover:opacity-75 transition-opacity" />
                      <div className="relative h-14 w-14 rounded-2xl bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform duration-300">
                        <MessageCircle className="h-7 w-7 text-white" />
                      </div>
                    </div>

                    <div className="flex-1">
                      <h3 className="text-xl font-bold mb-1 group-hover:text-primary transition-colors">
                        Чат с Tracy
                      </h3>
                      <p className="text-sm text-muted-foreground leading-relaxed">
                        Онлайн чат с AI-ассистентом для планирования дня
                      </p>
                    </div>

                    {/* Arrow */}
                    <div className="text-muted-foreground group-hover:text-primary group-hover:translate-x-1 transition-all">
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </div>
                  </div>
                </div>
              </div>
            </Link>

            {/* Calendar - MODERNIZED */}
            <Link
              href="/calendar"
              className="block group"
              onClick={() => {
                logger.info('AssistantPage', 'Card clicked: /calendar')
                if (debugMode) {
                  lastNavAttemptRef.current = '/calendar'
                }
              }}
            >
              <div className="relative overflow-hidden rounded-3xl border-0 bg-card shadow-lg hover:shadow-2xl transition-all duration-300 hover:-translate-y-1">
                <div className="h-1 bg-gradient-to-r from-blue-500 via-cyan-500 to-teal-500" />

                <div className="p-6">
                  <div className="flex items-center gap-4">
                    <div className="relative">
                      <div className="absolute inset-0 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-2xl blur-lg opacity-50 group-hover:opacity-75 transition-opacity" />
                      <div className="relative h-14 w-14 rounded-2xl bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform duration-300">
                        <Calendar className="h-7 w-7 text-white" />
                      </div>
                    </div>

                    <div className="flex-1">
                      <h3 className="text-xl font-bold mb-1 group-hover:text-blue-500 transition-colors">
                        Календарь
                      </h3>
                      <p className="text-sm text-muted-foreground leading-relaxed">
                        Просмотр и управление событиями
                      </p>
                    </div>

                    <div className="text-muted-foreground group-hover:text-blue-500 group-hover:translate-x-1 transition-all">
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </div>
                  </div>
                </div>
              </div>
            </Link>

            {/* История расшифровок - MODERNIZED */}
            <Link
              href="/meetings/history"
              className="block group"
              onClick={() => {
                logger.info('AssistantPage', 'Card clicked: /meetings/history')
                if (debugMode) {
                  lastNavAttemptRef.current = '/meetings/history'
                }
              }}
            >
              <div className="relative overflow-hidden rounded-3xl border-0 bg-card shadow-lg hover:shadow-2xl transition-all duration-300 hover:-translate-y-1">
                <div className="h-1 bg-gradient-to-r from-orange-500 via-red-500 to-pink-500" />

                <div className="p-6">
                  <div className="flex items-center gap-4">
                    <div className="relative">
                      <div className="absolute inset-0 bg-gradient-to-br from-orange-500 to-red-500 rounded-2xl blur-lg opacity-50 group-hover:opacity-75 transition-opacity" />
                      <div className="relative h-14 w-14 rounded-2xl bg-gradient-to-br from-orange-500 to-red-500 flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform duration-300">
                        <History className="h-7 w-7 text-white" />
                      </div>
                    </div>

                    <div className="flex-1">
                      <h3 className="text-xl font-bold mb-1 group-hover:text-orange-500 transition-colors">
                        История расшифровок
                      </h3>
                      <p className="text-sm text-muted-foreground leading-relaxed">
                        Просмотр всех расшифрованных встреч
                      </p>
                    </div>

                    <div className="text-muted-foreground group-hover:text-orange-500 group-hover:translate-x-1 transition-all">
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </div>
                  </div>
                </div>
              </div>
            </Link>

            {/* Списки задач - MODERNIZED */}
            <Link
              href="/todo-lists"
              className="block group"
              onClick={() => {
                logger.info('AssistantPage', 'Card clicked: /todo-lists')
                if (debugMode) {
                  lastNavAttemptRef.current = '/todo-lists'
                }
              }}
            >
              <div className="relative overflow-hidden rounded-3xl border-0 bg-card shadow-lg hover:shadow-2xl transition-all duration-300 hover:-translate-y-1">
                <div className="h-1 bg-gradient-to-r from-green-500 via-emerald-500 to-teal-500" />

                <div className="p-6">
                  <div className="flex items-center gap-4">
                    <div className="relative">
                      <div className="absolute inset-0 bg-gradient-to-br from-green-500 to-teal-500 rounded-2xl blur-lg opacity-50 group-hover:opacity-75 transition-opacity" />
                      <div className="relative h-14 w-14 rounded-2xl bg-gradient-to-br from-green-500 to-teal-500 flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform duration-300">
                        <ListTodo className="h-7 w-7 text-white" />
                      </div>
                    </div>

                    <div className="flex-1">
                      <h3 className="text-xl font-bold mb-1 group-hover:text-green-500 transition-colors">
                        Списки задач
                      </h3>
                      <p className="text-sm text-muted-foreground leading-relaxed">
                        Создание и управление списками задач
                      </p>
                    </div>

                    <div className="text-muted-foreground group-hover:text-green-500 group-hover:translate-x-1 transition-all">
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </div>
                  </div>
                </div>
              </div>
            </Link>

            {/* Обратная связь (только для супер-пользователя) */}
            {isSuperUser && (
              <>
                <Link
                  href="/settings/feedback"
                  className="block group"
                  onClick={() => {
                    logger.info('AssistantPage', 'Card clicked: /settings/feedback')
                    if (debugMode) {
                      lastNavAttemptRef.current = '/settings/feedback'
                    }
                  }}
                >
                  <div className="relative overflow-hidden rounded-3xl border-0 bg-card shadow-lg hover:shadow-2xl transition-all duration-300 hover:-translate-y-1">
                    <div className="h-1 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500" />

                    <div className="p-6">
                      <div className="flex items-center gap-4">
                        <div className="relative">
                          <div className="absolute inset-0 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-2xl blur-lg opacity-50 group-hover:opacity-75 transition-opacity" />
                          <div className="relative h-14 w-14 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform duration-300">
                            <MessageSquare className="h-7 w-7 text-white" />
                          </div>
                        </div>

                        <div className="flex-1">
                          <h3 className="text-xl font-bold mb-1 group-hover:text-indigo-500 transition-colors">
                            Обратная связь
                          </h3>
                          <p className="text-sm text-muted-foreground leading-relaxed">
                            Просмотр всех сообщений об ошибках и предложениях
                          </p>
                        </div>

                        <div className="text-muted-foreground group-hover:text-indigo-500 group-hover:translate-x-1 transition-all">
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                          </svg>
                        </div>
                      </div>
                    </div>
                  </div>
                </Link>

                <Link
                  href="/debug"
                  className="block group"
                  onClick={() => {
                    logger.info('AssistantPage', 'Card clicked: /debug')
                    if (debugMode) {
                      lastNavAttemptRef.current = '/debug'
                    }
                  }}
                >
                  <div className="relative overflow-hidden rounded-3xl border-0 bg-card shadow-lg hover:shadow-2xl transition-all duration-300 hover:-translate-y-1">
                    <div className="h-1 bg-gradient-to-r from-slate-500 via-gray-500 to-zinc-500" />

                    <div className="p-6">
                      <div className="flex items-center gap-4">
                        <div className="relative">
                          <div className="absolute inset-0 bg-gradient-to-br from-slate-500 to-gray-600 rounded-2xl blur-lg opacity-50 group-hover:opacity-75 transition-opacity" />
                          <div className="relative h-14 w-14 rounded-2xl bg-gradient-to-br from-slate-500 to-gray-600 flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform duration-300">
                            <Bug className="h-7 w-7 text-white" />
                          </div>
                        </div>

                        <div className="flex-1">
                          <h3 className="text-xl font-bold mb-1 group-hover:text-slate-500 transition-colors">
                            Debug: Network
                          </h3>
                          <p className="text-sm text-muted-foreground leading-relaxed">
                            Мониторинг сетевых запросов и диагностика ошибок
                          </p>
                        </div>

                        <div className="text-muted-foreground group-hover:text-slate-500 group-hover:translate-x-1 transition-all">
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                          </svg>
                        </div>
                      </div>
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
          <div className="relative">
            {/* Glow effect */}
            <div className="absolute inset-0 bg-gradient-to-r from-primary to-purple-600 rounded-full blur-2xl opacity-20 animate-pulse" />
            {/* Spinner */}
            <div className="relative inline-block h-12 w-12 animate-spin rounded-full border-4 border-solid border-primary/20 border-t-primary"></div>
          </div>
        </div>
      </div>
    }>
      <AssistantPageContent />
    </Suspense>
  )
}

