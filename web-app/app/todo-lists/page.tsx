"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { ArrowLeft, Plus, ListTodo, CheckSquare2, Square, Trash2, Loader2 } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card"
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

export default function TodoListsPage() {
  const router = useRouter()
  const [user, setUser] = useState<any>(null)
  const [lists, setLists] = useState<TodoList[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [newListTitle, setNewListTitle] = useState("")
  const [creating, setCreating] = useState(false)

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
    if (user?.id) {
      loadLists()
    }
  }, [user])

  const loadLists = async () => {
    if (!user?.id) return

    try {
      setLoading(true)
      setError(null)

      const apiBaseUrl = typeof window !== "undefined" && window.location.hostname === "localhost"
        ? "http://localhost:8080"
        : "http://5.35.126.42:8080"

      const response = await fetch(`${apiBaseUrl}/api/todo-lists?user_id=${user.id}`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
        mode: "cors",
      })

      if (!response.ok) {
        throw new Error("Ошибка загрузки списков")
      }

      const data = await response.json()
      setLists(data.lists || [])
    } catch (e: any) {
      console.error("Ошибка загрузки списков:", e)
      setError(e.message || "Не удалось загрузить списки задач")
    } finally {
      setLoading(false)
    }
  }

  const createList = async () => {
    if (!user?.id || !newListTitle.trim()) return

    try {
      setCreating(true)
      setError(null)

      const apiBaseUrl = typeof window !== "undefined" && window.location.hostname === "localhost"
        ? "http://localhost:8080"
        : "http://5.35.126.42:8080"

      const response = await fetch(`${apiBaseUrl}/api/todo-lists`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        mode: "cors",
        body: JSON.stringify({
          user_id: parseInt(user.id),
          title: newListTitle.trim(),
        }),
      })

      if (!response.ok) {
        throw new Error("Ошибка создания списка")
      }

      setNewListTitle("")
      setShowCreateForm(false)
      await loadLists()
    } catch (e: any) {
      console.error("Ошибка создания списка:", e)
      setError(e.message || "Не удалось создать список")
    } finally {
      setCreating(false)
    }
  }

  const handleBack = () => {
    router.push("/assistant")
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
          <div className="flex items-center gap-2">
            <ListTodo className="h-5 w-5 text-primary" />
            <span className="text-sm font-medium">Списки задач</span>
          </div>
          <button
            onClick={() => setShowCreateForm(!showCreateForm)}
            className="text-foreground hover:text-muted-foreground transition-colors"
          >
            <Plus className="h-5 w-5" />
          </button>
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

          {/* Форма создания списка */}
          {showCreateForm && (
            <Card className="mb-4 border-border">
              <CardContent className="pt-6">
                <div className="space-y-4">
                  <Input
                    placeholder="Название списка задач"
                    value={newListTitle}
                    onChange={(e) => setNewListTitle(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !creating) {
                        createList()
                      }
                    }}
                  />
                  <div className="flex gap-2">
                    <Button
                      onClick={createList}
                      disabled={creating || !newListTitle.trim()}
                      className="flex-1"
                    >
                      {creating ? (
                        <>
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                          Создание...
                        </>
                      ) : (
                        "Создать список"
                      )}
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => {
                        setShowCreateForm(false)
                        setNewListTitle("")
                      }}
                    >
                      Отмена
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Список списков задач */}
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : lists.length === 0 ? (
            <Card className="border-border">
              <CardContent className="pt-6">
                <div className="text-center space-y-4">
                  <ListTodo className="h-12 w-12 mx-auto opacity-50 text-muted-foreground" />
                  <p className="text-muted-foreground">У вас пока нет списков задач</p>
                  <Button onClick={() => setShowCreateForm(true)}>
                    <Plus className="h-4 w-4 mr-2" />
                    Создать список задач
                  </Button>
                </div>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {lists.map((list) => (
                <Card
                  key={list.id}
                  className="border-border hover:bg-accent/50 transition-colors cursor-pointer"
                  onClick={() => router.push(`/todo-lists/detail?id=${list.id}`)}
                >
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <h3 className="text-lg font-semibold mb-1">{list.title}</h3>
                        <p className="text-sm text-muted-foreground">
                          {new Date(list.updated_at).toLocaleDateString("ru-RU")}
                        </p>
                      </div>
                      <ListTodo className="h-5 w-5 text-muted-foreground" />
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

