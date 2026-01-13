"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { Calendar, Settings, Mic, FileAudio, History, Sparkles, MessageSquare, ListTodo, MessageCircle, Bug } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card"
import { Avatar, AvatarFallback, AvatarImage } from "../../components/ui/avatar"
import { Button } from "../../components/ui/button"
import Link from "next/link"

export default function AssistantPage() {
  const router = useRouter()
  const [user, setUser] = useState<any>(null)
  const [isSuperUser, setIsSuperUser] = useState(false)

  useEffect(() => {
    // Загружаем данные пользователя из Telegram Web App или localStorage
    if (typeof window !== "undefined") {
      const tg = (window as any).Telegram?.WebApp
      if (tg) {
        tg.ready()
        tg.expand()
        tg.setHeaderColor("#1a1a20")
        tg.setBackgroundColor("#1a1a20")
        
        const tgUser = tg.initDataUnsafe?.user
        if (tgUser) {
          const fullName = [tgUser.first_name, tgUser.last_name].filter(Boolean).join(" ")
          const userId = tgUser.id.toString()
          setUser({
            id: userId,
            name: fullName || tgUser.first_name || "Пользователь",
            avatarUrl: tgUser.photo_url,
            first_name: tgUser.first_name,
            last_name: tgUser.last_name,
            username: tgUser.username,
          })
          // Проверяем, является ли пользователь супер-пользователем (ID: 308477378)
          setIsSuperUser(userId === "308477378")
        }
      } else {
        const savedUser = localStorage.getItem("telegram_user")
        if (savedUser) {
          try {
            const parsed = JSON.parse(savedUser)
            const fullName = [parsed.first_name, parsed.last_name].filter(Boolean).join(" ")
            const userId = parsed.id?.toString()
            setUser({
              ...parsed,
              name: fullName || parsed.first_name || "Пользователь",
            })
            // Проверяем, является ли пользователь супер-пользователем
            setIsSuperUser(userId === "308477378")
          } catch (e) {
            console.error("Failed to parse user:", e)
          }
        }
      }
    }
  }, [])

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
          <Link href="/settings">
            <button className="text-foreground hover:text-muted-foreground transition-colors">
              <Settings className="h-5 w-5" />
            </button>
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
                  <div>
                    <h2 className="text-xl font-semibold">{displayName}</h2>
                    {user?.username && (
                      <p className="text-sm text-muted-foreground">@{user.username}</p>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Main Features */}
          <div className="space-y-8">
            {/* Чат с Tracy */}
            <Link href="/chat">
              <Card className="border-border hover:bg-accent/50 transition-colors cursor-pointer mb-2">
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
            </Link>

            {/* Calendar */}
            <Link href="/calendar">
              <Card className="border-border hover:bg-accent/50 transition-colors cursor-pointer mb-2">
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
            </Link>

            {/* История расшифровок */}
            <Link href="/meetings/history">
              <Card className="border-border hover:bg-accent/50 transition-colors cursor-pointer mb-2">
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
            </Link>

            {/* Списки задач */}
            <Link href="/todo-lists">
              <Card className="border-border hover:bg-accent/50 transition-colors cursor-pointer mb-2">
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
            </Link>

            {/* Обратная связь (только для супер-пользователя) */}
            {isSuperUser && (
              <>
                <Link href="/settings/feedback">
                  <Card className="border-border hover:bg-accent/50 transition-colors cursor-pointer mb-2">
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
                </Link>
                <Link href="/debug">
                  <Card className="border-border hover:bg-accent/50 transition-colors cursor-pointer mb-2">
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
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

