"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Bell, ArrowLeft } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "../../../components/ui/card"
import { Button } from "../../../components/ui/button"
import { useLocale } from "../../../lib/locale-context"
import { useToast } from "../../../hooks/use-toast"

export default function NotificationsPage() {
  const router = useRouter()
  const { locale, t } = useLocale()
  const { toast } = useToast()
  const [notificationsEnabled, setNotificationsEnabled] = useState(true)
  const [morningDigestEnabled, setMorningDigestEnabled] = useState(true)
  const [morningDigest, setMorningDigest] = useState("09:00")
  const [defaultReminder, setDefaultReminder] = useState("15")

  useEffect(() => {
    // Load settings from localStorage
    const savedNotifications = localStorage.getItem("tracy_web_notifications_enabled")
    if (savedNotifications !== null) {
      setNotificationsEnabled(savedNotifications === "true")
    }
    const savedDigestEnabled = localStorage.getItem("tracy_morning_digest_enabled")
    if (savedDigestEnabled !== null) {
      setMorningDigestEnabled(savedDigestEnabled === "true")
    }
    const savedDigest = localStorage.getItem("tracy_morning_digest")
    if (savedDigest) {
      setMorningDigest(savedDigest)
    }
    const savedReminder = localStorage.getItem("tracy_web_default_reminder")
    if (savedReminder) {
      setDefaultReminder(savedReminder)
    }
  }, [])

  const handleClose = () => {
    router.push("/settings")
  }

  const handleToggleNotifications = () => {
    const newValue = !notificationsEnabled
    setNotificationsEnabled(newValue)
    localStorage.setItem("tracy_web_notifications_enabled", String(newValue))
    // Send to bot via Telegram Web App API
    if (typeof window !== "undefined") {
      const tg = (window as any).Telegram?.WebApp
      if (tg) {
        tg.sendData(JSON.stringify({
          action: "update_notifications",
          enabled: newValue,
        }))
      }
    }
    toast({
      title: t("common.save"),
      description: newValue 
        ? (t("settings.notificationsEnableDesc"))
        : (t("settings.notificationsWarning")),
    })
  }

  const handleToggleDigest = () => {
    const newValue = !morningDigestEnabled
    setMorningDigestEnabled(newValue)
    localStorage.setItem("tracy_morning_digest_enabled", String(newValue))
    
    // Send to bot via Telegram Web App API
    if (typeof window !== "undefined") {
      const tg = (window as any).Telegram?.WebApp
      if (tg) {
        tg.sendData(JSON.stringify({
          action: "update_morning_digest",
          enabled: newValue,
          time: morningDigest,
          default_reminder: defaultReminder,
        }))
      }
    }
    
    toast({
      title: t("common.save"),
      description: newValue 
        ? (locale === "ru" ? "Утренний дайджест включен" : "Morning digest enabled")
        : (locale === "ru" ? "Утренний дайджест выключен" : "Morning digest disabled"),
    })
  }

  const handleSave = () => {
    localStorage.setItem("tracy_morning_digest", morningDigest)
    localStorage.setItem("tracy_web_default_reminder", defaultReminder)
    localStorage.setItem("tracy_morning_digest_enabled", String(morningDigestEnabled))
    
    // Send to bot via Telegram Web App API
    if (typeof window !== "undefined") {
      const tg = (window as any).Telegram?.WebApp
      if (tg) {
        tg.sendData(JSON.stringify({
          action: "update_morning_digest",
          enabled: morningDigestEnabled,
          time: morningDigest,
          default_reminder: defaultReminder,
        }))
      }
    }
    
    toast({
      title: t("common.save"),
      description: locale === "ru" 
        ? `Настройки сохранены. Дайджест ${morningDigestEnabled ? 'включен' : 'выключен'}.` 
        : `Settings saved. Digest ${morningDigestEnabled ? 'enabled' : 'disabled'}.`,
    })
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
          <h1 className="text-lg font-semibold">{t("settings.notifications")}</h1>
          <div className="w-5" />
        </div>
      </header>

      <div className="flex-1 overflow-y-auto">
        <div className="container mx-auto max-w-2xl px-4 py-6 space-y-4">
          {/* Карточка 1: Основные уведомления */}
          <Card className="border-border">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Bell className="h-5 w-5" />
                {t("settings.notificationsTitle")}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <p className="font-medium">{t("settings.notificationsEnable")}</p>
                  <p className="text-sm text-muted-foreground mt-1">
                    {t("settings.notificationsEnableDesc")}
                  </p>
                </div>
                <button
                  onClick={handleToggleNotifications}
                  className={`relative w-12 h-6 rounded-full transition-colors flex-shrink-0 ${
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

              {!notificationsEnabled && (
                <div className="p-3 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
                  <p className="text-xs text-yellow-600 dark:text-yellow-400">
                    {t("settings.notificationsWarning")}
                  </p>
                </div>
              )}

              {/* Default Reminder - под переключателем уведомлений */}
              {notificationsEnabled && (
                <div className="pt-4 border-t border-border">
                  <label className="text-sm font-medium mb-2 block">
                    {t("settings.defaultReminder")}
                  </label>
                  <select
                    value={defaultReminder}
                    onChange={(e) => setDefaultReminder(e.target.value)}
                    className="w-full px-3 py-2 bg-card border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                  >
                    <option value="0">{t("settings.reminderAtStart")}</option>
                    <option value="5">{t("settings.reminderBefore5")}</option>
                    <option value="15">{t("settings.reminderBefore15")}</option>
                    <option value="30">{t("settings.reminderBefore30")}</option>
                    <option value="60">{t("settings.reminderBefore1h")}</option>
                    <option value="1440">{t("settings.reminderBefore1d")}</option>
                  </select>
                  <p className="text-xs text-muted-foreground mt-1">
                    {t("settings.defaultReminderDesc")}
                  </p>
                </div>
              )}

              <div className="pt-4">
                <Button onClick={handleSave} className="w-full">
                  {t("common.save")}
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Карточка 2: Утренний дайджест (отдельный блок) */}
          <Card className="border-border">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Bell className="h-5 w-5" />
                {t("settings.morningDigest")}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <p className="font-medium">
                    {locale === "ru" ? "Включить утренний дайджест" : "Enable morning digest"}
                  </p>
                  <p className="text-sm text-muted-foreground mt-1">
                    {locale === "ru" 
                      ? "Ежедневный обзор событий с мотивационной цитатой" 
                      : "Daily events review with motivational quote"}
                  </p>
                </div>
                <button
                  onClick={handleToggleDigest}
                  className={`relative w-12 h-6 rounded-full transition-colors flex-shrink-0 ${
                    morningDigestEnabled ? "bg-primary" : "bg-muted"
                  }`}
                >
                  <span
                    className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full transition-transform ${
                      morningDigestEnabled ? "translate-x-6" : "translate-x-0"
                    }`}
                  />
                </button>
              </div>

              {morningDigestEnabled && (
                <div className="space-y-3 pt-4 border-t border-border">
                  <label className="text-sm font-medium block text-center">
                    {locale === "ru" ? "Время отправки" : "Delivery time"}
                  </label>
                  <div className="flex justify-center">
                    <input
                      type="time"
                      value={morningDigest}
                      onChange={(e) => setMorningDigest(e.target.value)}
                      className="w-full max-w-xs px-4 py-2.5 bg-card border border-border rounded-lg text-foreground text-center focus:outline-none focus:ring-2 focus:ring-primary"
                    />
                  </div>
                  <p className="text-xs text-muted-foreground text-center">
                    {t("settings.morningDigestDesc")}
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

