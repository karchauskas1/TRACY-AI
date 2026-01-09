"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { FileAudio, History, X, ArrowLeft } from "lucide-react"
import Link from "next/link"
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card"
import { Button } from "../../components/ui/button"

export function MeetingsPageClient() {
  const router = useRouter()

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      <header className="sticky top-0 z-20 border-b border-border bg-background/95 backdrop-blur">
        <div className="flex h-14 items-center justify-between px-4">
          <Link href="/assistant">
            <button className="text-foreground hover:text-muted-foreground transition-colors">
              <ArrowLeft className="h-5 w-5" />
            </button>
          </Link>
          <h1 className="text-lg font-semibold">ИИ транскрибатор</h1>
          <div className="w-5" />
        </div>
      </header>

      <div className="flex-1 overflow-y-auto">
        <div className="container mx-auto max-w-4xl px-4 py-6">
          <div className="mb-6">
            <h1 className="text-3xl font-semibold mb-2">ИИ транскрибатор</h1>
            <p className="text-muted-foreground">
              Расшифровка и анализ аудиозаписей встреч с помощью искусственного интеллекта
            </p>
          </div>

          <div className="space-y-4">
            <Card className="border-border hover:bg-accent/50 transition-colors cursor-pointer" onClick={() => router.push("/meetings/new")}>
              <CardHeader>
                <CardTitle className="flex items-center gap-3">
                  <FileAudio className="h-6 w-6 text-primary" />
                  Расшифровать встречу
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground mb-4">
                  Загрузите аудиозапись встречи для автоматического создания расшифровки с тайм-кодами и структурированного резюме
                </p>
                <Button className="w-full" onClick={() => router.push("/meetings/new")}>
                  <FileAudio className="mr-2 h-4 w-4" />
                  Начать расшифровку
                </Button>
              </CardContent>
            </Card>

            <Card className="border-border hover:bg-accent/50 transition-colors cursor-pointer" onClick={() => router.push("/meetings/history")}>
              <CardHeader>
                <CardTitle className="flex items-center gap-3">
                  <History className="h-6 w-6 text-primary" />
                  История расшифровок
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground mb-4">
                  Просмотрите ранее обработанные встречи, их расшифровки и резюме
                </p>
                <Button variant="outline" className="w-full" onClick={() => router.push("/meetings/history")}>
                  <History className="mr-2 h-4 w-4" />
                  Открыть историю
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}

