"use client"

import { useEffect, useState, useCallback } from "react"
import { useRouter } from "next/navigation"
import { ArrowLeft, Plus, Trash2, CheckSquare2, Square, Loader2, Pencil, Check, X } from "lucide-react"
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
  _isNew?: boolean // for animation
  _isRemoving?: boolean // for animation
}

interface TodoListDetailClientProps {
  listId: number
}

export function TodoListDetailClient({ listId }: TodoListDetailClientProps) {
  const router = useRouter()
  const { userId, isLoading: userLoading } = useTelegramUser()

  // Custom back handler that goes to todo-lists, not assistant
  const handleBack = () => {
    if (typeof window !== "undefined") {
      const isTelegramWebApp = !!(window as any).Telegram?.WebApp
      if (isTelegramWebApp) {
        window.location.assign("/todo-lists")
      } else {
        router.push("/todo-lists")
      }
    } else {
      router.push("/todo-lists")
    }
  }

  const [list, setList] = useState<TodoList | null>(null)
  const [items, setItems] = useState<TodoItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [newItemText, setNewItemText] = useState("")
  const [creating, setCreating] = useState(false)

  // Editing state
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editText, setEditText] = useState("")

  useEffect(() => {
    if (!userLoading && !userId) {
      router.push("/login")
    }
  }, [userLoading, userId, router])

  useEffect(() => {
    if (!userLoading && userId && listId) {
      loadList(true)
    }
  }, [userLoading, userId, listId])

  const loadList = async (forceFresh: boolean = false) => {
    if (!userId || !listId) return

    try {
      if (items.length === 0) setLoading(true)
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

  // Optimistic create
  const createItem = async () => {
    if (!listId || !newItemText.trim()) return

    const tempId = Date.now()
    const optimisticItem: TodoItem = {
      id: tempId,
      list_id: listId,
      text: newItemText.trim(),
      completed: false,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      _isNew: true
    }

    // Optimistic update
    setItems(prev => [optimisticItem, ...prev])
    setNewItemText("")
    setCreating(true)

    try {
      setError(null)
      const res = await apiPost<{ success?: boolean; item_id?: number; error?: string }>(
        `/api/todo-lists/${listId}/items`,
        { text: optimisticItem.text },
        { timeout: 15000 }
      )
      if (res.success === false && res.error) throw new Error(res.error)

      // Update with real ID
      if (res.item_id) {
        setItems(prev => prev.map(item =>
          item.id === tempId ? { ...item, id: res.item_id!, _isNew: false } : item
        ))
      }
      // Remove animation class after delay
      setTimeout(() => {
        setItems(prev => prev.map(item => ({ ...item, _isNew: false })))
      }, 300)
    } catch (e: any) {
      console.error("Ошибка создания задачи:", e)
      // Rollback
      setItems(prev => prev.filter(item => item.id !== tempId))
      const msg = e.type ? formatApiError(e) : (e.message || "Не удалось создать задачу")
      setError(msg)
    } finally {
      setCreating(false)
    }
  }

  // Optimistic toggle
  const toggleItem = async (itemId: number, currentCompleted: boolean) => {
    // Optimistic update
    setItems(prev => prev.map(item =>
      item.id === itemId ? { ...item, completed: !currentCompleted } : item
    ))

    try {
      setError(null)
      const res = await apiPut<{ success?: boolean; error?: string }>(
        `/api/todo-items/${itemId}`,
        { completed: !currentCompleted },
        { timeout: 15000 }
      )
      if (res.success === false && res.error) throw new Error(res.error)
    } catch (e: any) {
      console.error("Ошибка обновления задачи:", e)
      // Rollback
      setItems(prev => prev.map(item =>
        item.id === itemId ? { ...item, completed: currentCompleted } : item
      ))
      const msg = e.type ? formatApiError(e) : (e.message || "Не удалось обновить задачу")
      setError(msg)
    }
  }

  // Optimistic delete with animation
  const deleteItem = async (itemId: number) => {
    const itemToDelete = items.find(i => i.id === itemId)
    if (!itemToDelete) return

    // Start fade out animation
    setItems(prev => prev.map(item =>
      item.id === itemId ? { ...item, _isRemoving: true } : item
    ))

    // Wait for animation
    await new Promise(resolve => setTimeout(resolve, 250))

    // Optimistic remove
    setItems(prev => prev.filter(item => item.id !== itemId))

    try {
      setError(null)
      await apiDelete(`/api/todo-items/${itemId}`, { timeout: 15000 })
    } catch (e: any) {
      console.error("Ошибка удаления задачи:", e)
      // Rollback
      setItems(prev => [...prev, { ...itemToDelete, _isRemoving: false }])
      const msg = e.type ? formatApiError(e) : (e.message || "Не удалось удалить задачу")
      setError(msg)
    }
  }

  // Start editing
  const startEditing = (item: TodoItem) => {
    setEditingId(item.id)
    setEditText(item.text)
  }

  // Cancel editing
  const cancelEditing = () => {
    setEditingId(null)
    setEditText("")
  }

  // Save edit with optimistic update
  const saveEdit = async (itemId: number) => {
    if (!editText.trim()) {
      cancelEditing()
      return
    }

    const originalItem = items.find(i => i.id === itemId)
    if (!originalItem || originalItem.text === editText.trim()) {
      cancelEditing()
      return
    }

    // Optimistic update
    setItems(prev => prev.map(item =>
      item.id === itemId ? { ...item, text: editText.trim() } : item
    ))
    cancelEditing()

    try {
      setError(null)
      const res = await apiPut<{ success?: boolean; error?: string }>(
        `/api/todo-items/${itemId}`,
        { text: editText.trim() },
        { timeout: 15000 }
      )
      if (res.success === false && res.error) throw new Error(res.error)
    } catch (e: any) {
      console.error("Ошибка редактирования задачи:", e)
      // Rollback
      setItems(prev => prev.map(item =>
        item.id === itemId ? { ...item, text: originalItem.text } : item
      ))
      const msg = e.type ? formatApiError(e) : (e.message || "Не удалось сохранить изменения")
      setError(msg)
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
          <div className="w-5" />
        </div>
      </header>

      <div className="flex-1 overflow-y-auto">
        <div className="container mx-auto max-w-2xl px-4 py-6">
          {error && (
            <Card className="mb-4 border-destructive animate-appear">
              <CardContent className="pt-6">
                <p className="text-sm text-destructive">{error}</p>
              </CardContent>
            </Card>
          )}

          {/* Add task form */}
          <Card className="mb-4 border-border glass-card halation">
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
                  className="transition-all duration-200 active:scale-95"
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

          {/* Task list */}
          {items.length === 0 ? (
            <Card className="border-border glass-card">
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
                  className={`border-border glass-card transition-all duration-300 ${
                    item._isNew ? 'animate-slide-in' : ''
                  } ${item._isRemoving ? 'animate-fade-out' : ''}`}
                >
                  <CardContent className="pt-6">
                    <div className="flex items-start gap-3">
                      {/* Checkbox */}
                      <button
                        onClick={() => toggleItem(item.id, item.completed)}
                        className={`mt-0.5 transition-transform duration-200 ${
                          item.completed ? 'animate-check' : ''
                        }`}
                        disabled={editingId === item.id}
                      >
                        {item.completed ? (
                          <CheckSquare2 className="h-5 w-5 text-primary" />
                        ) : (
                          <Square className="h-5 w-5 text-muted-foreground hover:text-primary transition-colors" />
                        )}
                      </button>

                      {/* Text or Edit Input */}
                      <div className="flex-1 min-w-0">
                        {editingId === item.id ? (
                          <Input
                            value={editText}
                            onChange={(e) => setEditText(e.target.value)}
                            onKeyDown={(e) => {
                              if (e.key === "Enter") saveEdit(item.id)
                              if (e.key === "Escape") cancelEditing()
                            }}
                            autoFocus
                            className="h-8 text-sm"
                          />
                        ) : (
                          <p className={`break-words transition-all duration-200 ${
                            item.completed ? "line-through text-muted-foreground" : ""
                          }`}>
                            {item.text}
                          </p>
                        )}
                      </div>

                      {/* Action buttons */}
                      <div className="flex items-center gap-1">
                        {editingId === item.id ? (
                          <>
                            <button
                              onClick={() => saveEdit(item.id)}
                              className="p-1 text-primary hover:text-primary/80 transition-colors"
                            >
                              <Check className="h-4 w-4" />
                            </button>
                            <button
                              onClick={cancelEditing}
                              className="p-1 text-muted-foreground hover:text-foreground transition-colors"
                            >
                              <X className="h-4 w-4" />
                            </button>
                          </>
                        ) : (
                          <>
                            <button
                              onClick={() => startEditing(item)}
                              className="p-1 text-muted-foreground hover:text-foreground transition-colors"
                            >
                              <Pencil className="h-4 w-4" />
                            </button>
                            <button
                              onClick={() => deleteItem(item.id)}
                              className="p-1 text-destructive hover:text-destructive/80 transition-colors"
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          </>
                        )}
                      </div>
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
