"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { X, User, ArrowLeft } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "../../../components/ui/card"
import { Avatar, AvatarFallback, AvatarImage } from "../../../components/ui/avatar"
import { Button } from "../../../components/ui/button"
import { useLocale } from "../../../lib/locale-context"

export default function AccountPage() {
  const router = useRouter()
  const { t } = useLocale()
  const [user, setUser] = useState<any>(null)

  useEffect(() => {
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
            username: tgUser.username,
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

  const handleClose = () => {
    router.push("/settings")
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
      <header className="sticky top-0 z-20 border-b border-border bg-background/95 backdrop-blur">
        <div className="flex h-14 items-center justify-between px-4">
          <button
            onClick={handleClose}
            className="text-foreground hover:text-muted-foreground transition-colors"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <h1 className="text-lg font-semibold">{t("settings.account")}</h1>
          <div className="w-5" />
        </div>
      </header>

      <div className="flex-1 overflow-y-auto">
        <div className="container mx-auto max-w-2xl px-4 py-6">
          <Card className="border-border">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <User className="h-5 w-5" />
                {t("settings.profile")}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center gap-4">
                <Avatar className="h-24 w-24">
                  <AvatarImage src={user?.avatarUrl || user?.photo_url} alt={displayName} />
                  <AvatarFallback className="bg-muted text-muted-foreground text-3xl">
                    {avatarInitials}
                  </AvatarFallback>
                </Avatar>
                <div className="flex-1">
                  <h2 className="text-xl font-semibold mb-1">{displayName}</h2>
                  {user?.username && (
                    <p className="text-sm text-muted-foreground">@{user.username}</p>
                  )}
                </div>
              </div>

              <div className="space-y-4 pt-4 border-t border-border">
                <div>
                  <label className="text-sm font-medium text-muted-foreground mb-1 block">
                    {t("settings.firstName")}
                  </label>
                  <p className="text-base">{user?.first_name || "—"}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-muted-foreground mb-1 block">
                    {t("settings.lastName")}
                  </label>
                  <p className="text-base">{user?.last_name || "—"}</p>
                </div>
                {user?.username && (
                  <div>
                    <label className="text-sm font-medium text-muted-foreground mb-1 block">
                      {t("settings.username")}
                    </label>
                    <p className="text-base">@{user.username}</p>
                  </div>
                )}
                <div>
                  <label className="text-sm font-medium text-muted-foreground mb-1 block">
                    {t("settings.id")}
                  </label>
                  <p className="text-base font-mono text-sm">{user?.id || "—"}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

