"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { X, Calendar, Check, ExternalLink, ArrowLeft } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "../../../components/ui/card"
import { Button } from "../../../components/ui/button"

export default function CalendarsPage() {
  const router = useRouter()
  const [googleConnected, setGoogleConnected] = useState(false)
  const [icloudConnected, setIcloudConnected] = useState(false)

  const handleClose = () => {
    router.push("/settings")
  }

  const botUsername = process.env.NEXT_PUBLIC_TELEGRAM_BOT_USERNAME || "tracy_aibot"
  const telegramLink = `https://t.me/${botUsername}`

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
          <h1 className="text-lg font-semibold">Календари</h1>
          <div className="w-5" />
        </div>
      </header>

      <div className="flex-1 overflow-y-auto">
        <div className="container mx-auto max-w-2xl px-4 py-6 space-y-4">
          <Card className="border-border">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calendar className="h-5 w-5" />
                Подключенные календари
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Google Calendar */}
              <div className="p-4 rounded-lg border border-border bg-card">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-lg bg-blue-500 flex items-center justify-center">
                      <span className="text-white font-bold text-sm">G</span>
                    </div>
                    <div>
                      <p className="font-medium">Google Calendar</p>
                      <p className="text-xs text-muted-foreground">
                        {googleConnected ? "Подключен" : "Не подключен"}
                      </p>
                    </div>
                  </div>
                  {googleConnected && (
                    <Check className="h-5 w-5 text-primary" />
                  )}
                </div>
                {!googleConnected && (
                  <div className="space-y-3">
                    <p className="text-sm text-muted-foreground">
                      Подключи Google Calendar для синхронизации событий
                    </p>
                    <a href={telegramLink} target="_blank" rel="noopener noreferrer">
                      <Button className="w-full">
                        Подключить через Telegram
                        <ExternalLink className="ml-2 h-4 w-4" />
                      </Button>
                    </a>
                    <p className="text-xs text-muted-foreground">
                      Открой бота в Telegram и используй команду /settings для подключения
                    </p>
                  </div>
                )}
                {googleConnected && (
                  <Button
                    variant="outline"
                    className="w-full mt-2"
                    onClick={() => setGoogleConnected(false)}
                  >
                    Отключить
                  </Button>
                )}
              </div>

              {/* iCloud Calendar */}
              <div className="p-4 rounded-lg border border-border bg-card">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-lg bg-gray-600 flex items-center justify-center">
                      <span className="text-white font-bold text-sm">i</span>
                    </div>
                    <div>
                      <p className="font-medium">iCloud Calendar</p>
                      <p className="text-xs text-muted-foreground">
                        {icloudConnected ? "Подключен" : "Не подключен"}
                      </p>
                    </div>
                  </div>
                  {icloudConnected && (
                    <Check className="h-5 w-5 text-primary" />
                  )}
                </div>
                {!icloudConnected && (
                  <div className="space-y-3">
                    <p className="text-sm text-muted-foreground">
                      Подключи iCloud Calendar для синхронизации событий
                    </p>
                    <a href={telegramLink} target="_blank" rel="noopener noreferrer">
                      <Button className="w-full">
                        Подключить через Telegram
                        <ExternalLink className="ml-2 h-4 w-4" />
                      </Button>
                    </a>
                    <div className="mt-4 p-3 rounded-lg bg-muted/50 border border-border">
                      <p className="text-xs font-medium mb-2">Инструкция по подключению:</p>
                      <ol className="text-xs text-muted-foreground space-y-1 list-decimal list-inside">
                        <li>Открой бота в Telegram</li>
                        <li>Используй команду /settings</li>
                        <li>Выбери "iCloud Calendar"</li>
                        <li>Следуй инструкциям бота</li>
                        <li>Потребуется App-specific password от Apple</li>
                      </ol>
                    </div>
                  </div>
                )}
                {icloudConnected && (
                  <Button
                    variant="outline"
                    className="w-full mt-2"
                    onClick={() => setIcloudConnected(false)}
                  >
                    Отключить
                  </Button>
                )}
              </div>

              <div className="pt-4 border-t border-border">
                <p className="text-sm text-muted-foreground">
                  Для подключения календарей используй бота в Telegram. Все настройки синхронизируются автоматически.
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

