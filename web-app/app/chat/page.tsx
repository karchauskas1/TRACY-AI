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

interface ChatMessage {
  id: number
  role: "user" | "assistant"
  content: string
  created_at: string
}

export default function ChatPage() {
  const router = useRouter()
  const { user, userId, isLoading: userLoading, error: userError } = useTelegramUser()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputMessage, setInputMessage] = useState("")
  const [loading, setLoading] = useState(true)
  const [sending, setSending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [errorDetails, setErrorDetails] = useState<ErrorDetails | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const [greetingLoaded, setGreetingLoaded] = useState(false)

  useEffect(() => {
    // Загружаем чат только после получения user_id
    if (!userLoading && userId) {
      loadChat()
    } else if (!userLoading && !userId) {
      // Если user_id не получен, показываем ошибку
      if (userError) {
        setError(userError)
      } else {
        setError("Не удалось определить ID пользователя. Откройте приложение через Telegram.")
      }
      setLoading(false)
    }
  }, [userId, userLoading, userError])

  useEffect(() => {
    // Прокрутка к последнему сообщению
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

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

    const userMessage: ChatMessage = {
      id: Date.now(),
      role: "user",
      content: inputMessage.trim(),
      created_at: new Date().toISOString(),
    }

    // Добавляем сообщение пользователя сразу
    setMessages((prev) => [...prev, userMessage])
    const messageText = inputMessage.trim()
    setInputMessage("")
    setSending(true)
    setError(null)
    setErrorDetails(null)

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
        const assistantMessage: ChatMessage = {
          id: Date.now() + 1,
          role: "assistant",
          content: result.message,
          created_at: new Date().toISOString(),
        }
        setMessages((prev) => [...prev, assistantMessage])
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
    } finally {
      setSending(false)
    }
  }

  const handleBack = () => {
    router.push("/assistant")
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
      <div className="flex-1 overflow-y-auto px-4 py-6">
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
                  <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                    <Bot className="h-4 w-4 text-primary" />
                  </div>
                )}
                <div
                  className={`max-w-[80%] rounded-lg p-4 ${
                    message.role === "user"
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted"
                  }`}
                >
                  <p className="whitespace-pre-wrap text-sm">{message.content}</p>
                  <p className={`text-xs mt-2 ${
                    message.role === "user" ? "text-primary-foreground/70" : "text-muted-foreground"
                  }`}>
                    {formatTime(message.created_at)}
                  </p>
                </div>
                {message.role === "user" && (
                  <div className="h-8 w-8 rounded-full bg-muted flex items-center justify-center flex-shrink-0">
                    <User className="h-4 w-4 text-muted-foreground" />
                  </div>
                )}
              </div>
            ))}
            {sending && (
              <div className="flex gap-3 justify-start">
                <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                  <Bot className="h-4 w-4 text-primary" />
                </div>
                <div className="bg-muted rounded-lg p-4">
                  <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input */}
      <div className="sticky bottom-0 border-t border-border bg-background p-4">
        <div className="max-w-2xl mx-auto">
          {error && (
            <p className="text-sm text-destructive mb-2">{error}</p>
          )}
          <div className="flex gap-2">
            <Textarea
              placeholder="Напишите сообщение..."
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey && !sending) {
                  e.preventDefault()
                  sendMessage()
                }
              }}
              className="flex-1 min-h-[60px] max-h-[120px] resize-none"
              disabled={sending}
            />
            <Button
              onClick={sendMessage}
              disabled={!inputMessage.trim() || sending}
              size="icon"
              className="h-[60px] w-[60px]"
            >
              {sending ? (
                <Loader2 className="h-5 w-5 animate-spin" />
              ) : (
                <Send className="h-5 w-5" />
              )}
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}

