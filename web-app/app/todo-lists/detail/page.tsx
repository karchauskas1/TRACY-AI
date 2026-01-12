"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { TodoListDetailClient } from "../TodoListDetailClient"

export default function TodoListDetailPage() {
  const router = useRouter()
  const [listId, setListId] = useState<number | null>(null)

  useEffect(() => {
    // Получаем ID из query параметров
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search)
      const listIdStr = params.get("id")
      setListId(listIdStr ? parseInt(listIdStr) : null)
    }
  }, [])

  if (!listId) {
    return (
      <div className="min-h-screen bg-background text-foreground flex items-center justify-center">
        <div className="text-center">
          <p className="text-destructive">Неверный ID списка</p>
          <button
            onClick={() => router.push("/todo-lists")}
            className="mt-4 text-primary hover:underline"
          >
            Вернуться к спискам
          </button>
        </div>
      </div>
    )
  }

  return <TodoListDetailClient listId={listId} />
}

