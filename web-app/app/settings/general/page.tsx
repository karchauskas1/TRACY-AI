"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { X, Globe, ArrowLeft } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "../../../components/ui/card"
import { Button } from "../../../components/ui/button"

export default function GeneralPage() {
  const router = useRouter()
  const [language, setLanguage] = useState("ru")
  const [timezone, setTimezone] = useState("Europe/Moscow")
  const [timeFormat, setTimeFormat] = useState<"12" | "24">("24")

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
          <h1 className="text-lg font-semibold">Общие</h1>
          <div className="w-5" />
        </div>
      </header>

      <div className="flex-1 overflow-y-auto">
        <div className="container mx-auto max-w-2xl px-4 py-6 space-y-4">
          <Card className="border-border">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Globe className="h-5 w-5" />
                Язык и регион
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">Язык</label>
                <select
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                  className="w-full px-3 py-2 bg-card border border-border rounded-lg text-foreground"
                >
                  <option value="ru">Русский</option>
                  <option value="en">English</option>
                </select>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">Часовой пояс</label>
                <select
                  value={timezone}
                  onChange={(e) => setTimezone(e.target.value)}
                  className="w-full px-3 py-2 bg-card border border-border rounded-lg text-foreground"
                >
                  <option value="Europe/Moscow">Москва (UTC+3)</option>
                  <option value="Europe/Kiev">Киев (UTC+2)</option>
                  <option value="Europe/London">Лондон (UTC+0)</option>
                  <option value="America/New_York">Нью-Йорк (UTC-5)</option>
                </select>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">Формат времени</label>
                <div className="flex gap-2">
                  <Button
                    variant={timeFormat === "24" ? "default" : "outline"}
                    onClick={() => setTimeFormat("24")}
                    className="flex-1"
                  >
                    24 часа
                  </Button>
                  <Button
                    variant={timeFormat === "12" ? "default" : "outline"}
                    onClick={() => setTimeFormat("12")}
                    className="flex-1"
                  >
                    12 часов
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

