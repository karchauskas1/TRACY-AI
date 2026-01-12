"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { ArrowLeft, Plus, Trash2, CheckSquare2, Square, Loader2 } from "lucide-react"
import { Card, CardContent } from "../../components/ui/card"
import { Button } from "../../components/ui/button"
import { Input } from "../../components/ui/input"

interface TodoList {
  id: number
  user_id: number
  title: string
  created_at: string
  updated_at: string
}

interface TodoItem {
  id: number
  list_id: number
  text: string
  completed: boolean
  created_at: string
  updated_at: string
}

interface TodoListDetailClientProps {
  listId: number
}

export function TodoListDetailClient({ listId }: TodoListDetailClientProps) {
  const router = useRouter()

  const [user, setUser] = useState<any>(null)
  const [list, setList] = useState<TodoList | null>(null)
  const [items, setItems] = useState<TodoItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [newItemText, setNewItemText] = useState("")
  const [creating, setCreating] = useState(false)
  const [updating, setUpdating] = useState<number | null>(null)
  const [deleting, setDeleting] = useState<number | null>(null)

  useEffect(() => {
    // Загружаем данные пользователя
    if (typeof window !== "undefined") {
      const tg = (window as any).Telegram?.WebApp
      if (tg) {
        tg.ready()
        const tgUser = tg.initDataUnsafe?.user
        if (tgUser) {
          setUser({
            id: tgUser.id.toString(),
            first_name: tgUser.first_name,
            last_name: tgUser.last_name,
          })
        }
      } else {
        const savedUser = localStorage.getItem("telegram_user")
        if (savedUser) {
          try {
            const parsed = JSON.parse(savedUser)
            setUser({
              id: parsed.id?.toString(),
              first_name: parsed.first_name,
              last_name: parsed.last_name,
            })
          } catch (e) {
            console.error("Failed to parse user:", e)
          }
        }
      }
    }
  }, [])

  useEffect(() => {
    if (user?.id && listId) {
      loadList()
    }
  }, [user, listId])

  const loadList = async () => {
    if (!user?.id || !listId) return

    try {
      setLoading(true)
      setError(null)

      const apiBaseUrl = typeof window !== "undefined" && window.location.hostname === "localhost"
        ? "http://localhost:8080"
        : "http://5.35.126.42:8080"

      const response = await fetch(`${apiBaseUrl}/api/todo-lists/${listId}?user_id=${user.id}`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
        mode: "cors",
      })

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error("Список задач не найден")
        }
        throw new Error("Ошибка загрузки списка")
      }

      const data = await response.json()
      setList(data.list)
      setItems(data.items || [])
    } catch (e: any) {
      console.error("Ошибка загрузки списка:", e)
      setError(e.message || "Не удалось загрузить список задач")
    } finally {
      setLoading(false)
    }
  }

  const createItem = async () => {
    if (!listId || !newItemText.trim()) return

    try {
      setCreating(true)
      setError(null)

      const apiBaseUrl = typeof window !== "undefined" && window.location.hostname === "localhost"
        ? "http://localhost:8080"
        : "http://5.35.126.42:8080"

      const response = await fetch(`${apiBaseUrl}/api/todo-lists/${listId}/items`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        mode: "cors",
        body: JSON.stringify({
          text: newItemText.trim(),
        }),
      })

      if (!response.ok) {
        throw new Error("Ошибка создания задачи")
      }

      setNewItemText("")
      await loadList()
    } catch (e: any) {
      console.error("Ошибка создания задачи:", e)
      setError(e.message || "Не удалось создать задачу")
    } finally {
      setCreating(false)
    }
  }

  const toggleItem = async (itemId: number, currentCompleted: boolean) => {
    try {
      setUpdating(itemId)
      setError(null)

      const apiBaseUrl = typeof window !== "undefined" && window.location.hostname === "localhost"
        ? "http://localhost:8080"
        : "http://5.35.126.42:8080"

      const response = await fetch(`${apiBaseUrl}/api/todo-items/${itemId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        mode: "cors",
        body: JSON.stringify({
          completed: !currentCompleted,
        }),
      })

      if (!response.ok) {
        throw new Error("Ошибка обновления задачи")
      }

      await loadList()
    } catch (e: any) {
      console.error("Ошибка обновления задачи:", e)
      setError(e.message || "Не удалось обновить задачу")
    } finally {
      setUpdating(null)
    }
  }

  const deleteItem = async (itemId: number) => {
    try {
      setDeleting(itemId)
      setError(null)

      const apiBaseUrl = typeof window !== "undefined" && window.location.hostname === "localhost"
        ? "http://localhost:8080"
        : "http://5.35.126.42:8080"

      const response = await fetch(`${apiBaseUrl}/api/todo-items/${itemId}`, {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
        },
        mode: "cors",
      })

      if (!response.ok) {
        throw new Error("Ошибка удаления задачи")
      }

      await loadList()
    } catch (e: any) {
      console.error("Ошибка удаления задачи:", e)
      setError(e.message || "Не удалось удалить задачу")
    } finally {
      setDeleting(null)
    }
  }

  const handleBack = () => {
    router.push("/todo-lists")
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-background text-foreground flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (error && !list) {
    return (
      <div className="min-h-screen bg-background text-foreground flex flex-col">
        <header className="sticky top-0 z-20 border-b border-border bg-background/95 backdrop-blur">
          <div className="flex h-14 items-center px-4">
            <button
              onClick={handleBack}
              className="text-foreground hover:text-muted-foreground transition-colors"
            >
              <ArrowLeft className="h-5 w-5" />
            </button>
          </div>
        </header>
        <div className="flex-1 flex items-center justify-center p-4">
          <Card className="border-destructive">
            <CardContent className="pt-6">
              <p className="text-sm text-destructive">{error}</p>
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      {/* Header */}
      <header className="sticky top-0 z-20 border-b border-border bg-background/95 backdrop-blur">
        <div className="flex h-14 items-center justify-between px-4">
          <button
            onClick={handleBack}
            className="text-foreground hover:text-muted-foreground transition-colors"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <span className="text-sm font-medium">{list?.title || "Список задач"}</span>
          <div className="w-5" /> {/* Spacer */}
        </div>
      </header>

      <div className="flex-1 overflow-y-auto">
        <div className="container mx-auto max-w-2xl px-4 py-6">
          {error && (
            <Card className="mb-4 border-destructive">
              <CardContent className="pt-6">
                <p className="text-sm text-destructive">{error}</p>
              </CardContent>
            </Card>
          )}

          {/* Форма добавления задачи */}
          <Card className="mb-4 border-border">
            <CardContent className="pt-6">
              <div className="flex gap-2">
                <Input
                  placeholder="Новая задача..."
                  value={newItemText}
                  onChange={(e) => setNewItemText(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !creating) {
                      createItem()
                    }
                  }}
                  className="flex-1"
                />
                <Button
                  onClick={createItem}
                  disabled={creating || !newItemText.trim()}
                >
                  {creating ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Plus className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Список задач */}
          {items.length === 0 ? (
            <Card className="border-border">
              <CardContent className="pt-6">
                <div className="text-center space-y-4">
                  <CheckSquare2 className="h-12 w-12 mx-auto opacity-50 text-muted-foreground" />
                  <p className="text-muted-foreground">У вас пока нет задач</p>
                </div>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-2">
              {items.map((item) => (
                <Card
                  key={item.id}
                  className="border-border"
                >
                  <CardContent className="pt-6">
                    <div className="flex items-start gap-3">
                      <button
                        onClick={() => toggleItem(item.id, item.completed)}
                        disabled={updating === item.id}
                        className="mt-0.5"
                      >
                        {updating === item.id ? (
                          <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
                        ) : item.completed ? (
                          <CheckSquare2 className="h-5 w-5 text-primary" />
                        ) : (
                          <Square className="h-5 w-5 text-muted-foreground" />
                        )}
                      </button>
                      <div className="flex-1">
                        <p className={item.completed ? "line-through text-muted-foreground" : ""}>
                          {item.text}
                        </p>
                      </div>
                      <button
                        onClick={() => deleteItem(item.id)}
                        disabled={deleting === item.id}
                        className="text-destructive hover:text-destructive/80 transition-colors"
                      >
                        {deleting === item.id ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <Trash2 className="h-4 w-4" />
                        )}
                      </button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

