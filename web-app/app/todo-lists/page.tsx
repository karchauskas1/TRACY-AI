"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { ArrowLeft, Plus, ListTodo, CheckSquare2, Square, Trash2, Loader2 } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card"
import { Button } from "../../components/ui/button"
import { Input } from "../../components/ui/input"
import { getErrorDetails, formatErrorForDisplay, type ErrorDetails } from "../../lib/error-utils"

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
  const [errorDetails, setErrorDetails] = useState<ErrorDetails | null>(null)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [newListTitle, setNewListTitle] = useState("")
  const [creating, setCreating] = useState(false)

  useEffect(() => {
    // Загружаем данные пользователя
    // Ждем немного, чтобы убедиться, что родительский компонент сохранил пользователя
    const loadUser = () => {
      if (typeof window !== "undefined") {
        const tg = (window as any).Telegram?.WebApp
        if (tg) {
          tg.ready()
          const tgUser = tg.initDataUnsafe?.user
          if (tgUser) {
            const userData = {
              id: tgUser.id.toString(),
              first_name: tgUser.first_name,
              last_name: tgUser.last_name,
            }
            setUser(userData)
            // Сохраняем в localStorage для надежности
            localStorage.setItem("telegram_user", JSON.stringify({
              ...userData,
              username: tgUser.username,
              photo_url: tgUser.photo_url,
            }))
            return
          }
        }
        // Пробуем получить из localStorage (может быть сохранен родительским компонентом)
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
    
    // Пробуем сразу
    loadUser()
    
    // Если не получилось, пробуем еще раз через небольшую задержку
    const timeoutId = setTimeout(() => {
      if (!user) {
        loadUser()
      }
    }, 100)
    
    return () => clearTimeout(timeoutId)
  }, [])

  useEffect(() => {
    if (user?.id) {
      loadLists()
    }
  }, [user])

  const loadLists = async () => {
    // Получаем user_id из разных источников
    let userId: string | null = null
    // #region agent log
    fetch('http://127.0.0.1:7244/ingest/5297ce20-cdd6-4734-9a97-89b776b10890',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'TodoListsPage.tsx:75',message:'loadLists entry',data:{hasUser:!!user,userFromState:user?.id},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'D'})}).catch(()=>{});
    // #endregion
    if (user?.id) {
      userId = user.id.toString()
      // #region agent log
      fetch('http://127.0.0.1:7244/ingest/5297ce20-cdd6-4734-9a97-89b776b10890',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'TodoListsPage.tsx:80',message:'userId from state',data:{userId,source:'user.id'},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'D'})}).catch(()=>{});
      // #endregion
    } else if (typeof window !== "undefined") {
      const tg = (window as any).Telegram?.WebApp
      if (tg?.initDataUnsafe?.user?.id) {
        userId = tg.initDataUnsafe.user.id.toString()
        // #region agent log
        fetch('http://127.0.0.1:7244/ingest/5297ce20-cdd6-4734-9a97-89b776b10890',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'TodoListsPage.tsx:85',message:'userId from Telegram WebApp',data:{userId,source:'tg.initDataUnsafe.user.id',tgUserExists:!!tg.initDataUnsafe?.user},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'D'})}).catch(()=>{});
        // #endregion
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
            // #region agent log
            fetch('http://127.0.0.1:7244/ingest/5297ce20-cdd6-4734-9a97-89b776b10890',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'TodoListsPage.tsx:100',message:'userId from localStorage',data:{userId,source:'localStorage'},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'D'})}).catch(()=>{});
            // #endregion
          } catch (e) {
            console.error("[TodoLists] Error parsing saved user:", e)
            // #region agent log
            fetch('http://127.0.0.1:7244/ingest/5297ce20-cdd6-4734-9a97-89b776b10890',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'TodoListsPage.tsx:103',message:'Error parsing localStorage user',data:{error:String(e)},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'D'})}).catch(()=>{});
            // #endregion
          }
        } else {
          // #region agent log
          fetch('http://127.0.0.1:7244/ingest/5297ce20-cdd6-4734-9a97-89b776b10890',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'TodoListsPage.tsx:107',message:'No userId found',data:{userId:null,hasUser:!!user,hasTg:!!tg,hasSavedUser:false},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'D'})}).catch(()=>{});
          // #endregion
        }
      }
    }
    
    if (!userId || userId === "demo" || userId === "undefined" || userId === "null") {
      console.error("[TodoLists] ❌ User ID не найден или невалиден:", userId)
      // #region agent log
      fetch('http://127.0.0.1:7244/ingest/5297ce20-cdd6-4734-9a97-89b776b10890',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'TodoListsPage.tsx:111',message:'Invalid userId - returning early',data:{userId,isDemo:userId==='demo',isUndefined:userId==='undefined',isNull:userId==='null'},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'D'})}).catch(()=>{});
      // #endregion
      const errorMessage = userId === "demo" 
        ? "Демо-режим не поддерживает загрузку списков задач. Откройте приложение через Telegram."
        : "Не удалось определить ID пользователя. Откройте приложение через Telegram."
      setError(errorMessage)
      setLoading(false)
      return
    }
    
    console.log(`[TodoLists] User ID: ${userId}`)
    // #region agent log
    fetch('http://127.0.0.1:7244/ingest/5297ce20-cdd6-4734-9a97-89b776b10890',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'TodoListsPage.tsx:118',message:'userId validated - proceeding to API call',data:{userId,isValid:true},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'D'})}).catch(()=>{});
    // #endregion

    try {
      setLoading(true)
      setError(null)

      const apiBaseUrl = typeof window !== "undefined" && window.location.hostname === "localhost"
        ? "http://localhost:8080"
        : "https://api.pasekaproduction.ru"

      const apiUrl = `${apiBaseUrl}/api/todo-lists?user_id=${userId}`
      // #region agent log
      fetch('http://127.0.0.1:7244/ingest/5297ce20-cdd6-4734-9a97-89b776b10890',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'TodoListsPage.tsx:124',message:'API request before fetch',data:{apiUrl,userId,apiBaseUrl},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'D'})}).catch(()=>{});
      // #endregion
      const response = await fetch(apiUrl, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
        mode: "cors",
      })

      console.log(`[TodoLists] API Response: status=${response.status}, ok=${response.ok}`)
      // #region agent log
      fetch('http://127.0.0.1:7244/ingest/5297ce20-cdd6-4734-9a97-89b776b10890',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'TodoListsPage.tsx:135',message:'API response received',data:{status:response.status,ok:response.ok,statusText:response.statusText},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'E'})}).catch(()=>{});
      // #endregion
      
      if (!response.ok) {
        let errorText = ""
        try {
          errorText = await response.text()
        } catch (e) {
          errorText = response.statusText
        }
        console.error(`[TodoLists] API Error: ${response.status} ${response.statusText}`, errorText)
        // #region agent log
        fetch('http://127.0.0.1:7244/ingest/5297ce20-cdd6-4734-9a97-89b776b10890',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'TodoListsPage.tsx:143',message:'API error response',data:{status:response.status,statusText:response.statusText,errorText},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'E'})}).catch(()=>{});
        // #endregion
        if (response.status === 404) {
          throw new Error("API endpoint не найден. Сервер не обновлен.")
        }
        throw new Error(`Ошибка загрузки списков: ${response.status} ${response.statusText}`)
      }

      let data
      try {
        const responseText = await response.text()
        console.log(`[TodoLists] Raw API Response:`, responseText)
        // #region agent log
        fetch('http://127.0.0.1:7244/ingest/5297ce20-cdd6-4734-9a97-89b776b10890',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'TodoListsPage.tsx:153',message:'Raw API response received',data:{responseLength:responseText.length,responsePreview:responseText.substring(0,200)},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'E'})}).catch(()=>{});
        // #endregion
        data = JSON.parse(responseText)
        // #region agent log
        fetch('http://127.0.0.1:7244/ingest/5297ce20-cdd6-4734-9a97-89b776b10890',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'TodoListsPage.tsx:156',message:'JSON parsed successfully',data:{hasSuccess:!!data.success,hasLists:!!data.lists,listsIsArray:Array.isArray(data.lists),listsCount:Array.isArray(data.lists)?data.lists.length:0,dataKeys:Object.keys(data)},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'E'})}).catch(()=>{});
        // #endregion
      } catch (e) {
        console.error(`[TodoLists] Ошибка парсинга JSON:`, e)
        // #region agent log
        fetch('http://127.0.0.1:7244/ingest/5297ce20-cdd6-4734-9a97-89b776b10890',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'TodoListsPage.tsx:160',message:'JSON parse error',data:{error:String(e)},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'E'})}).catch(()=>{});
        // #endregion
        throw new Error("Неверный формат ответа от сервера")
      }
      
      console.log(`[TodoLists] Parsed API Data:`, data)
      
      if (data.success && Array.isArray(data.lists)) {
        console.log(`[TodoLists] ✅ Успешно загружено ${data.lists.length} списков`)
        // #region agent log
        fetch('http://127.0.0.1:7244/ingest/5297ce20-cdd6-4734-9a97-89b776b10890',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'TodoListsPage.tsx:168',message:'Lists extracted (format: success+lists)',data:{listsCount:data.lists.length},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'E'})}).catch(()=>{});
        // #endregion
        setLists(data.lists)
        setError(null) // Очищаем ошибку при успехе
        setErrorDetails(null) // Очищаем детали ошибки
        setLoading(false) // Убеждаемся, что loading выключен
      } else if (Array.isArray(data.lists)) {
        console.log(`[TodoLists] ✅ Загружено ${data.lists.length} списков (без success поля)`)
        // #region agent log
        fetch('http://127.0.0.1:7244/ingest/5297ce20-cdd6-4734-9a97-89b776b10890',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'TodoListsPage.tsx:172',message:'Lists extracted (format: lists)',data:{listsCount:data.lists.length},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'E'})}).catch(()=>{});
        // #endregion
        setLists(data.lists)
        setError(null) // Очищаем ошибку при успехе
        setErrorDetails(null) // Очищаем детали ошибки
        setLoading(false) // Убеждаемся, что loading выключен
      } else if (data.error) {
        console.error(`[TodoLists] ❌ API вернул ошибку:`, data.error)
        // #region agent log
        fetch('http://127.0.0.1:7244/ingest/5297ce20-cdd6-4734-9a97-89b776b10890',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'TodoListsPage.tsx:176',message:'API returned error in data',data:{error:data.error},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'E'})}).catch(()=>{});
        // #endregion
        throw new Error(data.error || "Ошибка загрузки списков")
      } else {
        console.warn(`[TodoLists] ⚠️ Неожиданный формат данных:`, data)
        // #region agent log
        fetch('http://127.0.0.1:7244/ingest/5297ce20-cdd6-4734-9a97-89b776b10890',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'TodoListsPage.tsx:180',message:'Unexpected data format',data:{dataKeys:Object.keys(data)},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'E'})}).catch(()=>{});
        // #endregion
        setLists([])
        setError(null) // Очищаем ошибку
        setErrorDetails(null) // Очищаем детали ошибки
        setLoading(false) // Убеждаемся, что loading выключен
      }
    } catch (e: any) {
      console.error("[TodoLists] Ошибка загрузки списков:", e)
      
      let errorMessage = "Не удалось загрузить списки задач"
      
      // Проверяем, является ли это ошибкой Mixed Content Policy
      if (e instanceof TypeError && e.message.includes("Failed to fetch")) {
        if (typeof window !== "undefined" && window.location.protocol === "https:") {
          errorMessage = "Не удалось подключиться к серверу. Откройте приложение через Telegram для доступа к спискам задач."
        } else {
          errorMessage = "Не удалось подключиться к серверу. Проверьте подключение к интернету."
        }
      } else if (e.message) {
        if (e.message.includes("Invalid user_id") || e.message.includes("user_id required")) {
          errorMessage = "Не удалось определить ID пользователя. Откройте приложение через Telegram."
        } else if (e.message.includes("demo")) {
          errorMessage = "Демо-режим не поддерживает загрузку списков задач. Откройте приложение через Telegram."
        } else {
          errorMessage = e.message
        }
      }
      
      setError(errorMessage)
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

