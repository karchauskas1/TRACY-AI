"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { ChevronRight, User, Globe, Bell, Brain, Calendar, X, MoreVertical, ArrowLeft, Sun, Moon } from "lucide-react"
import { Card, CardContent } from "../../components/ui/card"
import { Avatar, AvatarFallback, AvatarImage } from "../../components/ui/avatar"
import { Button } from "../../components/ui/button"
import { useLocale } from "../../lib/locale-context"
import { useTheme } from "../../lib/theme-context"

interface SettingsPageClientProps {
  user: {
    id: string
    name: string
    avatarUrl?: string
    photo_url?: string
    first_name?: string
    last_name?: string
  } | null
}

export function SettingsPageClient({ user: initialUser }: SettingsPageClientProps) {
  const router = useRouter()
  const { t } = useLocale()
  const { theme, setTheme, resolvedTheme } = useTheme()
  const [user, setUser] = useState(initialUser)

  useEffect(() => {
    // Загружаем данные пользователя из Telegram Web App или localStorage
    if (typeof window !== "undefined") {
      const tg = (window as any).Telegram?.WebApp
      if (tg) {
        tg.ready()
        const tgUser = tg.initDataUnsafe?.user
        if (tgUser) {
          const fullName = [tgUser.first_name, tgUser.last_name].filter(Boolean).join(" ")
          setUser({
            id: tgUser.id.toString(),
            name: fullName || tgUser.first_name || "Пользователь",
            avatarUrl: tgUser.photo_url,
            first_name: tgUser.first_name,
            last_name: tgUser.last_name,
          })
        }
      } else {
        const savedUser = localStorage.getItem("telegram_user")
        if (savedUser) {
          try {
            const parsed = JSON.parse(savedUser)
            const fullName = [parsed.first_name, parsed.last_name].filter(Boolean).join(" ")
            setUser({
              ...parsed,
              name: fullName || parsed.first_name || "Пользователь",
            })
          } catch (e) {
            console.error("Failed to parse user:", e)
          }
        }
      }
    }
  }, [])

  const handleBack = () => {
    router.push("/calendar")
  }

  const handleClose = () => {
    if (typeof window !== "undefined" && (window as any).Telegram?.WebApp) {
      (window as any).Telegram.WebApp.close()
    } else {
      router.push("/calendar")
    }
  }

  const settingsItems = [
    {
      icon: User,
      label: t("settings.account"),
      href: "/settings/account",
    },
    {
      icon: Globe,
      label: t("settings.general"),
      href: "/settings/general",
    },
    {
      icon: Bell,
      label: t("settings.notifications"),
      href: "/settings/notifications",
    },
    {
      icon: Brain,
      label: t("settings.ai"),
      href: "/settings/ai",
    },
    {
      icon: Calendar,
      label: t("settings.calendars"),
      href: "/settings/calendars",
    },
  ]

  const handleThemeToggle = () => {
    if (theme === "dark") {
      setTheme("light")
    } else if (theme === "light") {
      setTheme("system")
    } else {
      setTheme("dark")
    }
  }

  const getThemeLabel = () => {
    if (theme === "system") {
      return "Системная"
    }
    return theme === "dark" ? "Тёмная" : "Светлая"
  }

  const displayName = user?.name || [user?.first_name, user?.last_name].filter(Boolean).join(" ") || "Пользователь"
  const avatarInitials = displayName
    .split(" ")
    .map((n: string) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2) || "U"

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      {/* Header - как на скриншоте */}
      <header className="sticky top-0 z-20 border-b border-border bg-background/95 backdrop-blur">
        <div className="flex h-14 items-center justify-between px-4">
          <button
            onClick={handleBack}
            className="text-foreground hover:text-muted-foreground transition-colors"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div className="flex items-center gap-2">
            <div className="h-6 w-6 rounded-full bg-primary flex items-center justify-center">
              <span className="text-xs font-bold text-primary-foreground">T</span>
            </div>
            <span className="text-sm font-medium">{t("settings.tracyAssistant")}</span>
          </div>
          <button
            onClick={handleClose}
            className="text-foreground hover:text-muted-foreground transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto">
        <div className="container mx-auto max-w-2xl px-4 py-6">
          <div className="mb-6">
            <h1 className="text-3xl font-semibold">{t("settings.title")}</h1>
          </div>

          {/* Profile Header */}
          <Card className="mb-6 border-border">
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <Avatar className="h-20 w-20">
                  <AvatarImage src={user?.avatarUrl || user?.photo_url} alt={displayName} />
                  <AvatarFallback className="bg-muted text-muted-foreground text-2xl">
                    {avatarInitials}
                  </AvatarFallback>
                </Avatar>
                <div>
                  <h2 className="text-xl font-semibold">{displayName}</h2>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Settings List */}
          <Card className="border-border">
            <CardContent className="p-0">
              {settingsItems.map((item, index) => {
                const Icon = item.icon
                return (
                  <div key={item.href}>
                    {index > 0 && <div className="border-t border-border" />}
                    <button
                      onClick={() => router.push(item.href)}
                      className="w-full flex items-center justify-between p-4 hover:bg-accent/50 transition-colors"
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
              <div className="border-t border-border" />
              <button
                onClick={handleThemeToggle}
                className="w-full flex items-center justify-between p-4 hover:bg-accent/50 transition-colors"
              >
                <div className="flex items-center gap-3">
                  {resolvedTheme === "dark" ? (
                    <Moon className="h-5 w-5 text-muted-foreground" />
                  ) : (
                    <Sun className="h-5 w-5 text-muted-foreground" />
                  )}
                  <span className="font-medium">Тема: {getThemeLabel()}</span>
                </div>
                <ChevronRight className="h-5 w-5 text-muted-foreground" />
              </button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

