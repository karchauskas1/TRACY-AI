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
    // Получаем user_id из разных источников
    let userId: string | null = null
    // #region agent log
    fetch('http://127.0.0.1:7244/ingest/5297ce20-cdd6-4734-9a97-89b776b10890',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'ChatPage.tsx:71',message:'loadChat entry',data:{hasUser:!!user,userFromState:user?.id},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'F'})}).catch(()=>{});
    // #endregion
    if (user?.id) {
      userId = user.id.toString()
      // #region agent log
      fetch('http://127.0.0.1:7244/ingest/5297ce20-cdd6-4734-9a97-89b776b10890',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'ChatPage.tsx:76',message:'userId from state',data:{userId,source:'user.id'},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'F'})}).catch(()=>{});
      // #endregion
    } else if (typeof window !== "undefined") {
      const tg = (window as any).Telegram?.WebApp
      if (tg?.initDataUnsafe?.user?.id) {
        userId = tg.initDataUnsafe.user.id.toString()
        // #region agent log
        fetch('http://127.0.0.1:7244/ingest/5297ce20-cdd6-4734-9a97-89b776b10890',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'ChatPage.tsx:81',message:'userId from Telegram WebApp',data:{userId,source:'tg.initDataUnsafe.user.id',tgUserExists:!!tg.initDataUnsafe?.user},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'F'})}).catch(()=>{});
        // #endregion
        // Сохраняем user для будущего использования
        if (!user) {
          setUser({
            id: userId,
            first_name: tg.initDataUnsafe.user.first_name,
            last_name: tg.initDataUnsafe.user.last_name,
          })
        }
      } else {
        // Пробуем получить из localStorage
        const savedUser = localStorage.getItem("telegram_user")
        if (savedUser) {
          try {
            const parsed = JSON.parse(savedUser)
            userId = parsed.id?.toString() || null
            // #region agent log
            fetch('http://127.0.0.1:7244/ingest/5297ce20-cdd6-4734-9a97-89b776b10890',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'ChatPage.tsx:96',message:'userId from localStorage',data:{userId,source:'localStorage'},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'F'})}).catch(()=>{});
            // #endregion
          } catch (e) {
            console.error("[Chat] Error parsing saved user:", e)
            // #region agent log
            fetch('http://127.0.0.1:7244/ingest/5297ce20-cdd6-4734-9a97-89b776b10890',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'ChatPage.tsx:99',message:'Error parsing localStorage user',data:{error:String(e)},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'F'})}).catch(()=>{});
            // #endregion
          }
        } else {
          // #region agent log
          fetch('http://127.0.0.1:7244/ingest/5297ce20-cdd6-4734-9a97-89b776b10890',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'ChatPage.tsx:103',message:'No userId found',data:{userId:null,hasUser:!!user,hasTg:!!tg,hasSavedUser:false},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'F'})}).catch(()=>{});
          // #endregion
        }
      }
    }
    
    if (!userId || userId === "demo" || userId === "undefined" || userId === "null") {
      console.error("[Chat] ❌ User ID не найден или невалиден:", userId)
      // #region agent log
      fetch('http://127.0.0.1:7244/ingest/5297ce20-cdd6-4734-9a97-89b776b10890',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'ChatPage.tsx:107',message:'Invalid userId - returning early',data:{userId,isDemo:userId==='demo',isUndefined:userId==='undefined',isNull:userId==='null'},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'F'})}).catch(()=>{});
      // #endregion
      setError("Не удалось определить ID пользователя. Откройте приложение через Telegram.")
      setLoading(false)
      return
    }
    
    console.log(`[Chat] User ID: ${userId}`)
    // #region agent log
    fetch('http://127.0.0.1:7244/ingest/5297ce20-cdd6-4734-9a97-89b776b10890',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'ChatPage.tsx:113',message:'userId validated - proceeding to API call',data:{userId,isValid:true},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'F'})}).catch(()=>{});
    // #endregion

    try {
      setLoading(true)
      setError(null)

      const apiBaseUrl = typeof window !== "undefined" && window.location.hostname === "localhost"
        ? "http://localhost:8080"
        : "https://api.pasekaproduction.ru"

      // Загружаем историю сообщений
      const messagesApiUrl = `${apiBaseUrl}/api/chat/messages?user_id=${userId}&limit=50`
      // #region agent log
      fetch('http://127.0.0.1:7244/ingest/5297ce20-cdd6-4734-9a97-89b776b10890',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'ChatPage.tsx:121',message:'API request before fetch (messages)',data:{apiUrl:messagesApiUrl,userId,apiBaseUrl},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'F'})}).catch(()=>{});
      // #endregion
      const messagesResponse = await fetch(messagesApiUrl, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
        mode: "cors",
      })

      console.log(`[Chat] Messages API Response: status=${messagesResponse.status}, ok=${messagesResponse.ok}`)
      // #region agent log
      fetch('http://127.0.0.1:7244/ingest/5297ce20-cdd6-4734-9a97-89b776b10890',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'ChatPage.tsx:132',message:'Messages API response received',data:{status:messagesResponse.status,ok:messagesResponse.ok,statusText:messagesResponse.statusText},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'F'})}).catch(()=>{});
      // #endregion
      
      if (messagesResponse.ok) {
        let messagesData
        try {
          const responseText = await messagesResponse.text()
          console.log(`[Chat] Raw Messages Response:`, responseText)
          // #region agent log
          fetch('http://127.0.0.1:7244/ingest/5297ce20-cdd6-4734-9a97-89b776b10890',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'ChatPage.tsx:136',message:'Raw messages response received',data:{responseLength:responseText.length,responsePreview:responseText.substring(0,200)},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'E'})}).catch(()=>{});
          // #endregion
          messagesData = JSON.parse(responseText)
          // #region agent log
          fetch('http://127.0.0.1:7244/ingest/5297ce20-cdd6-4734-9a97-89b776b10890',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'ChatPage.tsx:139',message:'Messages JSON parsed successfully',data:{hasSuccess:!!messagesData.success,hasMessages:!!messagesData.messages,messagesIsArray:Array.isArray(messagesData.messages),messagesCount:Array.isArray(messagesData.messages)?messagesData.messages.length:0,dataKeys:Object.keys(messagesData)},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'E'})}).catch(()=>{});
          // #endregion
        } catch (e) {
          console.error(`[Chat] Ошибка парсинга JSON:`, e)
          // #region agent log
          fetch('http://127.0.0.1:7244/ingest/5297ce20-cdd6-4734-9a97-89b776b10890',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'ChatPage.tsx:142',message:'Messages JSON parse error',data:{error:String(e)},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'E'})}).catch(()=>{});
          // #endregion
          throw new Error("Неверный формат ответа от сервера")
        }
        
        console.log(`[Chat] Parsed Messages Data:`, messagesData)
        
        if (messagesData.success && Array.isArray(messagesData.messages)) {
          console.log(`[Chat] ✅ Успешно загружено ${messagesData.messages.length} сообщений`)
          // #region agent log
          fetch('http://127.0.0.1:7244/ingest/5297ce20-cdd6-4734-9a97-89b776b10890',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'ChatPage.tsx:150',message:'Messages extracted (format: success+messages)',data:{messagesCount:messagesData.messages.length},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'E'})}).catch(()=>{});
          // #endregion
          setMessages(messagesData.messages)
        } else if (Array.isArray(messagesData.messages)) {
          console.log(`[Chat] ✅ Загружено ${messagesData.messages.length} сообщений (без success поля)`)
          // #region agent log
          fetch('http://127.0.0.1:7244/ingest/5297ce20-cdd6-4734-9a97-89b776b10890',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'ChatPage.tsx:154',message:'Messages extracted (format: messages)',data:{messagesCount:messagesData.messages.length},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'E'})}).catch(()=>{});
          // #endregion
          setMessages(messagesData.messages)
        } else if (messagesData.error) {
          console.error(`[Chat] ❌ API вернул ошибку:`, messagesData.error)
          // #region agent log
          fetch('http://127.0.0.1:7244/ingest/5297ce20-cdd6-4734-9a97-89b776b10890',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'ChatPage.tsx:158',message:'API returned error in messagesData',data:{error:messagesData.error},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'E'})}).catch(()=>{});
          // #endregion
          throw new Error(messagesData.error || "Ошибка загрузки сообщений")
        } else {
          console.warn(`[Chat] ⚠️ Неожиданный формат данных:`, messagesData)
          // #region agent log
          fetch('http://127.0.0.1:7244/ingest/5297ce20-cdd6-4734-9a97-89b776b10890',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'ChatPage.tsx:162',message:'Unexpected messagesData format',data:{dataKeys:Object.keys(messagesData)},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'E'})}).catch(()=>{});
          // #endregion
          setMessages([])
        }
        
        // Если истории нет, загружаем приветственное сообщение
        if (!messagesData.messages || messagesData.messages.length === 0) {
          await loadGreeting()
        }
      } else {
        let errorText = ""
        try {
          errorText = await messagesResponse.text()
        } catch (e) {
          errorText = messagesResponse.statusText
        }
        console.error(`[Chat] Messages API Error: ${messagesResponse.status} ${messagesResponse.statusText}`, errorText)
        if (messagesResponse.status === 404) {
          setError("API endpoint не найден. Сервер не обновлен.")
        } else {
          setError(`Ошибка загрузки сообщений: ${messagesResponse.status}`)
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
      } else if (e.message && (e.message.includes("Invalid user_id") || e.message.includes("user_id required"))) {
        setError("Не удалось определить ID пользователя. Откройте приложение через Telegram.")
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
    if (greetingLoaded) return

    // Получаем user_id из разных источников
    let userId: string | null = null
    
    if (user?.id) {
      userId = user.id.toString()
    } else if (typeof window !== "undefined") {
      const tg = (window as any).Telegram?.WebApp
      if (tg?.initDataUnsafe?.user?.id) {
        userId = tg.initDataUnsafe.user.id.toString()
      } else {
        const savedUser = localStorage.getItem("telegram_user")
        if (savedUser) {
          try {
            const parsed = JSON.parse(savedUser)
            userId = parsed.id?.toString() || null
          } catch (e) {
            console.error("[Chat] Error parsing saved user:", e)
          }
        }
      }
    }
    
    if (!userId || userId === "demo" || userId === "undefined" || userId === "null") {
      console.error("[Chat] ❌ User ID не найден для приветствия:", userId)
      return
    }

    try {
      setGreetingLoaded(true)
      const apiBaseUrl = typeof window !== "undefined" && window.location.hostname === "localhost"
        ? "http://localhost:8080"
        : "https://api.pasekaproduction.ru"

      const response = await fetch(`${apiBaseUrl}/api/chat/greeting?user_id=${userId}`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
        mode: "cors",
      })

      console.log(`[Chat] Greeting API Response: status=${response.status}, ok=${response.ok}`)
      // #region agent log
      fetch('http://127.0.0.1:7244/ingest/5297ce20-cdd6-4734-9a97-89b776b10890',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'ChatPage.tsx:245',message:'loadGreeting API response received',data:{status:response.status,ok:response.ok,statusText:response.statusText},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'G'})}).catch(()=>{});
      // #endregion
      
      if (response.ok) {
        const data = await response.json()
        console.log(`[Chat] Greeting API Data:`, data)
          if (data.success && data.greeting) {
            // Добавляем приветственное сообщение в список
            const greetingMsg: ChatMessage = {
              id: Date.now(),
              role: "assistant",
              content: data.greeting,
              created_at: new Date().toISOString(),
            }
            setMessages((prev) => prev.length === 0 ? [greetingMsg] : prev)
          } else if (data.greeting) {
            // Добавляем приветственное сообщение в список
            const greetingMsg: ChatMessage = {
              id: Date.now(),
              role: "assistant",
              content: data.greeting,
              created_at: new Date().toISOString(),
            }
            setMessages((prev) => prev.length === 0 ? [greetingMsg] : prev)
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
    if (!inputMessage.trim() || sending) return

    // Получаем user_id из разных источников
    let userId: string | null = null
    
    if (user?.id) {
      userId = user.id.toString()
    } else if (typeof window !== "undefined") {
      const tg = (window as any).Telegram?.WebApp
      if (tg?.initDataUnsafe?.user?.id) {
        userId = tg.initDataUnsafe.user.id.toString()
      } else {
        const savedUser = localStorage.getItem("telegram_user")
        if (savedUser) {
          try {
            const parsed = JSON.parse(savedUser)
            userId = parsed.id?.toString() || null
          } catch (e) {
            console.error("[Chat] Error parsing saved user:", e)
          }
        }
      }
    }
    
    if (!userId || userId === "demo" || userId === "undefined" || userId === "null") {
      console.error("[Chat] ❌ User ID не найден или невалиден:", userId)
      setError("Не удалось определить ID пользователя. Откройте приложение через Telegram.")
      return
    }

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
        : "https://api.pasekaproduction.ru"

      const response = await fetch(`${apiBaseUrl}/api/chat/send`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        mode: "cors",
        body: JSON.stringify({
          user_id: parseInt(userId),
          message: messageText,
        }),
      })

      if (!response.ok) {
        let errorText = ""
        try {
          const errorData = await response.json()
          errorText = errorData.error || response.statusText
        } catch (e) {
          errorText = await response.text().catch(() => response.statusText)
        }
        throw new Error(errorText || "Ошибка отправки сообщения")
      }

      let data
      try {
        const responseText = await response.text()
        console.log(`[Chat] Raw Send Response:`, responseText)
        data = JSON.parse(responseText)
      } catch (e) {
        console.error(`[Chat] Ошибка парсинга JSON:`, e)
        throw new Error("Неверный формат ответа от сервера")
      }
      
      console.log(`[Chat] Parsed Send Data:`, data)
      
      if (data.success && data.message) {
        console.log(`[Chat] ✅ Получен ответ от AI`)
        const assistantMessage: ChatMessage = {
          id: Date.now() + 1,
          role: "assistant",
          content: data.message,
          created_at: new Date().toISOString(),
        }
        setMessages((prev) => [...prev, assistantMessage])
      } else if (data.message) {
        console.log(`[Chat] ✅ Получен ответ от AI (без success поля)`)
        const assistantMessage: ChatMessage = {
          id: Date.now() + 1,
          role: "assistant",
          content: data.message,
          created_at: new Date().toISOString(),
        }
        setMessages((prev) => [...prev, assistantMessage])
      } else if (data.error) {
        console.error(`[Chat] ❌ API вернул ошибку:`, data.error)
        throw new Error(data.error || "Ошибка отправки сообщения")
      } else {
        console.warn(`[Chat] ⚠️ Неожиданный формат ответа:`, data)
        throw new Error("Неожиданный формат ответа от сервера")
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

