"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { FileAudio, History } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card"
import { Button } from "../../components/ui/button"

export function MeetingsPageClient() {
  const router = useRouter()

  return (
    <div className="container mx-auto max-w-4xl px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-semibold">Встречи и резюме</h1>
        <p className="mt-2 text-muted-foreground">
          Загрузите аудио встречи для создания резюме
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card className="cursor-pointer hover:bg-accent transition-colors" onClick={() => router.push("/meetings/new")}>
          <CardHeader>
            <CardTitle className="flex items-center gap-3">
              <FileAudio className="h-6 w-6" />
              Сделать резюме встречи
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Загрузите аудиозапись встречи для автоматического создания резюме
            </p>
          </CardContent>
        </Card>

        <Card className="cursor-pointer hover:bg-accent transition-colors" onClick={() => router.push("/meetings/history")}>
          <CardHeader>
            <CardTitle className="flex items-center gap-3">
              <History className="h-6 w-6" />
              История
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Просмотрите ранее обработанные встречи
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

