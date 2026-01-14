"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { useNavigation } from "../../lib/useNavigation"
import { ArrowLeft, Plus, Trash2, CheckSquare2, Square, Loader2 } from "lucide-react"
import { Card, CardContent } from "../../components/ui/card"
import { Button } from "../../components/ui/button"
import { Input } from "../../components/ui/input"
import { apiDelete, apiGet, apiPost, apiPut, formatApiError } from "../../lib/apiClient"
import { useTelegramUser } from "../../lib/useTelegramUser"

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
  const { handleBack } = useNavigation()
  const { userId, isLoading: userLoading } = useTelegramUser()

  const [list, setList] = useState<TodoList | null>(null)
  const [items, setItems] = useState<TodoItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [newItemText, setNewItemText] = useState("")
  const [creating, setCreating] = useState(false)
  const [updating, setUpdating] = useState<number | null>(null)
  const [deleting, setDeleting] = useState<number | null>(null)

  useEffect(() => {
    // Если пользователь не авторизован, перенаправляем на логин
    if (!userLoading && !userId) {
      router.push("/login")
    }
  }, [userLoading, userId, router])

  useEffect(() => {
    if (!userLoading && userId && listId) {
      loadList(true)
    }
  }, [])

  useEffect(() => {
    if (!userLoading && userId && listId) {
      loadList()
    }
  }, [userLoading, userId, listId])

  const loadList = async (forceFresh: boolean = false) => {
    if (!userId || !listId) return

    try {
      setLoading(true)
      setError(null)
      const data = await apiGet<{ success?: boolean; list?: TodoList; items?: TodoItem[]; error?: string }>(
        `/api/todo-lists/${listId}`,
        { user_id: parseInt(userId) },
        { timeout: 15000, noCache: forceFresh }
      )

      if (data.success && data.list) {
        setList(data.list)
        setItems(data.items || [])
      } else if (data.error) {
        throw new Error(data.error)
      } else if (data.list) {
        setList(data.list)
        setItems(data.items || [])
      } else {
        throw new Error("Список задач не найден")
      }
    } catch (e: any) {
      console.error("Ошибка загрузки списка:", e)
      const msg = e.type ? formatApiError(e) : (e.message || "Не удалось загрузить список задач")
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  const createItem = async () => {
    if (!listId || !newItemText.trim()) return

    try {
      setCreating(true)
      setError(null)
      const res = await apiPost<{ success?: boolean; item_id?: number; error?: string }>(
        `/api/todo-lists/${listId}/items`,
        { text: newItemText.trim() },
        { timeout: 15000 }
      )
      if (res.success === false && res.error) throw new Error(res.error)

      setNewItemText("")
      await loadList(true)
    } catch (e: any) {
      console.error("Ошибка создания задачи:", e)
      const msg = e.type ? formatApiError(e) : (e.message || "Не удалось создать задачу")
      setError(msg)
    } finally {
      setCreating(false)
    }
  }

  const toggleItem = async (itemId: number, currentCompleted: boolean) => {
    try {
      setUpdating(itemId)
      setError(null)
      const res = await apiPut<{ success?: boolean; error?: string }>(
        `/api/todo-items/${itemId}`,
        { completed: !currentCompleted },
        { timeout: 15000 }
      )
      if (res.success === false && res.error) throw new Error(res.error)
      await loadList(true)
    } catch (e: any) {
      console.error("Ошибка обновления задачи:", e)
      const msg = e.type ? formatApiError(e) : (e.message || "Не удалось обновить задачу")
      setError(msg)
    } finally {
      setUpdating(null)
    }
  }

  const deleteItem = async (itemId: number) => {
    try {
      setDeleting(itemId)
      setError(null)
      await apiDelete(`/api/todo-items/${itemId}`, { timeout: 15000 })
      await loadList(true)
    } catch (e: any) {
      console.error("Ошибка удаления задачи:", e)
      const msg = e.type ? formatApiError(e) : (e.message || "Не удалось удалить задачу")
      setError(msg)
    } finally {
      setDeleting(null)
    }
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

