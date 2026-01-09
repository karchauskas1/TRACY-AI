"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { X, Bell, ArrowLeft } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "../../../components/ui/card"
import { Button } from "../../../components/ui/button"

export default function NotificationsPage() {
  const router = useRouter()
  const [notificationsEnabled, setNotificationsEnabled] = useState(true)
  const [morningDigest, setMorningDigest] = useState("09:00")
  const [defaultReminder, setDefaultReminder] = useState("15")

  const handleClose = () => {
    router.push("/settings")
  }

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
          <h1 className="text-lg font-semibold">Уведомления</h1>
          <div className="w-5" />
        </div>
      </header>

      <div className="flex-1 overflow-y-auto">
        <div className="container mx-auto max-w-2xl px-4 py-6 space-y-4">
          <Card className="border-border">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Bell className="h-5 w-5" />
                Настройки уведомлений
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">Включить уведомления</p>
                  <p className="text-sm text-muted-foreground">
                    Получать напоминания о событиях
                  </p>
                </div>
                <button
                  onClick={() => setNotificationsEnabled(!notificationsEnabled)}
                  className={`relative w-12 h-6 rounded-full transition-colors ${
                    notificationsEnabled ? "bg-primary" : "bg-muted"
                  }`}
                >
                  <span
                    className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full transition-transform ${
                      notificationsEnabled ? "translate-x-6" : "translate-x-0"
                    }`}
                  />
                </button>
              </div>

              <div className="pt-4 border-t border-border">
                <label className="text-sm font-medium mb-2 block">
                  Утренний дайджест
                </label>
                <input
                  type="time"
                  value={morningDigest}
                  onChange={(e) => setMorningDigest(e.target.value)}
                  className="w-full px-3 py-2 bg-card border border-border rounded-lg text-foreground"
                />
                <p className="text-xs text-muted-foreground mt-1">
                  Время ежедневного обзора событий
                </p>
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">
                  Напоминание по умолчанию
                </label>
                <select
                  value={defaultReminder}
                  onChange={(e) => setDefaultReminder(e.target.value)}
                  className="w-full px-3 py-2 bg-card border border-border rounded-lg text-foreground"
                >
                  <option value="0">В момент начала</option>
                  <option value="5">За 5 минут</option>
                  <option value="15">За 15 минут</option>
                  <option value="30">За 30 минут</option>
                  <option value="60">За 1 час</option>
                  <option value="1440">За 1 день</option>
                </select>
                <p className="text-xs text-muted-foreground mt-1">
                  Напоминание будет установлено для всех новых событий
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

