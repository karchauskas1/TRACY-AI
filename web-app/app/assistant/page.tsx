"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { Calendar, Settings, Mic, FileAudio, History, Sparkles, MessageSquare, ListTodo, MessageCircle, Bug } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card"
import { Avatar, AvatarFallback, AvatarImage } from "../../components/ui/avatar"
import { Button } from "../../components/ui/button"
import { useTelegramUser } from "../../lib/useTelegramUser"

export default function AssistantPage() {
  const router = useRouter()
  const { user: telegramUser, userId, isLoading: userLoading } = useTelegramUser()
  const [user, setUser] = useState<any>(null)
  const [isSuperUser, setIsSuperUser] = useState(false)

  useEffect(() => {
    console.log("[AssistantPage] userLoading:", userLoading, "userId:", userId)
    
    // Если пользователь не загружен и не загружается, перенаправляем на логин
    if (!userLoading && !userId) {
      console.log("[AssistantPage] No user, redirecting to login")
      router.push("/login")
      return
    }

    // Если пользователь загружен, обновляем состояние
    if (telegramUser && userId) {
      const fullName = [telegramUser.first_name, telegramUser.last_name].filter(Boolean).join(" ")
      console.log("[AssistantPage] User loaded:", fullName)
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

    // Настраиваем Telegram Web App, если доступен
    if (typeof window !== "undefined") {
      const tg = (window as any).Telegram?.WebApp
      if (tg) {
        tg.ready()
        tg.expand()
        tg.setHeaderColor("#1a1a20")
        tg.setBackgroundColor("#1a1a20")
      }
    }
  }, [telegramUser, userId, userLoading, router])

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
            onClick={() => router.push("/settings")}
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
                      onClick={() => router.push("/login")}
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
          <div className="space-y-8">
            {/* Чат с Tracy */}
            <Card 
              className="border-border hover:bg-accent/50 transition-colors cursor-pointer mb-2"
              onClick={() => router.push("/chat")}
            >
              <CardContent className="p-6">
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
              </CardContent>
            </Card>

            {/* Calendar */}
            <Card 
              className="border-border hover:bg-accent/50 transition-colors cursor-pointer mb-2"
              onClick={() => router.push("/calendar")}
            >
              <CardContent className="p-6">
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
              </CardContent>
            </Card>

            {/* История расшифровок */}
            <Card 
              className="border-border hover:bg-accent/50 transition-colors cursor-pointer mb-2"
              onClick={() => router.push("/meetings/history")}
            >
              <CardContent className="p-6">
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
              </CardContent>
            </Card>

            {/* Списки задач */}
            <Card 
              className="border-border hover:bg-accent/50 transition-colors cursor-pointer mb-2"
              onClick={() => router.push("/todo-lists")}
            >
              <CardContent className="p-6">
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
              </CardContent>
            </Card>

            {/* Обратная связь (только для супер-пользователя) */}
            {isSuperUser && (
              <>
                <Card 
                  className="border-border hover:bg-accent/50 transition-colors cursor-pointer mb-2"
                  onClick={() => router.push("/settings/feedback")}
                >
                  <CardContent className="p-6">
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
                  </CardContent>
                </Card>
                <Card 
                  className="border-border hover:bg-accent/50 transition-colors cursor-pointer mb-2"
                  onClick={() => router.push("/debug")}
                >
                  <CardContent className="p-6">
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
                  </CardContent>
                </Card>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

