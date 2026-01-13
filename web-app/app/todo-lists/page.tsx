"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { ArrowLeft, Plus, ListTodo, CheckSquare2, Square, Trash2, Loader2 } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card"
import { Button } from "../../components/ui/button"
import { Input } from "../../components/ui/input"
import { apiGet, apiPost, formatApiError, type ApiError } from "../../lib/apiClient"
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

export default function TodoListsPage() {
  const router = useRouter()
  const { user, userId, isLoading: userLoading, error: userError } = useTelegramUser()
  const [lists, setLists] = useState<TodoList[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [newListTitle, setNewListTitle] = useState("")
  const [creating, setCreating] = useState(false)

  useEffect(() => {
    // Загружаем списки только после получения user_id
    if (!userLoading && userId) {
      loadLists()
    } else if (!userLoading && !userId) {
      // Если user_id не получен, показываем ошибку
      if (userError) {
        setError(userError)
      } else {
        setError("Не удалось определить ID пользователя. Откройте приложение через Telegram.")
      }
      setLoading(false)
    }
  }, [userId, userLoading, userError])

  const loadLists = async () => {
    // Ждем, пока user_id будет получен
    if (userLoading) {
      console.log("[TodoLists] Ожидание user_id...")
      return
    }
    
    if (!userId || userId === "demo" || userId === "undefined" || userId === "null") {
      console.error("[TodoLists] ❌ User ID не найден или невалиден:", userId)
      if (userError) {
        setError(userError)
      } else {
        const errorMessage = userId === "demo" 
          ? "Демо-режим не поддерживает загрузку списков задач. Откройте приложение через Telegram."
          : "Не удалось определить ID пользователя. Откройте приложение через Telegram."
        setError(errorMessage)
      }
      setLoading(false)
      return
    }
    
    try {
      setLoading(true)
      setError(null)

      const data = await apiGet<{ success?: boolean; lists?: TodoList[]; error?: string }>(
        `/api/todo-lists`,
        { user_id: parseInt(userId) },
        { timeout: 15000 }
      )
      
      // Обрабатываем разные форматы ответа
      let listsArray: TodoList[] = []
      if (data.success && Array.isArray(data.lists)) {
        listsArray = data.lists
      } else if (Array.isArray(data.lists)) {
        listsArray = data.lists
      } else if (data.error) {
        throw new Error(data.error)
      }
      
      console.log(`[TodoLists] ✅ Загружено ${listsArray.length} списков`)
      setLists(listsArray)
      setError(null)
      setLoading(false)
      
    } catch (e: any) {
      console.error("[TodoLists] Ошибка загрузки списков:", e)
      
      // Показываем конкретную ошибку
      const errorMessage = e.type 
        ? formatApiError(e)
        : (e.message || "Не удалось загрузить списки задач")
      
      setError(errorMessage)
      setLoading(false)
    }
  }

  const createList = async () => {
    if (!newListTitle.trim() || !userId) return

    try {
      setCreating(true)
      setError(null)

      const result = await apiPost<{ success?: boolean; list?: TodoList; error?: string }>(
        `/api/todo-lists`,
        {
          user_id: parseInt(userId),
          title: newListTitle.trim(),
        },
        { timeout: 15000 }
      )

      if (result.success && result.list) {
        setNewListTitle("")
        setShowCreateForm(false)
        await loadLists()
      } else if (result.error) {
        setError(result.error)
      } else {
        // Если нет ошибки, но и нет success, все равно обновляем список
        setNewListTitle("")
        setShowCreateForm(false)
        await loadLists()
      }
    } catch (e: any) {
      console.error("Ошибка создания списка:", e)
      const errorMessage = e.type 
        ? formatApiError(e)
        : (e.message || "Не удалось создать список")
      setError(errorMessage)
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
                  <span className="ml-2 text-sm text-muted-foreground">Загрузка...</span>
                </div>
              ) : error ? (
                <Card className="border-destructive">
                  <CardContent className="pt-6">
                    <div className="text-center space-y-4">
                      <p className="text-destructive font-semibold">Ошибка загрузки</p>
                      <p className="text-sm text-muted-foreground">{error}</p>
                      <Button onClick={loadLists} variant="outline">
                        Попробовать снова
                      </Button>
                    </div>
                  </CardContent>
                </Card>
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

