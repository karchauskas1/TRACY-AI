"use client"

import { useEffect, useState, useRef } from "react"
import { useRouter } from "next/navigation"
import { ArrowLeft, Send, Loader2, Bot, User } from "lucide-react"
import { Card, CardContent } from "../../components/ui/card"
import { Button } from "../../components/ui/button"
import { Textarea } from "../../components/ui/textarea"

interface ChatMessage {
  id: number
  role: "user" | "assistant"
  content: string
  created_at: string
}

export default function ChatPage() {
  const router = useRouter()
  const [user, setUser] = useState<any>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputMessage, setInputMessage] = useState("")
  const [loading, setLoading] = useState(true)
  const [sending, setSending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const [greetingLoaded, setGreetingLoaded] = useState(false)

  useEffect(() => {
    // Загружаем данные пользователя
    if (typeof window !== "undefined") {
      const tg = (window as any).Telegram?.WebApp
      if (tg) {
        tg.ready()
        const tgUser = tg.initDataUnsafe?.user
        if (tgUser) {
          setUser({
            id: tgUser.id.toString(),
            first_name: tgUser.first_name,
            last_name: tgUser.last_name,
          })
        }
      } else {
        const savedUser = localStorage.getItem("telegram_user")
        if (savedUser) {
          try {
            const parsed = JSON.parse(savedUser)
            setUser({
              id: parsed.id?.toString(),
              first_name: parsed.first_name,
              last_name: parsed.last_name,
            })
          } catch (e) {
            console.error("Failed to parse user:", e)
          }
        }
      }
    }
  }, [])

  useEffect(() => {
    if (user?.id) {
      loadChat()
    }
  }, [user])

  useEffect(() => {
    // Прокрутка к последнему сообщению
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  const loadChat = async () => {
    if (!user?.id) return

    try {
      setLoading(true)
      setError(null)

      const apiBaseUrl = typeof window !== "undefined" && window.location.hostname === "localhost"
        ? "http://localhost:8080"
        : "http://5.35.126.42:8080"

      // Загружаем историю сообщений
      const messagesResponse = await fetch(`${apiBaseUrl}/api/chat/messages?user_id=${user.id}&limit=50`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
        mode: "cors",
      })

      console.log(`[Chat] Messages API Response: status=${messagesResponse.status}, ok=${messagesResponse.ok}`)
      
      if (messagesResponse.ok) {
        const messagesData = await messagesResponse.json()
        console.log(`[Chat] Messages API Data:`, messagesData)
        setMessages(messagesData.messages || [])
        
        // Если истории нет, загружаем приветственное сообщение
        if (!messagesData.messages || messagesData.messages.length === 0) {
          await loadGreeting()
        }
      } else {
        const errorText = await messagesResponse.text()
        console.error(`[Chat] Messages API Error: ${messagesResponse.status} ${messagesResponse.statusText}`, errorText)
        if (messagesResponse.status === 404) {
          setError("API endpoint не найден. Сервер не обновлен.")
        }
        // Если ошибка загрузки истории, пробуем загрузить приветствие
        await loadGreeting()
      }
    } catch (e: any) {
      console.error("Ошибка загрузки чата:", e)
      
      // Проверяем, является ли это ошибкой Mixed Content Policy
      if (e instanceof TypeError && e.message.includes("Failed to fetch")) {
        if (typeof window !== "undefined" && window.location.protocol === "https:") {
          setError("Не удалось подключиться к серверу. Откройте приложение через Telegram для доступа к чату.")
        } else {
          setError("Не удалось подключиться к серверу. Проверьте подключение к интернету.")
        }
      } else {
        setError(e.message || "Не удалось загрузить чат")
      }
      // Пробуем загрузить приветствие даже при ошибке
      await loadGreeting()
    } finally {
      setLoading(false)
    }
  }

  const loadGreeting = async () => {
    if (!user?.id || greetingLoaded) return

    try {
      setGreetingLoaded(true)
      const apiBaseUrl = typeof window !== "undefined" && window.location.hostname === "localhost"
        ? "http://localhost:8080"
        : "http://5.35.126.42:8080"

      const response = await fetch(`${apiBaseUrl}/api/chat/greeting?user_id=${user.id}`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
        mode: "cors",
      })

      console.log(`[Chat] Greeting API Response: status=${response.status}, ok=${response.ok}`)
      
      if (response.ok) {
        const data = await response.json()
        console.log(`[Chat] Greeting API Data:`, data)
        if (data.greeting) {
          // Добавляем приветственное сообщение в список
          const greetingMsg: ChatMessage = {
            id: Date.now(),
            role: "assistant",
            content: data.greeting,
            created_at: new Date().toISOString(),
          }
          setMessages([greetingMsg])
        }
      } else {
        const errorText = await response.text()
        console.error(`[Chat] Greeting API Error: ${response.status} ${response.statusText}`, errorText)
        if (response.status === 404) {
          setError("API endpoint не найден. Сервер не обновлен.")
        }
      }
    } catch (e: any) {
      console.error("Ошибка загрузки приветствия:", e)
      
      // Проверяем, является ли это ошибкой Mixed Content Policy
      if (e instanceof TypeError && e.message.includes("Failed to fetch")) {
        if (typeof window !== "undefined" && window.location.protocol === "https:") {
          setError("Не удалось подключиться к серверу. Откройте приложение через Telegram для доступа к чату.")
        }
      }
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
    if (!user?.id || !inputMessage.trim() || sending) return

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

    try {
      const apiBaseUrl = typeof window !== "undefined" && window.location.hostname === "localhost"
        ? "http://localhost:8080"
        : "http://5.35.126.42:8080"

      const response = await fetch(`${apiBaseUrl}/api/chat/send`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        mode: "cors",
        body: JSON.stringify({
          user_id: parseInt(user.id),
          message: messageText,
        }),
      })

      if (!response.ok) {
        throw new Error("Ошибка отправки сообщения")
      }

      const data = await response.json()
      
      if (data.message) {
        const assistantMessage: ChatMessage = {
          id: Date.now() + 1,
          role: "assistant",
          content: data.message,
          created_at: new Date().toISOString(),
        }
        setMessages((prev) => [...prev, assistantMessage])
      }
    } catch (e: any) {
      console.error("Ошибка отправки сообщения:", e)
      setError(e.message || "Не удалось отправить сообщение")
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

