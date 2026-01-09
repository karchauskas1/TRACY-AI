"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { ChevronRight, User, Globe, Bell, Brain, Calendar, LogOut } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"

interface SettingsPageClientProps {
  user: {
    id: string
    name: string
    avatarUrl?: string
  } | null
}

export function SettingsPageClient({ user }: SettingsPageClientProps) {
  const router = useRouter()

  const handleLogout = async () => {
    // Для статического экспорта просто очищаем localStorage
    localStorage.removeItem("telegram_user")
    localStorage.removeItem("tracy_events")
    router.push("/login")
  }

  const settingsItems = [
    {
      icon: User,
      label: "Аккаунт",
      href: "/settings/account",
    },
    {
      icon: Globe,
      label: "Общие",
      href: "/settings/general",
    },
    {
      icon: Bell,
      label: "Уведомления",
      href: "/settings/notifications",
    },
    {
      icon: Brain,
      label: "ИИ",
      href: "/settings/ai",
    },
    {
      icon: Calendar,
      label: "Календари",
      href: "/settings/calendars",
    },
  ]

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto max-w-2xl px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-semibold mb-2">Настройки</h1>
        </div>

        {/* Profile Header */}
        <Card className="mb-6">
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <Avatar className="h-16 w-16">
                <AvatarImage src={user?.avatarUrl} alt={user?.name || "User"} />
                <AvatarFallback>
                  {user?.name
                    ?.split(" ")
                    .map((n) => n[0])
                    .join("")
                    .toUpperCase() || "U"}
                </AvatarFallback>
              </Avatar>
              <div>
                <h2 className="text-xl font-semibold">{user?.name || "Пользователь"}</h2>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Settings List */}
        <Card>
          <CardContent className="p-0">
            {settingsItems.map((item, index) => {
              const Icon = item.icon
              return (
                <div key={item.href}>
                  {index > 0 && <div className="border-t" />}
                  <button
                    onClick={() => router.push(item.href)}
                    className="w-full flex items-center justify-between p-4 hover:bg-accent transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <Icon className="h-5 w-5 text-muted-foreground" />
                      <span className="font-medium">{item.label}</span>
                    </div>
                    <ChevronRight className="h-5 w-5 text-muted-foreground" />
                  </button>
                </div>
              )
            })}
            <div className="border-t" />
            <button
              onClick={handleLogout}
              className="w-full flex items-center justify-between p-4 hover:bg-accent transition-colors text-destructive"
            >
              <div className="flex items-center gap-3">
                <LogOut className="h-5 w-5" />
                <span className="font-medium">Выйти</span>
              </div>
            </button>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

