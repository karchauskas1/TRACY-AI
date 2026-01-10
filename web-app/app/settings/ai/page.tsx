"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Brain, ArrowLeft } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "../../../components/ui/card"
import { Button } from "../../../components/ui/button"
import { useLocale } from "../../../lib/locale-context"
import { useToast } from "../../../hooks/use-toast"

export default function AIPage() {
  const router = useRouter()
  const { locale, t } = useLocale()
  const { toast } = useToast()
  const [interpretationMode, setInterpretationMode] = useState<"strict" | "soft">("soft")
  const [smartReplyEnabled, setSmartReplyEnabled] = useState(true)

  useEffect(() => {
    // Load settings from localStorage
    const savedMode = localStorage.getItem("tracy_ai_mode")
    if (savedMode === "strict" || savedMode === "soft") {
      setInterpretationMode(savedMode)
    }
    const savedSmartReply = localStorage.getItem("tracy_smart_reply")
    if (savedSmartReply !== null) {
      setSmartReplyEnabled(savedSmartReply === "true")
    }
  }, [])

  const handleClose = () => {
    router.push("/settings")
  }

  const handleSave = () => {
    localStorage.setItem("tracy_ai_mode", interpretationMode)
    localStorage.setItem("tracy_smart_reply", String(smartReplyEnabled))
    
    // Send to bot via Telegram Web App API
    if (typeof window !== "undefined") {
      const tg = (window as any).Telegram?.WebApp
      if (tg) {
        tg.sendData(JSON.stringify({
          action: "update_ai_settings",
          mode: interpretationMode,
          smart_reply: smartReplyEnabled,
        }))
      }
    }
    
    toast({
      title: t("common.save"),
      description: locale === "ru" ? "Настройки ИИ сохранены" : "AI settings saved",
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
          <h1 className="text-lg font-semibold">{t("settings.ai")}</h1>
          <div className="w-5" />
        </div>
      </header>

      <div className="flex-1 overflow-y-auto">
        <div className="container mx-auto max-w-2xl px-4 py-6 space-y-4">
          <Card className="border-border">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Brain className="h-5 w-5" />
                {t("settings.aiTitle")}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <p className="font-medium">{t("settings.aiSmartReply")}</p>
                  <p className="text-sm text-muted-foreground mt-1">
                    {t("settings.aiSmartReplyDesc")}
                  </p>
                </div>
                <button
                  onClick={() => setSmartReplyEnabled(!smartReplyEnabled)}
                  className={`relative w-12 h-6 rounded-full transition-colors ${
                    smartReplyEnabled ? "bg-primary" : "bg-muted"
                  }`}
                >
                  <span
                    className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full transition-transform ${
                      smartReplyEnabled ? "translate-x-6" : "translate-x-0"
                    }`}
                  />
                </button>
              </div>

              <div className="pt-4 border-t border-border">
                <label className="text-sm font-medium mb-2 block">{t("settings.aiInterpretation")}</label>
                <div className="space-y-2">
                  <button
                    onClick={() => setInterpretationMode("strict")}
                    className={`w-full p-3 rounded-lg border text-left transition-colors ${
                      interpretationMode === "strict"
                        ? "border-primary bg-primary/10"
                        : "border-border hover:bg-accent/50"
                    }`}
                  >
                    <p className="font-medium">{t("settings.aiInterpretationStrict")}</p>
                    <p className="text-xs text-muted-foreground mt-1">
                      {t("settings.aiInterpretationStrictDesc")}
                    </p>
                  </button>
                  <button
                    onClick={() => setInterpretationMode("soft")}
                    className={`w-full p-3 rounded-lg border text-left transition-colors ${
                      interpretationMode === "soft"
                        ? "border-primary bg-primary/10"
                        : "border-border hover:bg-accent/50"
                    }`}
                  >
                    <p className="font-medium">{t("settings.aiInterpretationSoft")}</p>
                    <p className="text-xs text-muted-foreground mt-1">
                      {t("settings.aiInterpretationSoftDesc")}
                    </p>
                  </button>
                </div>
              </div>

              <div className="pt-4">
                <Button onClick={handleSave} className="w-full">
                  {t("common.save")}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

