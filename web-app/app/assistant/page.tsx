"use client"

import { useEffect, useState, useRef, Suspense, useCallback } from "react"
import { useRouter, usePathname, useSearchParams } from "next/navigation"
import Link from "next/link"
import { logger } from "../../lib/logger"
import { Calendar, Settings, Mic, FileAudio, History, Sparkles, MessageSquare, ListTodo, MessageCircle, Bug, ArrowDownUp, Check } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card"
import { Avatar, AvatarFallback, AvatarImage } from "../../components/ui/avatar"
import { Button } from "../../components/ui/button"
import { useTelegramUser } from "../../lib/useTelegramUser"

// Определение плиток для главного экрана
interface TileConfig {
  id: string
  href: string
  title: string
  description: string
  icon: React.ReactNode
  gradient: string
  gradientLine: string
  hoverColor: string
  superUserOnly?: boolean
}

const DEFAULT_TILE_ORDER = ['chat', 'calendar', 'history', 'todos', 'feedback', 'debug']

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

  // Drag-and-drop состояние для плиток
  const [tileOrder, setTileOrder] = useState<string[]>(DEFAULT_TILE_ORDER)
  const [draggedTile, setDraggedTile] = useState<string | null>(null)
  const [dragOverTile, setDragOverTile] = useState<string | null>(null)
  const [isEditMode, setIsEditMode] = useState(false)

  // Touch drag state
  const touchStartRef = useRef<{ x: number; y: number; tileId: string; time: number } | null>(null)
  const touchDragActiveRef = useRef(false)
  const tileRefsMap = useRef<Map<string, HTMLDivElement>>(new Map())

  // Загрузка порядка плиток из localStorage
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('tile_order')
      if (saved) {
        try {
          const parsed = JSON.parse(saved)
          if (Array.isArray(parsed) && parsed.length === DEFAULT_TILE_ORDER.length) {
            setTileOrder(parsed)
          }
        } catch (e) {
          console.error('Failed to parse tile order:', e)
        }
      }
    }
  }, [])

  // Обработчики drag-and-drop (Desktop)
  const handleDragStart = useCallback((e: React.DragEvent, tileId: string) => {
    setDraggedTile(tileId)
    e.dataTransfer.effectAllowed = 'move'
    e.dataTransfer.setData('text/plain', tileId)
    setTimeout(() => {
      (e.target as HTMLElement).style.opacity = '0.5'
    }, 0)
  }, [])

  const handleDragEnd = useCallback((e: React.DragEvent) => {
    (e.target as HTMLElement).style.opacity = '1'
    setDraggedTile(null)
    setDragOverTile(null)
  }, [])

  const handleDragOver = useCallback((e: React.DragEvent, tileId: string) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
    if (draggedTile && draggedTile !== tileId) {
      setDragOverTile(tileId)
    }
  }, [draggedTile])

  const handleDragLeave = useCallback(() => {
    setDragOverTile(null)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent, targetTileId: string) => {
    e.preventDefault()
    const sourceTileId = e.dataTransfer.getData('text/plain')

    if (sourceTileId && sourceTileId !== targetTileId) {
      setTileOrder(prevOrder => {
        const newOrder = [...prevOrder]
        const sourceIndex = newOrder.indexOf(sourceTileId)
        const targetIndex = newOrder.indexOf(targetTileId)

        if (sourceIndex !== -1 && targetIndex !== -1) {
          newOrder.splice(sourceIndex, 1)
          newOrder.splice(targetIndex, 0, sourceTileId)
          localStorage.setItem('tile_order', JSON.stringify(newOrder))
        }

        return newOrder
      })
    }

    setDraggedTile(null)
    setDragOverTile(null)
  }, [])

  // Track if drag happened to prevent click
  const didDragRef = useRef(false)

  // Touch handlers for mobile drag-and-drop - now on entire tile
  const handleTileTouchStart = useCallback((e: React.TouchEvent, tileId: string) => {
    if (!isEditMode) return

    // Prevent scrolling in edit mode
    e.preventDefault()

    const touch = e.touches[0]
    touchStartRef.current = { x: touch.clientX, y: touch.clientY, tileId, time: Date.now() }
    touchDragActiveRef.current = false
    didDragRef.current = false
  }, [isEditMode])

  const handleTileTouchMove = useCallback((e: React.TouchEvent, tileId: string) => {
    if (!isEditMode || !touchStartRef.current || touchStartRef.current.tileId !== tileId) return

    // Always prevent default in edit mode to stop scrolling
    e.preventDefault()

    const touch = e.touches[0]
    const deltaX = Math.abs(touch.clientX - touchStartRef.current.x)
    const deltaY = Math.abs(touch.clientY - touchStartRef.current.y)

    // Mark as drag even with small movement to prevent accidental clicks
    if (deltaX > 5 || deltaY > 5) {
      didDragRef.current = true
    }

    // Activate drag after larger movement threshold
    if (!touchDragActiveRef.current && (deltaX > 10 || deltaY > 10)) {
      touchDragActiveRef.current = true
      setDraggedTile(tileId)
    }

    if (touchDragActiveRef.current) {
      // Find which tile we're over
      const elementsAtPoint = document.elementsFromPoint(touch.clientX, touch.clientY)
      let foundTileId: string | null = null

      for (const el of elementsAtPoint) {
        const tileEl = el.closest('[data-tile-id]') as HTMLElement
        if (tileEl && tileEl.dataset.tileId) {
          foundTileId = tileEl.dataset.tileId
          break
        }
      }

      if (foundTileId && foundTileId !== tileId) {
        setDragOverTile(foundTileId)
      } else {
        setDragOverTile(null)
      }
    }
  }, [isEditMode])

  const handleTileTouchEnd = useCallback((e: React.TouchEvent) => {
    const wasDragging = touchDragActiveRef.current
    const hadMovement = didDragRef.current

    if (wasDragging && draggedTile && dragOverTile) {
      // Perform the swap
      setTileOrder(prevOrder => {
        const newOrder = [...prevOrder]
        const sourceIndex = newOrder.indexOf(draggedTile)
        const targetIndex = newOrder.indexOf(dragOverTile)

        if (sourceIndex !== -1 && targetIndex !== -1) {
          newOrder.splice(sourceIndex, 1)
          newOrder.splice(targetIndex, 0, draggedTile)
          localStorage.setItem('tile_order', JSON.stringify(newOrder))
        }

        return newOrder
      })
    }

    touchStartRef.current = null
    touchDragActiveRef.current = false
    setDraggedTile(null)
    setDragOverTile(null)

    // Keep didDragRef true if there was any movement to block click
    // Don't reset immediately - let the onClick handler check it first
    if (!hadMovement) {
      didDragRef.current = false
    }
  }, [draggedTile, dragOverTile])

  // Конфигурация плиток
  const tilesConfig: Record<string, TileConfig> = {
    chat: {
      id: 'chat',
      href: '/chat',
      title: 'Чат с Tracy',
      description: 'Онлайн чат с AI-ассистентом для планирования дня',
      icon: <MessageCircle className="h-7 w-7 text-white" />,
      gradient: 'from-primary to-purple-600',
      gradientLine: 'from-primary via-purple-500 to-pink-500',
      hoverColor: 'text-primary',
    },
    calendar: {
      id: 'calendar',
      href: '/calendar',
      title: 'Календарь',
      description: 'Просмотр и управление событиями',
      icon: <Calendar className="h-7 w-7 text-white" />,
      gradient: 'from-blue-500 to-cyan-500',
      gradientLine: 'from-blue-500 via-cyan-500 to-teal-500',
      hoverColor: 'text-blue-500',
    },
    history: {
      id: 'history',
      href: '/meetings/history',
      title: 'История расшифровок',
      description: 'Просмотр всех расшифрованных встреч',
      icon: <History className="h-7 w-7 text-white" />,
      gradient: 'from-orange-500 to-red-500',
      gradientLine: 'from-orange-500 via-red-500 to-pink-500',
      hoverColor: 'text-orange-500',
    },
    todos: {
      id: 'todos',
      href: '/todo-lists',
      title: 'Списки задач',
      description: 'Создание и управление списками задач',
      icon: <ListTodo className="h-7 w-7 text-white" />,
      gradient: 'from-green-500 to-teal-500',
      gradientLine: 'from-green-500 via-emerald-500 to-teal-500',
      hoverColor: 'text-green-500',
    },
    feedback: {
      id: 'feedback',
      href: '/settings/feedback',
      title: 'Обратная связь',
      description: 'Просмотр всех сообщений об ошибках и предложениях',
      icon: <MessageSquare className="h-7 w-7 text-white" />,
      gradient: 'from-indigo-500 to-purple-500',
      gradientLine: 'from-indigo-500 via-purple-500 to-pink-500',
      hoverColor: 'text-indigo-500',
      superUserOnly: true,
    },
    debug: {
      id: 'debug',
      href: '/debug',
      title: 'Debug: Network',
      description: 'Мониторинг сетевых запросов и диагностика ошибок',
      icon: <Bug className="h-7 w-7 text-white" />,
      gradient: 'from-slate-500 to-gray-600',
      gradientLine: 'from-slate-500 via-gray-500 to-zinc-500',
      hoverColor: 'text-slate-500',
      superUserOnly: true,
    },
  }

  // Рендер одной плитки
  const renderTile = (tileId: string) => {
    const tile = tilesConfig[tileId]
    if (!tile) return null

    // Skip superUser-only tiles for regular users
    if (tile.superUserOnly && !isSuperUser) return null

    const isDragging = draggedTile === tileId
    const isDragOver = dragOverTile === tileId

    return (
      <div
        key={tile.id}
        data-tile-id={tile.id}
        draggable={isEditMode}
        onDragStart={isEditMode ? (e) => handleDragStart(e, tile.id) : undefined}
        onDragEnd={isEditMode ? handleDragEnd : undefined}
        onDragOver={isEditMode ? (e) => handleDragOver(e, tile.id) : undefined}
        onDragLeave={isEditMode ? handleDragLeave : undefined}
        onDrop={isEditMode ? (e) => handleDrop(e, tile.id) : undefined}
        onTouchStart={isEditMode ? (e) => handleTileTouchStart(e, tile.id) : undefined}
        onTouchMove={isEditMode ? (e) => handleTileTouchMove(e, tile.id) : undefined}
        onTouchEnd={isEditMode ? (e) => handleTileTouchEnd(e) : undefined}
        style={isEditMode ? { touchAction: 'none' } : undefined}
        className={`relative ${isDragOver ? 'scale-105' : ''} ${isDragging ? 'opacity-50' : ''} transition-all duration-200 ${isEditMode ? 'cursor-grab active:cursor-grabbing' : ''}`}
      >
        <Link
          href={tile.href}
          className={`block group ${isEditMode ? 'pointer-events-none' : ''}`}
          onClick={(e) => {
            // In edit mode, prevent navigation
            if (isEditMode) {
              e.preventDefault()
              e.stopPropagation()
              return
            }
            // Prevent navigation if there was any touch movement
            if (didDragRef.current) {
              e.preventDefault()
              e.stopPropagation()
              // Reset after blocking the click
              didDragRef.current = false
              return
            }
            logger.info('AssistantPage', `Card clicked: ${tile.href}`)
            if (debugMode) {
              lastNavAttemptRef.current = tile.href
            }
          }}
        >
          <div className={`relative overflow-hidden rounded-3xl border-0 bg-card shadow-lg hover:shadow-2xl transition-all duration-300 hover:-translate-y-1 ${isDragOver ? 'ring-2 ring-primary ring-offset-2' : ''}`}>
            {/* Gradient line on top */}
            <div className={`h-1 bg-gradient-to-r ${tile.gradientLine}`} />

            <div className="p-6">
              <div className="flex items-center gap-4">
                {/* Icon with gradient and glow */}
                <div className="relative">
                  <div className={`absolute inset-0 bg-gradient-to-br ${tile.gradient} rounded-2xl blur-lg opacity-50 group-hover:opacity-75 transition-opacity`} />
                  <div className={`relative h-14 w-14 rounded-2xl bg-gradient-to-br ${tile.gradient} flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform duration-300`}>
                    {tile.icon}
                  </div>
                </div>

                <div className="flex-1">
                  <h3 className={`text-xl font-bold mb-1 group-hover:${tile.hoverColor} transition-colors`}>
                    {tile.title}
                  </h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    {tile.description}
                  </p>
                </div>

                {/* Arrow or Edit mode indicator */}
                {isEditMode ? (
                  <div className="text-muted-foreground">
                    <ArrowDownUp className="h-5 w-5" />
                  </div>
                ) : (
                  <div className={`text-muted-foreground group-hover:${tile.hoverColor} group-hover:translate-x-1 transition-all`}>
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </div>
                )}
              </div>
            </div>
          </div>
        </Link>
      </div>
    )
  }

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
          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsEditMode(!isEditMode)}
              aria-label={isEditMode ? "Готово" : "Изменить порядок"}
              className={`text-foreground transition-colors p-2 rounded-lg ${
                isEditMode
                  ? 'bg-primary text-primary-foreground hover:bg-primary/90'
                  : 'hover:text-muted-foreground hover:bg-muted'
              }`}
            >
              {isEditMode ? (
                <Check className="h-5 w-5" />
              ) : (
                <ArrowDownUp className="h-5 w-5" />
              )}
            </button>
            <Link
              href="/settings"
              aria-label="Settings"
              className="text-foreground hover:text-muted-foreground transition-colors p-2 rounded-lg hover:bg-muted"
            >
              <Settings className="h-5 w-5" />
            </Link>
          </div>
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
            <Link href="/settings/account" className="block">
              <Card variant="gradient" className="mb-6 border-0 overflow-hidden relative cursor-pointer hover:shadow-xl transition-shadow">
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
            </Link>
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

          {/* Main Features - Draggable Tiles */}
          <div className="space-y-4">
            {/* Hint about drag-and-drop */}
            <p className="text-xs text-muted-foreground text-center mb-2">
              Перетащите плитки для изменения порядка
            </p>
            
            {/* Render tiles in user-defined order */}
            {tileOrder.map(tileId => renderTile(tileId))}
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

