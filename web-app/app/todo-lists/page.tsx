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
    // Получаем user_id из разных источников
    let userId: string | null = null
    
    if (user?.id) {
      userId = user.id.toString()
    } else if (typeof window !== "undefined") {
      const tg = (window as any).Telegram?.WebApp
      if (tg?.initDataUnsafe?.user?.id) {
        userId = tg.initDataUnsafe.user.id.toString()
        // Сохраняем user для будущего использования
        if (!user) {
          setUser({
            id: userId,
            first_name: tg.initDataUnsafe.user.first_name,
            last_name: tg.initDataUnsafe.user.last_name,
          })
        }
      } else {
        // Пробуем получить из localStorage
        const savedUser = localStorage.getItem("telegram_user")
        if (savedUser) {
          try {
            const parsed = JSON.parse(savedUser)
            userId = parsed.id?.toString() || null
          } catch (e) {
            console.error("[TodoLists] Error parsing saved user:", e)
          }
        }
      }
    }
    
    if (!userId || userId === "demo" || userId === "undefined" || userId === "null") {
      console.error("[TodoLists] ❌ User ID не найден или невалиден:", userId)
      setError("Не удалось определить ID пользователя. Откройте приложение через Telegram.")
      setLoading(false)
      return
    }
    
    console.log(`[TodoLists] User ID: ${userId}`)

    try {
      setLoading(true)
      setError(null)

      const apiBaseUrl = typeof window !== "undefined" && window.location.hostname === "localhost"
        ? "http://localhost:8080"
        : "https://api.pasekaproduction.ru"

      const response = await fetch(`${apiBaseUrl}/api/todo-lists?user_id=${userId}`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
        mode: "cors",
      })

      console.log(`[TodoLists] API Response: status=${response.status}, ok=${response.ok}`)
      
      if (!response.ok) {
        let errorText = ""
        try {
          errorText = await response.text()
        } catch (e) {
          errorText = response.statusText
        }
        console.error(`[TodoLists] API Error: ${response.status} ${response.statusText}`, errorText)
        if (response.status === 404) {
          throw new Error("API endpoint не найден. Сервер не обновлен.")
        }
        throw new Error(`Ошибка загрузки списков: ${response.status} ${response.statusText}`)
      }

      let data
      try {
        const responseText = await response.text()
        console.log(`[TodoLists] Raw API Response:`, responseText)
        data = JSON.parse(responseText)
      } catch (e) {
        console.error(`[TodoLists] Ошибка парсинга JSON:`, e)
        throw new Error("Неверный формат ответа от сервера")
      }
      
      console.log(`[TodoLists] Parsed API Data:`, data)
      
      if (data.success && Array.isArray(data.lists)) {
        console.log(`[TodoLists] ✅ Успешно загружено ${data.lists.length} списков`)
        setLists(data.lists)
      } else if (Array.isArray(data.lists)) {
        console.log(`[TodoLists] ✅ Загружено ${data.lists.length} списков (без success поля)`)
        setLists(data.lists)
      } else if (data.error) {
        console.error(`[TodoLists] ❌ API вернул ошибку:`, data.error)
        throw new Error(data.error || "Ошибка загрузки списков")
      } else {
        console.warn(`[TodoLists] ⚠️ Неожиданный формат данных:`, data)
        setLists([])
      }
    } catch (e: any) {
      console.error("[TodoLists] Ошибка загрузки списков:", e)
      
      // Проверяем, является ли это ошибкой Mixed Content Policy
      if (e instanceof TypeError && e.message.includes("Failed to fetch")) {
        if (typeof window !== "undefined" && window.location.protocol === "https:") {
          setError("Не удалось подключиться к серверу. Откройте приложение через Telegram для доступа к спискам задач.")
        } else {
          setError("Не удалось подключиться к серверу. Проверьте подключение к интернету.")
        }
      } else {
        setError(e.message || "Не удалось загрузить списки задач")
      }
    } finally {
      setLoading(false)
    }
  }

  const createList = async () => {
    if (!newListTitle.trim()) return

    // Получаем user_id из разных источников
    let userId: string | null = null
    
    if (user?.id) {
      userId = user.id.toString()
    } else if (typeof window !== "undefined") {
      const tg = (window as any).Telegram?.WebApp
      if (tg?.initDataUnsafe?.user?.id) {
        userId = tg.initDataUnsafe.user.id.toString()
      } else {
        const savedUser = localStorage.getItem("telegram_user")
        if (savedUser) {
          try {
            const parsed = JSON.parse(savedUser)
            userId = parsed.id?.toString() || null
          } catch (e) {
            console.error("[TodoLists] Error parsing saved user:", e)
          }
        }
      }
    }
    
    if (!userId || userId === "demo" || userId === "undefined" || userId === "null") {
      console.error("[TodoLists] ❌ User ID не найден или невалиден:", userId)
      setError("Не удалось определить ID пользователя. Откройте приложение через Telegram.")
      return
    }

    try {
      setCreating(true)
      setError(null)

      const apiBaseUrl = typeof window !== "undefined" && window.location.hostname === "localhost"
        ? "http://localhost:8080"
        : "https://api.pasekaproduction.ru"

      const response = await fetch(`${apiBaseUrl}/api/todo-lists`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        mode: "cors",
        body: JSON.stringify({
          user_id: parseInt(userId),
          title: newListTitle.trim(),
        }),
      })

      if (!response.ok) {
        let errorText = ""
        try {
          const responseText = await response.text()
          console.error(`[TodoLists] Create Error Response:`, responseText)
          const errorData = JSON.parse(responseText)
          errorText = errorData.error || response.statusText
        } catch (e) {
          errorText = response.statusText || "Ошибка создания списка"
        }
        throw new Error(errorText || "Ошибка создания списка")
      }

      let result
      try {
        const responseText = await response.text()
        console.log(`[TodoLists] Create Success Response:`, responseText)
        result = JSON.parse(responseText)
      } catch (e) {
        console.error(`[TodoLists] Ошибка парсинга ответа создания:`, e)
        throw new Error("Неверный формат ответа от сервера")
      }
      
      console.log(`[TodoLists] ✅ Список создан:`, result)
      
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

