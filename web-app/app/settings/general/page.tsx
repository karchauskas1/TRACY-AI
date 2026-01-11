"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Globe, ArrowLeft } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "../../../components/ui/card"
import { Button } from "../../../components/ui/button"
import { useLocale } from "../../../lib/locale-context"
import { useToast } from "../../../hooks/use-toast"

export default function GeneralPage() {
  const router = useRouter()
  const { locale, setLocale, t } = useLocale()
  const { toast } = useToast()
  const [user, setUser] = useState<any>(null)
  const [selectedLanguage, setSelectedLanguage] = useState<"ru" | "en">(locale)

  useEffect(() => {
    // Load user from Telegram Web App or localStorage
    if (typeof window !== "undefined") {
      const tg = (window as any).Telegram?.WebApp
      if (tg && tg.initDataUnsafe?.user) {
        setUser(tg.initDataUnsafe.user)
      } else {
        const savedUser = localStorage.getItem("telegram_user")
        if (savedUser) {
          try {
            setUser(JSON.parse(savedUser))
          } catch (e) {
            console.error("Failed to parse user:", e)
          }
        }
      }
    }

    // Load saved language from localStorage
    const savedLocale = localStorage.getItem('tracy_locale') as "ru" | "en" | null
    if (savedLocale && (savedLocale === "ru" || savedLocale === "en")) {
      setSelectedLanguage(savedLocale)
    } else {
      setSelectedLanguage(locale)
    }
  }, [locale])

  const handleClose = () => {
    router.push("/settings")
  }

  const handleLanguageChange = (newLang: "ru" | "en") => {
    setSelectedLanguage(newLang)
  }

  const handleSave = async () => {
    // Сохраняем язык в localStorage и в контексте
    try {
      localStorage.setItem('tracy_locale', selectedLanguage)
      
      // Обновляем язык в контексте
      setLocale(selectedLanguage)
      
      // Обновляем HTML lang атрибут
      if (typeof document !== 'undefined') {
        document.documentElement.lang = selectedLanguage
      }

      // Сохраняем в API
      if (user?.id) {
        try {
          const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080'
          const lang_code = selectedLanguage === 'ru' ? 'ru_RU' : 'en_US'
          await fetch(`${apiBaseUrl}/api/settings`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              user_id: user.id,
              locale: lang_code,
            }),
            mode: 'cors',
          })
        } catch (error) {
          console.error("Failed to save settings to API:", error)
        }
      }
      
      toast({
        title: selectedLanguage === "ru" ? "Сохранено" : "Saved",
        description: selectedLanguage === "ru" 
          ? "Язык изменен на русский. Страница будет перезагружена." 
          : "Language changed to English. Page will reload.",
      })
      
      // Перезагружаем страницу для применения изменений языка
      setTimeout(() => {
        window.location.reload()
      }, 1000)
    } catch (error) {
      console.error('Ошибка сохранения языка:', error)
      toast({
        title: "Ошибка",
        description: "Не удалось сохранить язык. Попробуйте еще раз.",
      })
    }
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
          <h1 className="text-lg font-semibold">{t("settings.general")}</h1>
          <div className="w-5" />
        </div>
      </header>

      <div className="flex-1 overflow-y-auto">
        <div className="container mx-auto max-w-2xl px-4 py-6 space-y-4">
          <Card className="border-border">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Globe className="h-5 w-5" />
                {t("settings.language")}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">{t("settings.languageSelect")}</label>
                <select
                  value={selectedLanguage}
                  onChange={(e) => handleLanguageChange(e.target.value as "ru" | "en")}
                  className="w-full px-3 py-2 bg-card border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  <option value="ru">Русский</option>
                  <option value="en">English</option>
                </select>
                <p className="text-xs text-muted-foreground mt-2">
                  {selectedLanguage === "ru" 
                    ? "Язык интерфейса приложения" 
                    : "Application interface language"}
                </p>
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

