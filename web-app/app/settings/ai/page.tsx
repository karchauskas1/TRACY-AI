"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { X, Brain } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "../../../components/ui/card"
import { Button } from "../../../components/ui/button"

export default function AIPage() {
  const router = useRouter()
  const [model, setModel] = useState("gpt-4o-mini")
  const [interpretationMode, setInterpretationMode] = useState<"strict" | "soft">("soft")

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
            <X className="h-5 w-5" />
          </button>
          <h1 className="text-lg font-semibold">ИИ</h1>
          <div className="w-5" />
        </div>
      </header>

      <div className="flex-1 overflow-y-auto">
        <div className="container mx-auto max-w-2xl px-4 py-6 space-y-4">
          <Card className="border-border">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Brain className="h-5 w-5" />
                Настройки ИИ
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">Модель ИИ</label>
                <select
                  value={model}
                  onChange={(e) => setModel(e.target.value)}
                  className="w-full px-3 py-2 bg-card border border-border rounded-lg text-foreground"
                >
                  <option value="gpt-4o-mini">GPT-4o Mini (быстрая, экономичная)</option>
                  <option value="gpt-4o">GPT-4o (высокое качество)</option>
                  <option value="gpt-4-turbo">GPT-4 Turbo</option>
                  <option value="claude-3-haiku">Claude 3 Haiku</option>
                </select>
                <p className="text-xs text-muted-foreground mt-1">
                  Выберите модель для обработки запросов
                </p>
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">Режим интерпретации</label>
                <div className="space-y-2">
                  <button
                    onClick={() => setInterpretationMode("strict")}
                    className={`w-full p-3 rounded-lg border text-left transition-colors ${
                      interpretationMode === "strict"
                        ? "border-primary bg-primary/10"
                        : "border-border hover:bg-accent/50"
                    }`}
                  >
                    <p className="font-medium">Строгий</p>
                    <p className="text-xs text-muted-foreground mt-1">
                      Точное следование инструкциям, меньше предположений
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
                    <p className="font-medium">Мягкий</p>
                    <p className="text-xs text-muted-foreground mt-1">
                      Гибкая интерпретация, больше предположений и контекста
                    </p>
                  </button>
                </div>
              </div>

              <div className="pt-4 border-t border-border">
                <p className="text-sm text-muted-foreground">
                  API ключ OpenRouter настраивается на сервере бота
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

