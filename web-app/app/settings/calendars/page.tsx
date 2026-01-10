"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Calendar, Check, ArrowLeft, ChevronDown, ChevronUp } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "../../../components/ui/card"
import { Button } from "../../../components/ui/button"
import { useLocale } from "../../../lib/locale-context"

export default function CalendarsPage() {
  const router = useRouter()
  const { t } = useLocale()
  const [googleConnected, setGoogleConnected] = useState(false)
  const [icloudConnected, setIcloudConnected] = useState(false)
  const [googleInstructionsOpen, setGoogleInstructionsOpen] = useState(false)
  const [icloudInstructionsOpen, setIcloudInstructionsOpen] = useState(false)

  useEffect(() => {
    // Try to get calendar status from Telegram Web App data
    if (typeof window !== "undefined") {
      const tg = (window as any).Telegram?.WebApp
      if (tg && tg.initDataUnsafe?.user) {
        // Request calendar status from bot
        tg.sendData(JSON.stringify({
          action: "get_calendar_status"
        }))
        
        // Check for calendar status in localStorage periodically
        // Bot will send status in format TRACY_CALENDAR_STATUS:{base64_json}
        // We need to parse messages from bot and update localStorage
        const checkStatus = () => {
          const savedStatus = localStorage.getItem("tracy_calendar_status")
          if (savedStatus) {
            try {
              const status = JSON.parse(savedStatus)
              setGoogleConnected(status.google || false)
              setIcloudConnected(status.icloud || false)
            } catch (e) {
              console.error("Error parsing calendar status:", e)
            }
          } else {
            // If no saved status, request from bot
            tg.sendData(JSON.stringify({
              action: "get_calendar_status"
            }))
          }
        }
        
        // Check immediately
        checkStatus()
        
        // Check periodically
        const interval = setInterval(checkStatus, 5000)
        
        return () => clearInterval(interval)
      }
    }
  }, [])

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
          <h1 className="text-lg font-semibold">Подключенные календари</h1>
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
                      Подключи Google Calendar для синхронизации событий через бота в Telegram
                    </p>
                    <Button
                      className="w-full"
                      variant="outline"
                      onClick={() => setGoogleInstructionsOpen(!googleInstructionsOpen)}
                    >
                      {googleInstructionsOpen ? (
                        <>
                          Скрыть инструкцию
                          <ChevronUp className="ml-2 h-4 w-4" />
                        </>
                      ) : (
                        <>
                          Показать инструкцию по подключению
                          <ChevronDown className="ml-2 h-4 w-4" />
                        </>
                      )}
                    </Button>
                    {googleInstructionsOpen && (
                      <div className="mt-4 p-4 rounded-lg bg-muted/50 border border-border">
                        <p className="text-sm font-medium mb-3">📋 Инструкция по подключению Google Calendar:</p>
                        <ol className="text-sm text-muted-foreground space-y-2 list-decimal list-inside">
                          <li>Открой бота в Telegram и перейди в /settings или нажми кнопку "Настройки"</li>
                          <li>Выбери "Google Calendar"</li>
                          <li>Следуй инструкциям бота — откроется страница авторизации Google</li>
                          <li>Войди в свой Google аккаунт и разреши доступ TRACY к календарю</li>
                          <li>Если видишь "Access blocked" — это нормально:
                            <ul className="list-disc list-inside ml-4 mt-1 space-y-1">
                              <li>Скопируй весь URL из адресной строки браузера</li>
                              <li>Отправь этот URL боту в Telegram</li>
                              <li>Бот обработает URL и завершит подключение</li>
                            </ul>
                          </li>
                          <li>После успешного подключения все события будут синхронизироваться автоматически</li>
                        </ol>
                      </div>
                    )}
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
                      Подключи iCloud Calendar для синхронизации событий через бота в Telegram
                    </p>
                    <Button
                      className="w-full"
                      variant="outline"
                      onClick={() => setIcloudInstructionsOpen(!icloudInstructionsOpen)}
                    >
                      {icloudInstructionsOpen ? (
                        <>
                          Скрыть инструкцию
                          <ChevronUp className="ml-2 h-4 w-4" />
                        </>
                      ) : (
                        <>
                          Показать инструкцию по подключению
                          <ChevronDown className="ml-2 h-4 w-4" />
                        </>
                      )}
                    </Button>
                    {icloudInstructionsOpen && (
                      <div className="mt-4 p-4 rounded-lg bg-muted/50 border border-border">
                        <p className="text-sm font-medium mb-3">📋 Инструкция по подключению iCloud Calendar:</p>
                        <ol className="text-sm text-muted-foreground space-y-2 list-decimal list-inside">
                          <li>Открой бота в Telegram и перейди в /settings или нажми кнопку "Настройки"</li>
                          <li>Выбери "iCloud Calendar"</li>
                          <li>Следуй пошаговым инструкциям бота</li>
                          <li>Перейди на <strong>appleid.apple.com</strong> в раздел <strong>"Безопасность"</strong></li>
                          <li>Убедись, что включена <strong>двухфакторная аутентификация</strong></li>
                          <li>Создай <strong>App-Specific Password</strong> (Пароль для приложения):
                            <ul className="list-disc list-inside ml-4 mt-1 space-y-1">
                              <li>В разделе "Пароли приложений" нажми "Создать пароль..."</li>
                              <li>Введи название: <strong>"TRACY Bot"</strong></li>
                              <li>Скопируй созданный пароль (формат: xxxx-xxxx-xxxx-xxxx)</li>
                              <li>⚠️ Пароль показывается только один раз!</li>
                            </ul>
                          </li>
                          <li>Вернись в бота и отправь:
                            <ul className="list-disc list-inside ml-4 mt-1 space-y-1">
                              <li>Сначала свой Apple ID (email)</li>
                              <li>Затем созданный App-Specific Password</li>
                            </ul>
                          </li>
                          <li>После успешного подключения все события будут синхронизироваться автоматически</li>
                        </ol>
                      </div>
                    )}
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

            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

