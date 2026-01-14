"use client"

import { useEffect, useState } from "react"
import { useRouter, usePathname } from "next/navigation"
import { logger } from "../../lib/logger"
import { Calendar, Settings, Mic, FileAudio, History, Sparkles, MessageSquare, ListTodo, MessageCircle, Bug } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card"
import { Avatar, AvatarFallback, AvatarImage } from "../../components/ui/avatar"
import { Button } from "../../components/ui/button"
import { useTelegramUser } from "../../lib/useTelegramUser"

export default function AssistantPage() {
  const router = useRouter()
  const pathname = usePathname()
  const { user: telegramUser, userId, isLoading: userLoading } = useTelegramUser()
  const [user, setUser] = useState<any>(null)
  const [isSuperUser, setIsSuperUser] = useState(false)
  const mountedRef = useRef(false)
  const lastPathnameRef = useRef<string | null>(null)
  const lastUserIdRef = useRef<string | null>(null)

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
          <button 
            onClick={() => router.push('/settings')}
            className="text-foreground hover:text-muted-foreground transition-colors"
          >
            <Settings className="h-5 w-5" />
          </button>
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
                    <Button
                      onClick={() => router.push('/login')}
                      className="bg-amber-600 hover:bg-amber-700 text-white"
                    >
                      <MessageCircle className="mr-2 h-4 w-4" />
                      Войти через Telegram
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Main Features */}
          <div className="space-y-4">
            {/* Чат с Tracy */}
            <div 
              className="block border border-border rounded-lg hover:bg-accent/50 transition-colors cursor-pointer p-6"
              onClick={(e) => {
                logger.debug('AssistantPage', 'Click on Чат с Tracy', {
                  target: e.target,
                  currentTarget: e.currentTarget,
                  targetTag: (e.target as HTMLElement)?.tagName,
                  currentTargetTag: (e.currentTarget as HTMLElement)?.tagName,
                  timestamp: Date.now(),
                })
                
                e.preventDefault()
                e.stopPropagation()
                
                logger.info('AssistantPage', 'Calling router.push(/chat)', {
                  beforePathname: pathname,
                  routerExists: !!router,
                })
                
                try {
                  router.push("/chat")
                  logger.info('AssistantPage', 'router.push(/chat) called successfully')
                } catch (error) {
                  logger.error('AssistantPage', 'Error in router.push(/chat)', { error })
                }
              }}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault()
                  router.push("/chat")
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
            </div>

            {/* Calendar */}
            <div 
              className="block border border-border rounded-lg hover:bg-accent/50 transition-colors cursor-pointer p-6"
              onClick={(e) => {
                logger.debug('AssistantPage', 'Click on Календарь', {
                  target: e.target,
                  currentTarget: e.currentTarget,
                  targetTag: (e.target as HTMLElement)?.tagName,
                  currentTargetTag: (e.currentTarget as HTMLElement)?.tagName,
                  timestamp: Date.now(),
                })
                
                e.preventDefault()
                e.stopPropagation()
                
                logger.info('AssistantPage', 'Calling router.push(/calendar)', {
                  beforePathname: pathname,
                  routerExists: !!router,
                })
                
                try {
                  router.push("/calendar")
                  logger.info('AssistantPage', 'router.push(/calendar) called successfully')
                } catch (error) {
                  logger.error('AssistantPage', 'Error in router.push(/calendar)', { error })
                }
              }}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault()
                  router.push("/calendar")
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
            </div>

            {/* История расшифровок */}
            <div 
              className="block border border-border rounded-lg hover:bg-accent/50 transition-colors cursor-pointer p-6"
              onClick={(e) => {
                e.preventDefault()
                e.stopPropagation()
                console.log("[AssistantPage] Navigate to /meetings/history via router.push")
                router.push("/meetings/history")
              }}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault()
                  router.push("/meetings/history")
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
            </div>

            {/* Списки задач */}
            <div 
              className="block border border-border rounded-lg hover:bg-accent/50 transition-colors cursor-pointer p-6"
              onClick={(e) => {
                logger.debug('AssistantPage', 'Click on Списки задач', {
                  target: e.target,
                  currentTarget: e.currentTarget,
                  targetTag: (e.target as HTMLElement)?.tagName,
                  currentTargetTag: (e.currentTarget as HTMLElement)?.tagName,
                  timestamp: Date.now(),
                })
                
                e.preventDefault()
                e.stopPropagation()
                
                logger.info('AssistantPage', 'Calling router.push(/todo-lists)', {
                  beforePathname: pathname,
                  routerExists: !!router,
                })
                
                try {
                  router.push("/todo-lists")
                  logger.info('AssistantPage', 'router.push(/todo-lists) called successfully')
                } catch (error) {
                  logger.error('AssistantPage', 'Error in router.push(/todo-lists)', { error })
                }
              }}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault()
                  router.push("/todo-lists")
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
            </div>

            {/* Обратная связь (только для супер-пользователя) */}
            {isSuperUser && (
              <>
                <div 
                  className="block border border-border rounded-lg hover:bg-accent/50 transition-colors cursor-pointer p-6"
                  onClick={(e) => {
                    e.preventDefault()
                    e.stopPropagation()
                    console.log("[AssistantPage] Navigate to /settings/feedback via router.push")
                    router.push("/settings/feedback")
                  }}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault()
                      router.push("/settings/feedback")
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
                </div>
                <div 
                  className="block border border-border rounded-lg hover:bg-accent/50 transition-colors cursor-pointer p-6"
                  onClick={(e) => {
                    e.preventDefault()
                    e.stopPropagation()
                    console.log("[AssistantPage] Navigate to /debug via router.push")
                    router.push("/debug")
                  }}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault()
                      router.push("/debug")
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
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

