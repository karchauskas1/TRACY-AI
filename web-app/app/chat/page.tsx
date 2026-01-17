"use client"

import { useEffect, useState, useRef } from "react"
import { useRouter } from "next/navigation"
import { ArrowLeft, Send, Loader2, Bot, User } from "lucide-react"
import { Card, CardContent } from "../../components/ui/card"
import { Button } from "../../components/ui/button"
import { Textarea } from "../../components/ui/textarea"
import { getErrorDetails, formatErrorForDisplay, type ErrorDetails } from "../../lib/error-utils"
import { apiGet, apiPost, formatApiError, type ApiError } from "../../lib/apiClient"
import { useTelegramUser } from "../../lib/useTelegramUser"
import { useNavigation } from "../../lib/useNavigation"

interface ChatMessage {
  id: number
  role: "user" | "assistant"
  content: string
  created_at: string
  clientId?: string
  pending?: boolean
}

export default function ChatPage() {
  const router = useRouter()
  const { user, userId, isLoading: userLoading, error: userError } = useTelegramUser()
  const { handleBack } = useNavigation()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputMessage, setInputMessage] = useState("")
  const [loading, setLoading] = useState(true)
  const [sending, setSending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [errorDetails, setErrorDetails] = useState<ErrorDetails | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const [keyboardInset, setKeyboardInset] = useState(0)
  const [greetingLoaded, setGreetingLoaded] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const messagesContainerRef = useRef<HTMLDivElement>(null)
  const [isNearBottom, setIsNearBottom] = useState(true)
  const touchStartRef = useRef<{ x: number; y: number; t: number } | null>(null)
  const msgTouchRef = useRef<{ y: number; scrollTop: number } | null>(null)
  const suppressAutoScrollUntilRef = useRef(0)
  const lastMsgTouchYRef = useRef<number | null>(null)
  
  // 🔴 iOS KEYBOARD FIX: refs для предотвращения дёрганья
  const sendingRef = useRef(false) // Отслеживаем sending в ref для использования в callback
  const lastKeyboardInsetRef = useRef(0) // Последнее значение keyboardInset
  const keyboardInsetTimeoutRef = useRef<NodeJS.Timeout | null>(null) // Debounce timeout
  const keyboardLockedUntilRef = useRef(0) // Блокировка обновления keyboardInset до этого времени

  useEffect(() => {
    // Если пользователь не авторизован, перенаправляем на логин
    if (!userLoading && !userId) {
      router.push("/login")
      return
    }

    // Загружаем чат только после получения user_id
    if (!userLoading && userId) {
      loadChat()
    }
  }, [userId, userLoading, router])

  const scrollToBottom = (behavior: ScrollBehavior = "smooth") => {
    if (Date.now() < suppressAutoScrollUntilRef.current) return
    messagesEndRef.current?.scrollIntoView({ behavior })
  }

  // Keep input above the on-screen keyboard (iOS/Telegram WebView)
  // 🔴 iOS KEYBOARD FIX: Debounce + блокировка при отправке
  useEffect(() => {
    if (typeof window === "undefined") return
    const vv = (window as any).visualViewport as VisualViewport | undefined
    if (!vv) return

    const computeInset = () => {
      // 🔴 Блокируем обновление если идёт отправка сообщения
      if (sendingRef.current) return
      
      // 🔴 Блокируем обновление если ещё не прошло время после отправки
      if (Date.now() < keyboardLockedUntilRef.current) return
      
      const rawInset = Math.max(0, window.innerHeight - (vv.height + vv.offsetTop))
      const inset = Math.round(rawInset)
      
      // 🔴 Игнорируем мелкие колебания (< 10px) для предотвращения jitter
      const diff = Math.abs(inset - lastKeyboardInsetRef.current)
      if (diff > 0 && diff < 10) return
      
      // 🔴 Debounce: откладываем обновление на 50ms, отменяем если пришло новое
      if (keyboardInsetTimeoutRef.current) {
        clearTimeout(keyboardInsetTimeoutRef.current)
      }
      
      keyboardInsetTimeoutRef.current = setTimeout(() => {
        // Повторная проверка перед применением
        if (sendingRef.current || Date.now() < keyboardLockedUntilRef.current) return
        
        lastKeyboardInsetRef.current = inset
        setKeyboardInset(inset)
      }, 50)
    }

    computeInset()
    vv.addEventListener("resize", computeInset)
    vv.addEventListener("scroll", computeInset)
    return () => {
      vv.removeEventListener("resize", computeInset)
      vv.removeEventListener("scroll", computeInset)
      if (keyboardInsetTimeoutRef.current) {
        clearTimeout(keyboardInsetTimeoutRef.current)
      }
    }
  }, [])

  // iOS Telegram WebView: prevent top overscroll bounce while keyboard is open
  useEffect(() => {
    const el = messagesContainerRef.current
    if (!el) return
    // Only matters on touch devices
    if (typeof window === "undefined") return

    const onTouchStart = (e: TouchEvent) => {
      if (e.touches.length !== 1) return
      lastMsgTouchYRef.current = e.touches[0].clientY
    }

    const onTouchMove = (e: TouchEvent) => {
      if (keyboardInset <= 0) return
      if (e.touches.length !== 1) return
      const lastY = lastMsgTouchYRef.current
      if (lastY == null) return
      const y = e.touches[0].clientY
      const dy = y - lastY
      lastMsgTouchYRef.current = y

      // At top and pulling down -> prevent default to avoid bounce + snap-to-bottom
      if (el.scrollTop <= 0 && dy > 0) {
        suppressAutoScrollUntilRef.current = Date.now() + 1200
        if (isNearBottom) setIsNearBottom(false)
        e.preventDefault()
      }
    }

    const onTouchEnd = () => {
      lastMsgTouchYRef.current = null
    }

    el.addEventListener("touchstart", onTouchStart, { passive: true })
    el.addEventListener("touchmove", onTouchMove, { passive: false })
    el.addEventListener("touchend", onTouchEnd, { passive: true })
    el.addEventListener("touchcancel", onTouchEnd, { passive: true })
    return () => {
      el.removeEventListener("touchstart", onTouchStart)
      el.removeEventListener("touchmove", onTouchMove)
      el.removeEventListener("touchend", onTouchEnd)
      el.removeEventListener("touchcancel", onTouchEnd)
    }
  }, [keyboardInset, isNearBottom])

  useEffect(() => {
    if (keyboardInset <= 0) return
    // When keyboard opens, keep latest message visible only if user is already near bottom
    if (!isNearBottom) return
    requestAnimationFrame(() => scrollToBottom("smooth"))
  }, [keyboardInset, isNearBottom])

  useEffect(() => {
    // Auto-scroll only when user is pinned to bottom
    if (!isNearBottom) return
    requestAnimationFrame(() => scrollToBottom("smooth"))
  }, [messages.length, isNearBottom])

  const loadChat = async () => {
    // Ждем, пока user_id будет получен
    if (userLoading) {
      console.log("[Chat] Ожидание user_id...")
      return
    }
    
    if (!userId || userId === "demo" || userId === "undefined" || userId === "null") {
      console.error("[Chat] ❌ User ID не найден или невалиден:", userId)
      const errorMessage = userId === "demo" 
        ? "Демо-режим не поддерживает чат. Откройте приложение через Telegram."
        : "Не удалось определить ID пользователя. Откройте приложение через Telegram."
      setError(errorMessage)
      setLoading(false)
      return
    }

    try {
      setLoading(true)
      setError(null)
      setErrorDetails(null)

      // Загружаем историю сообщений через единый API клиент
      const messagesData = await apiGet<{ success?: boolean; messages?: ChatMessage[]; error?: string }>(
        `/api/chat/messages`,
        { user_id: parseInt(userId), limit: 50 },
        { timeout: 15000 }
      )
      
      if (messagesData.success && Array.isArray(messagesData.messages)) {
        setMessages(messagesData.messages)
      } else if (Array.isArray(messagesData.messages)) {
        setMessages(messagesData.messages)
      } else if (messagesData.error) {
        throw new Error(messagesData.error)
      } else {
        setMessages([])
      }
      
      setError(null)
      setErrorDetails(null)
      
      // Если истории нет, загружаем приветственное сообщение
      if (!messagesData.messages || messagesData.messages.length === 0) {
        await loadGreeting(userId)
      }
      
      setLoading(false)
    } catch (e: any) {
      console.error("Ошибка загрузки чата:", e)
      
      const errorMessage = e.type 
        ? formatApiError(e)
        : (e.message || "Не удалось загрузить чат")
      
      setError(errorMessage)
      setErrorDetails({
        code: String(e.status || e.type || "UNKNOWN"),
        message: e.message || errorMessage,
        context: "Загрузка чата",
      })
      
      // Пробуем загрузить приветствие даже при ошибке
      if (userId && userId !== "demo" && userId !== "undefined" && userId !== "null") {
        await loadGreeting(userId)
      }
      setLoading(false)
    }
  }

  const loadGreeting = async (currentUserId?: string | null) => {
    if (greetingLoaded) return

    const userIdToUse = currentUserId || userId
    if (!userIdToUse || userIdToUse === "demo" || userIdToUse === "undefined" || userIdToUse === "null") {
      console.error("[Chat] ❌ User ID не найден для приветствия:", userIdToUse)
      return
    }

    try {
      setGreetingLoaded(true)
      
      const result = await apiGet<{ success?: boolean; greeting?: string; error?: string }>(
        `/api/chat/greeting`,
        { user_id: parseInt(userIdToUse) },
        { timeout: 15000 }
      )
      
      if (result.success && result.greeting) {
        const greetingMsg: ChatMessage = {
          id: Date.now(),
          role: "assistant",
          content: result.greeting,
          created_at: new Date().toISOString(),
        }
        setMessages((prev) => prev.length === 0 ? [greetingMsg] : prev)
      } else if (result.error) {
        console.error(`[Chat] Greeting API Error:`, result.error)
      }
    } catch (e: any) {
      console.error("Ошибка загрузки приветствия:", e)
      // Если не удалось загрузить приветствие, добавляем базовое
      const fallbackGreeting: ChatMessage = {
        id: Date.now(),
        role: "assistant",
        content: "Привет! 👋\n\nЯ TRACY, твой AI-ассистент для планирования. Чем могу помочь?",
        created_at: new Date().toISOString(),
      }
      setMessages([fallbackGreeting])
    }
  }

  const sendMessage = async () => {
    if (!inputMessage.trim() || sending || !userId) return

    const clientId = `${Date.now()}-${Math.random().toString(16).slice(2)}`
    const messageText = inputMessage.trim()
    
    const userMessage: ChatMessage = {
      id: Date.now(),
      role: "user",
      content: messageText,
      created_at: new Date().toISOString(),
      clientId,
    }

    const pendingAssistant: ChatMessage = {
      id: Date.now() + 1,
      role: "assistant",
      content: "",
      created_at: new Date().toISOString(),
      clientId,
      pending: true,
    }

    // 🔴 iOS KEYBOARD FIX: Блокируем обновление keyboardInset во время отправки
    sendingRef.current = true
    // Блокируем обновления на время отправки + 500ms после
    keyboardLockedUntilRef.current = Date.now() + 30000 // Будет обновлено в finally
    
    setSending(true)
    setError(null)
    setErrorDetails(null)
    
    // Добавляем сообщение пользователя и placeholder ответа ассистента
    // Используем requestAnimationFrame для батчинга state updates
    requestAnimationFrame(() => {
      setMessages((prev) => [...prev, userMessage, pendingAssistant])
    })

    try {
      const result = await apiPost<{ success?: boolean; message?: string; error?: string }>(
        `/api/chat/send`,
        {
          user_id: parseInt(userId),
          message: messageText,
        },
        { timeout: 30000 }
      )

      if (result.success && result.message) {
        // Replace placeholder for this send (if present)
        setMessages((prev) => {
          const idx = prev.findIndex((m) => m.role === "assistant" && m.clientId === clientId && m.pending)
          if (idx === -1) {
            return [
              ...prev,
              {
                id: Date.now() + 2,
                role: "assistant",
                content: result.message as string,
                created_at: new Date().toISOString(),
                clientId,
              },
            ]
          }
          const next = [...prev]
          next[idx] = {
            ...next[idx],
            content: result.message as string,
            pending: false,
          }
          return next
        })
        setError(null)
        setErrorDetails(null)
      } else if (result.error) {
        throw new Error(result.error)
      }
    } catch (e: any) {
      console.error("Ошибка отправки сообщения:", e)
      const errorMessage = e.type 
        ? formatApiError(e)
        : (e.message || "Не удалось отправить сообщение")
      setError(errorMessage)
      setErrorDetails({
        code: String(e.status || e.type || "UNKNOWN"),
        message: e.message || errorMessage,
        context: "Отправка сообщения",
      })
      // Mark placeholder as failed
      setMessages((prev) =>
        prev.map((m) =>
          m.role === "assistant" && m.clientId === clientId && m.pending
            ? { ...m, content: `❌ ${errorMessage}`, pending: false }
            : m
        )
      )
    } finally {
      // 🔴 iOS KEYBOARD FIX: Разблокируем keyboard updates через 500ms после отправки
      // Это даёт время iOS стабилизировать viewport
      sendingRef.current = false
      keyboardLockedUntilRef.current = Date.now() + 500
      
      setSending(false)
      
      // Очищаем input через двойной RAF для максимальной стабильности на iOS
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          setInputMessage("")
          // If user didn't scroll away, keep bottom pinned
          if (isNearBottom) scrollToBottom("smooth")
        })
      })
    }
  }


  const formatTime = (dateStr: string) => {
    try {
      const date = new Date(dateStr)
      return date.toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" })
    } catch {
      return ""
    }
  }

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      {/* Header */}
      <header className="sticky top-0 z-20 border-b border-border bg-background/95 backdrop-blur">
        <div className="flex h-14 items-center justify-between px-4">
          <button
            onClick={handleBack}
            className="text-foreground hover:text-muted-foreground transition-colors"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div className="flex items-center gap-2">
            <Bot className="h-5 w-5 text-primary" />
            <span className="text-sm font-medium">Чат с Tracy</span>
          </div>
          <div className="w-5" /> {/* Spacer */}
        </div>
      </header>

      {/* Messages */}
      <div
        ref={messagesContainerRef}
        className="flex-1 overflow-y-auto px-4 py-6"
        style={{
          // Extra space for fixed input + keyboard
          paddingBottom: 120 + keyboardInset,
        }}
        onScroll={() => {
          const el = messagesContainerRef.current
          if (!el) return
          const distance = el.scrollHeight - (el.scrollTop + el.clientHeight)
          // tighter threshold reduces accidental “pinned” state on iOS
          setIsNearBottom(distance < 60)
        }}
        onTouchStart={(e) => {
          if (e.touches.length !== 1) return
          const el = messagesContainerRef.current
          msgTouchRef.current = {
            y: e.touches[0].clientY,
            scrollTop: el ? el.scrollTop : 0,
          }
        }}
        onTouchMove={(e) => {
          const el = messagesContainerRef.current
          const start = msgTouchRef.current
          if (!el || !start || e.touches.length !== 1) return
          const dy = e.touches[0].clientY - start.y

          // iOS Telegram WebView: when keyboard is open and user reaches top then pulls down,
          // visualViewport can “jitter” and trigger our auto-scroll. Suppress it during this gesture.
          if (keyboardInset > 0 && el.scrollTop <= 0 && dy > 8) {
            suppressAutoScrollUntilRef.current = Date.now() + 800
            if (isNearBottom) setIsNearBottom(false)
          }
        }}
        onTouchEnd={() => {
          msgTouchRef.current = null
          // keep suppression a bit longer to survive iOS bounce animation
          if (keyboardInset > 0) suppressAutoScrollUntilRef.current = Math.max(suppressAutoScrollUntilRef.current, Date.now() + 300)
        }}
      >
          {loading ? (
              <div className="flex items-center justify-center h-full">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                <span className="ml-2 text-sm text-muted-foreground">Загрузка...</span>
              </div>
            ) : error ? (
              <div className="flex items-center justify-center h-full">
                <Card className="border-destructive">
                  <CardContent className="pt-6">
                    <div className="text-center space-y-4">
                      <p className="text-destructive font-semibold">Ошибка загрузки</p>
                      <p className="text-sm text-muted-foreground">{error}</p>
                      <Button onClick={loadChat} variant="outline">
                        Попробовать снова
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </div>
            ) : messages.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <Card className="border-border">
              <CardContent className="pt-6">
                <p className="text-muted-foreground text-center">Начните диалог с Tracy</p>
              </CardContent>
            </Card>
          </div>
        ) : (
          <div className="space-y-4 max-w-2xl mx-auto">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex gap-3 ${
                  message.role === "user" ? "justify-end" : "justify-start"
                }`}
              >
                {message.role === "assistant" && (
                  <div className="h-10 w-10 rounded-full bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center flex-shrink-0 shadow-lg">
                    <Bot className="h-5 w-5 text-white" />
                  </div>
                )}

                {/* User message - Gradient with glow */}
                {message.role === "user" ? (
                  <div className="relative max-w-[85%] group">
                    <div className="absolute inset-0 bg-gradient-to-br from-primary to-purple-600 rounded-[20px] blur-md opacity-50 group-hover:opacity-70 transition-opacity" />
                    <div className="relative bg-gradient-to-br from-primary to-purple-600 text-white rounded-[20px_20px_4px_20px] p-4 shadow-lg">
                      <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
                      <p className="text-xs mt-2 text-white/70">
                        {formatTime(message.created_at)}
                      </p>
                    </div>
                  </div>
                ) : (
                  /* Assistant message - Frosted glass */
                  <div className="relative max-w-[85%]">
                    <div
                      className="bg-[var(--glass-bg)] backdrop-blur-[30px] border border-[var(--glass-border)] rounded-[20px_20px_20px_4px] p-4 shadow-[0_8px_24px_rgba(31,38,135,0.15)]"
                      style={{
                        backdropFilter: 'blur(30px) saturate(200%)',
                        WebkitBackdropFilter: 'blur(30px) saturate(200%)'
                      }}
                    >
                      {message.pending ? (
                        <div className="flex items-center gap-2 py-1">
                          <span className="h-2.5 w-2.5 rounded-full bg-primary animate-bounce" style={{ animationDelay: "0ms" }} />
                          <span className="h-2.5 w-2.5 rounded-full bg-primary animate-bounce" style={{ animationDelay: "150ms" }} />
                          <span className="h-2.5 w-2.5 rounded-full bg-primary animate-bounce" style={{ animationDelay: "300ms" }} />
                        </div>
                      ) : (
                        <>
                          <p className="text-sm leading-relaxed whitespace-pre-wrap text-foreground">{message.content}</p>
                          <p className="text-xs mt-2 text-muted-foreground">
                            {formatTime(message.created_at)}
                          </p>
                        </>
                      )}
                    </div>
                  </div>
                )}

                {message.role === "user" && (
                  <div className="h-10 w-10 rounded-full bg-gradient-to-br from-muted to-muted/80 flex items-center justify-center flex-shrink-0 shadow-md">
                    <User className="h-5 w-5 text-muted-foreground" />
                  </div>
                )}
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input */}
      <div
        className="fixed left-0 right-0 border-t border-border bg-background p-4"
        style={{ 
          // 🔴 iOS KEYBOARD FIX: Используем transform вместо bottom для GPU-ускорения
          // transform более производительный чем изменение bottom
          bottom: 0,
          transform: `translateY(-${keyboardInset}px)`,
          // Плавная анимация только когда не отправляем (sending блокирует)
          transition: sending ? 'none' : 'transform 0.15s ease-out',
          // GPU-ускорение
          willChange: 'transform',
          WebkitBackfaceVisibility: 'hidden',
          backfaceVisibility: 'hidden',
        }}
        onTouchStart={(e) => {
          if (e.touches.length !== 1) return
          touchStartRef.current = { x: e.touches[0].clientX, y: e.touches[0].clientY, t: Date.now() }
        }}
        onTouchEnd={(e) => {
          const start = touchStartRef.current
          touchStartRef.current = null
          if (!start) return
          const touch = e.changedTouches[0]
          const dx = touch.clientX - start.x
          const dy = touch.clientY - start.y
          const dt = Date.now() - start.t
          // Down swipe to dismiss keyboard (like messengers)
          const isFocused = typeof document !== "undefined" && document.activeElement === textareaRef.current
          if (keyboardInset > 0 && isFocused && dy > 40 && Math.abs(dx) < 24 && dt < 600) {
            textareaRef.current?.blur()
          }
        }}
      >
        <div className="max-w-2xl mx-auto">
          {error && (
            <p className="text-sm text-destructive mb-2">{error}</p>
          )}
          <div className="flex gap-3">
            <Textarea
              ref={textareaRef}
              placeholder="Напишите сообщение..."
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey && !sending) {
                  e.preventDefault()
                  sendMessage()
                }
              }}
              className="flex-1 min-h-[56px] max-h-[120px] resize-none text-base rounded-2xl border-2 focus:border-primary transition-all bg-card shadow-sm focus:shadow-[0_0_0_4px_rgba(102,126,234,0.1),0_0_20px_rgba(102,126,234,0.3),0_0_40px_rgba(102,126,234,0.15)] focus:ring-0 focus-visible:ring-0 focus-visible:ring-offset-0"
              disabled={sending}
            />
            <Button
              onClick={sendMessage}
              disabled={!inputMessage.trim() || sending}
              size="icon"
              className="h-[56px] w-[56px] rounded-2xl bg-gradient-to-br from-primary to-purple-600 shadow-lg hover:shadow-xl hover:scale-105 transition-all"
            >
              {sending ? (
                <Loader2 className="h-6 w-6 animate-spin" />
              ) : (
                <Send className="h-6 w-6" />
              )}
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}

