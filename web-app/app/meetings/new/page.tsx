"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { ArrowLeft, Upload, FileAudio, Mic } from "lucide-react"
import Link from "next/link"
import { Card, CardContent, CardHeader, CardTitle } from "../../../components/ui/card"
import { Button } from "../../../components/ui/button"

export default function NewMeetingPage() {
  const router = useRouter()
  const [isDragging, setIsDragging] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    
    const file = e.dataTransfer.files[0]
    if (file && file.type.startsWith('audio/')) {
      setSelectedFile(file)
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file && file.type.startsWith('audio/')) {
      setSelectedFile(file)
    }
  }

  const handleSubmit = async () => {
    if (!selectedFile) return
    
    setIsProcessing(true)
    
    // Получаем username бота из переменных окружения
    const botUsername = process.env.NEXT_PUBLIC_TELEGRAM_BOT_USERNAME || "tracy_aibot"
    
    // Если открыто через Telegram Web App, открываем чат с ботом
    if (typeof window !== "undefined" && (window as any).Telegram?.WebApp) {
      const tg = (window as any).Telegram.WebApp
      // Telegram WebApp уже инициализирован через TelegramBootstrap
      
      // Открываем чат с ботом через deep link для расшифровки встречи
      tg.openTelegramLink(`https://t.me/${botUsername}?start=meeting_transcribe`)
      
      // Закрываем веб-приложение после небольшой задержки
      setTimeout(() => {
        tg.close()
      }, 500)
    } else {
      // Если не через Telegram Web App, открываем ссылку на бота
      const telegramLink = `https://t.me/${botUsername}?start=meeting_transcribe`
      window.open(telegramLink, '_blank')
      
      alert(
        "В открывшемся чате отправь аудиофайл боту.\n\n" +
        "Бот автоматически создаст расшифровку с тайм-кодами и структурированное резюме."
      )
    }
    
    setIsProcessing(false)
  }

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      <header className="sticky top-0 z-20 border-b border-border bg-background/95 backdrop-blur">
        <div className="flex h-14 items-center justify-between px-4">
          <Link href="/assistant">
            <button className="text-foreground hover:text-muted-foreground transition-colors">
              <ArrowLeft className="h-5 w-5" />
            </button>
          </Link>
          <h1 className="text-lg font-semibold">Расшифровать встречу</h1>
          <div className="w-5" />
        </div>
      </header>

      <div className="flex-1 overflow-y-auto">
        <div className="container mx-auto max-w-2xl px-4 py-6">
          <Card className="border-border">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Mic className="h-5 w-5 text-primary" />
                Загрузить аудио встречи
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-muted-foreground">
                Поддерживаемые форматы: MP3, M4A, WAV, OGG. Максимальный размер: 25 МБ.
              </p>

              {/* Drag & Drop Zone */}
              <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
                  isDragging
                    ? "border-primary bg-primary/10"
                    : "border-border hover:border-primary/50"
                }`}
              >
                {selectedFile ? (
                  <div className="space-y-4">
                    <FileAudio className="h-12 w-12 mx-auto text-primary" />
                    <div>
                      <p className="font-medium">{selectedFile.name}</p>
                      <p className="text-sm text-muted-foreground">
                        {(selectedFile.size / 1024 / 1024).toFixed(2)} МБ
                      </p>
                    </div>
                    <Button
                      variant="outline"
                      onClick={() => setSelectedFile(null)}
                    >
                      Выбрать другой файл
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <Upload className="h-12 w-12 mx-auto text-muted-foreground" />
                    <div>
                      <p className="font-medium mb-2">
                        Перетащите аудиофайл сюда
                      </p>
                      <p className="text-sm text-muted-foreground mb-4">
                        или
                      </p>
                      <label className="inline-block">
                        <input
                          type="file"
                          accept="audio/*"
                          onChange={handleFileSelect}
                          className="hidden"
                        />
                        <span className="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 border border-input bg-background hover:bg-accent hover:text-accent-foreground h-10 px-4 py-2 cursor-pointer">
                          Выбрать файл
                        </span>
                      </label>
                    </div>
                  </div>
                )}
              </div>

              {/* Submit Button */}
              {selectedFile && (
                <div className="space-y-2">
                  <Button
                    className="w-full"
                    size="lg"
                    onClick={handleSubmit}
                    disabled={isProcessing}
                  >
                    {isProcessing ? "Обработка..." : "Открыть бота для расшифровки"}
                  </Button>
                  <p className="text-xs text-muted-foreground text-center">
                    После нажатия откроется чат с ботом. Отправь файл боту для расшифровки.
                  </p>
                </div>
              )}

              {/* Info Box */}
              <div className="mt-6 p-4 bg-muted/50 rounded-lg space-y-3">
                <p className="text-sm text-muted-foreground mb-2">
                  💡 <strong>Как это работает:</strong>
                </p>
                <ol className="text-sm text-muted-foreground space-y-2 list-decimal list-inside ml-2">
                  <li>Загрузи аудиофайл выше или выбери файл (MP3, M4A, WAV, OGG)</li>
                  <li>Нажми кнопку "Открыть бота для расшифровки"</li>
                  <li>В открывшемся чате отправь боту голосовое сообщение или аудиофайл</li>
                  <li>Бот автоматически создаст расшифровку с тайм-кодами и структурированное резюме</li>
                </ol>
                <p className="text-xs text-muted-foreground pt-2 border-t border-border">
                  📝 <strong>Примечание:</strong> Файл не загружается автоматически. После открытия чата отправь файл боту вручную.
                </p>
              </div>
              
              {/* Alternative Method */}
              <div className="p-4 bg-primary/5 rounded-lg border border-primary/20">
                <p className="text-sm font-medium mb-2">
                  🚀 Быстрый способ:
                </p>
                <p className="text-sm text-muted-foreground mb-3">
                  Просто открой бота в Telegram и отправь ему голосовое сообщение или аудиофайл. 
                  Бот автоматически распознает, что это встреча, и создаст расшифровку.
                </p>
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={() => {
                    const botUsername = process.env.NEXT_PUBLIC_TELEGRAM_BOT_USERNAME || "tracy_aibot"
                    if (typeof window !== "undefined" && (window as any).Telegram?.WebApp) {
                      const tg = (window as any).Telegram.WebApp
                      // Telegram WebApp уже инициализирован через TelegramBootstrap
                      tg.openTelegramLink(`https://t.me/${botUsername}`)
                    } else {
                      window.open(`https://t.me/${botUsername}`, '_blank')
                    }
                  }}
                >
                  Открыть бота напрямую
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

