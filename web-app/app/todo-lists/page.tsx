"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { ArrowLeft, Plus, ListTodo, CheckSquare2, Square, Trash2, Loader2 } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card"
import { Button } from "../../components/ui/button"
import { Input } from "../../components/ui/input"
import { apiGet, apiPost, apiDelete, formatApiError, type ApiError } from "../../lib/apiClient"
import { useTelegramUser } from "../../lib/useTelegramUser"
import { useNavigation } from "../../lib/useNavigation"
import { useToast } from "../../hooks/use-toast"

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
  const { handleBack } = useNavigation()
  const { toast } = useToast()
  const { user, userId, isLoading: userLoading, error: userError } = useTelegramUser()
  const [lists, setLists] = useState<TodoList[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [newListTitle, setNewListTitle] = useState("")
  const [creating, setCreating] = useState(false)
  const [deleteConfirmId, setDeleteConfirmId] = useState<number | null>(null)
  const [deleting, setDeleting] = useState<number | null>(null)

  useEffect(() => {
    // Если пользователь не авторизован, перенаправляем на логин
    if (!userLoading && !userId) {
      router.push("/login")
      return
    }

    // Загружаем списки только после получения user_id
    if (!userLoading && userId) {
      loadLists()
    }
  }, [userId, userLoading, router])

  const loadLists = async (forceFresh: boolean = false) => {
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
        { timeout: 15000, noCache: forceFresh }
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
        await loadLists(true)
      } else if (result.error) {
        setError(result.error)
      } else {
        // Если нет ошибки, но и нет success, все равно обновляем список
        setNewListTitle("")
        setShowCreateForm(false)
        await loadLists(true)
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

  const deleteList = async (listId: number) => {
    // Открываем нижнюю панель подтверждения
    setDeleteConfirmId(listId)
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
                      <Button onClick={() => loadLists(true)} variant="outline">
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
                  className="border-border hover:bg-accent/50 transition-colors"
                >
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                      <Link
                        href={`/todo-lists/detail?id=${list.id}`}
                        className="flex-1"
                      >
                        <h3 className="text-lg font-semibold mb-1">{list.title}</h3>
                        <p className="text-sm text-muted-foreground">
                          {new Date(list.updated_at).toLocaleDateString("ru-RU")}
                        </p>
                      </Link>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={(e) => {
                            e.preventDefault()
                            e.stopPropagation()
                            deleteList(list.id)
                          }}
                          disabled={deleting === list.id}
                          className="text-destructive hover:text-destructive/80 transition-colors p-1"
                          title="Удалить список"
                        >
                          {deleting === list.id ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <Trash2 className="h-4 w-4" />
                          )}
                        </button>
                        <ListTodo className="h-5 w-5 text-muted-foreground" />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Bottom delete confirmation */}
      {deleteConfirmId !== null && (
        <div className="fixed left-0 right-0 bottom-0 z-30 border-t border-border bg-background/95 backdrop-blur">
          <div className="container mx-auto max-w-2xl px-4 py-3 flex items-center justify-between gap-3">
            <div className="text-sm">
              <div className="font-medium">Удалить список?</div>
              <div className="text-muted-foreground">Это действие нельзя отменить.</div>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                onClick={() => setDeleteConfirmId(null)}
                disabled={deleting !== null}
              >
                Отмена
              </Button>
              <Button
                variant="destructive"
                onClick={async () => {
                  const listId = deleteConfirmId
                  if (listId === null) return
                  try {
                    setDeleting(listId)
                    setError(null)
                    await apiDelete(`/api/todo-lists/${listId}?user_id=${parseInt(userId!)}`, { timeout: 15000 })
                    await loadLists(true)
                    setDeleteConfirmId(null)
                    toast({
                      title: "Список удален",
                      description: "Список задач успешно удален",
                    })
                  } catch (e: any) {
                    console.error("Ошибка удаления списка:", e)
                    const errorMessage = e.type ? formatApiError(e) : (e.message || "Не удалось удалить список")
                    setError(errorMessage)
                    toast({
                      title: "Ошибка",
                      description: errorMessage,
                      variant: "destructive",
                    })
                  } finally {
                    setDeleting(null)
                  }
                }}
                disabled={deleting !== null}
              >
                Удалить
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

