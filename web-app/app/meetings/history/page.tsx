"use client"

import { useState, useEffect } from "react"
import { ArrowLeft, Search, Mic, Clock, Edit, Trash2, Filter, FileText, Globe, History } from "lucide-react"
import Link from "next/link"
import { Card, CardContent } from "../../../components/ui/card"
import { Button } from "../../../components/ui/button"
import { useToast } from "../../../hooks/use-toast"
import { format, formatDistanceToNow } from "date-fns"
import { ru } from "date-fns/locale"

interface Meeting {
  id: string
  title: string
  createdAt: string
  summary?: string
  transcript?: string
  type?: "voice" | "video"
  chat?: string
}

export default function MeetingsHistoryPage() {
  const { toast } = useToast()
  const [meetings, setMeetings] = useState<Meeting[]>([])
  const [filteredMeetings, setFilteredMeetings] = useState<Meeting[]>([])
  const [searchQuery, setSearchQuery] = useState("")
  const [mediaFilter, setMediaFilter] = useState<"all" | "voice" | "video">("all")
  const [chatFilter, setChatFilter] = useState<"all" | string>("all")
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null)

  useEffect(() => {
    const loadMeetings = async () => {
      // Получаем user_id
      let userId: string | null = null
      if (typeof window !== "undefined") {
        const tg = (window as any).Telegram?.WebApp
        if (tg) {
          // Telegram WebApp уже инициализирован через TelegramBootstrap
          userId = tg.initDataUnsafe?.user?.id?.toString() || null
        } else {
          const savedUser = localStorage.getItem("telegram_user")
          if (savedUser) {
            try {
              const parsed = JSON.parse(savedUser)
              userId = parsed.id?.toString() || null
            } catch (e) {
              console.error("Error parsing saved user:", e)
            }
          }
        }
      }

      if (!userId) {
        setMeetings([])
        setFilteredMeetings([])
        return
      }

      // Загружаем из API
      try {
        const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || 
          (typeof window !== 'undefined' && window.location.hostname === 'localhost' 
            ? 'http://localhost:8080' 
            : 'https://api.pasekaproduction.ru')
        const apiUrl = `${apiBaseUrl}/api/meetings?user_id=${userId}`
        
        const response = await fetch(apiUrl, {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' },
          mode: 'cors',
        })
        
        if (response.ok) {
          const data = await response.json()
          if (data.success && Array.isArray(data.meetings)) {
            const formattedMeetings: Meeting[] = data.meetings.map((m: any) => ({
              id: m.id,
              title: m.title || m.summary?.substring(0, 100) || 'Встреча',
              createdAt: m.createdAt,
              summary: m.summary,
              transcript: m.transcript,
              type: "voice" as const,
              chat: "Personal"
            }))
            setMeetings(formattedMeetings)
            setFilteredMeetings(formattedMeetings)
            localStorage.setItem("tracy_meetings", JSON.stringify(formattedMeetings))
            return
          }
        }
      } catch (error) {
        console.error("Error loading meetings:", error)
      }

      // Fallback: загружаем из localStorage
      const storedMeetings = localStorage.getItem("tracy_meetings")
      if (storedMeetings) {
        try {
          const parsed = JSON.parse(storedMeetings)
          setMeetings(parsed)
          setFilteredMeetings(parsed)
        } catch (e) {
          console.error("Failed to parse meetings:", e)
        }
      }
    }

    loadMeetings()
  }, [])

  useEffect(() => {
    // Фильтрация встреч
    let filtered = [...meetings]

    // Поиск
    if (searchQuery) {
      filtered = filtered.filter(meeting =>
        meeting.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (meeting.summary && meeting.summary.toLowerCase().includes(searchQuery.toLowerCase()))
      )
    }

    // Фильтр по типу медиа
    if (mediaFilter !== "all") {
      filtered = filtered.filter(meeting => meeting.type === mediaFilter)
    }

    // Фильтр по чату
    if (chatFilter !== "all") {
      filtered = filtered.filter(meeting => meeting.chat === chatFilter)
    }

    setFilteredMeetings(filtered)
  }, [searchQuery, mediaFilter, chatFilter, meetings])

  const handleDelete = (id: string) => {
    // Если уже подтверждено, удаляем
    if (deleteConfirmId === id) {
      const updated = meetings.filter(m => m.id !== id)
      setMeetings(updated)
      localStorage.setItem("tracy_meetings", JSON.stringify(updated))
      
      // Обновляем отфильтрованный список
      let filtered = [...updated]
      if (searchQuery) {
        filtered = filtered.filter(meeting =>
          meeting.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
          (meeting.summary && meeting.summary.toLowerCase().includes(searchQuery.toLowerCase()))
        )
      }
      if (mediaFilter !== "all") {
        filtered = filtered.filter(meeting => meeting.type === mediaFilter)
      }
      if (chatFilter !== "all") {
        filtered = filtered.filter(meeting => meeting.chat === chatFilter)
      }
      setFilteredMeetings(filtered)
      setDeleteConfirmId(null)
      toast({
        title: "Запись удалена",
        description: "Встреча успешно удалена из истории",
      })
    } else {
      // Первый клик - показываем подтверждение через toast
      setDeleteConfirmId(id)
      toast({
        title: "Подтвердите удаление",
        description: "Нажмите на кнопку удаления еще раз для подтверждения",
        variant: "destructive",
      })
      // Сбрасываем подтверждение через 3 секунды
      setTimeout(() => setDeleteConfirmId(null), 3000)
    }
  }

  const handleEdit = (id: string) => {
    // Открываем детали встречи через API
    const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || 
      (typeof window !== 'undefined' && window.location.hostname === 'localhost' 
        ? 'http://localhost:8080' 
        : 'https://api.pasekaproduction.ru')
    const userId = typeof window !== 'undefined' ? 
      ((window as any).Telegram?.WebApp?.initDataUnsafe?.user?.id || 
       localStorage.getItem('telegram_user')?.match(/"id":"(\d+)"/)?.[1]) : ''
    const apiUrl = `${apiBaseUrl}/api/meetings/${id}?user_id=${userId}`
    
    fetch(apiUrl)
      .then(res => res.json())
      .then(data => {
        if (data.success && data.meeting) {
          const details = `Резюме: ${data.meeting.summary || 'Нет'}\n\nРасширенное резюме: ${data.meeting.summaryExtended || 'Нет'}\n\nПолный текст: ${data.meeting.transcript || 'Нет'}`
          // Используем toast вместо alert
          toast({
            title: "Детали встречи",
            description: details.substring(0, 500) + (details.length > 500 ? '...' : ''),
          })
        } else {
          toast({
            title: "Ошибка",
            description: "Не удалось загрузить детали встречи",
            variant: "destructive",
          })
        }
      })
      .catch(e => {
        console.error(e)
        toast({
          title: "Ошибка",
          description: "Ошибка загрузки деталей встречи",
          variant: "destructive",
        })
      })
  }

  const uniqueChats = Array.from(new Set(meetings.map(m => m.chat).filter(Boolean)))

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      <header className="sticky top-0 z-20 border-b border-border bg-background/95 backdrop-blur">
        <div className="flex h-14 items-center justify-between px-4">
          <Link href="/assistant">
            <button className="text-foreground hover:text-muted-foreground transition-colors">
              <ArrowLeft className="h-5 w-5" />
            </button>
          </Link>
          <h1 className="text-lg font-semibold">Все записи</h1>
          <div className="w-5" />
        </div>
      </header>

      <div className="flex-1 overflow-y-auto">
        <div className="container mx-auto max-w-2xl px-4 py-6">
          {/* Заголовок и счетчик */}
          <div className="mb-4">
            <p className="text-sm text-muted-foreground">
              {filteredMeetings.length} / {meetings.length} записей
            </p>
          </div>

          {/* Поиск */}
          <div className="mb-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <input
                type="text"
                placeholder="Поиск по записям..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 rounded-lg border border-border bg-card text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
          </div>

          {/* Фильтры */}
          <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
            <Button
              variant={mediaFilter === "all" ? "default" : "outline"}
              size="sm"
              onClick={() => setMediaFilter("all")}
              className="flex items-center gap-2 whitespace-nowrap"
            >
              <FileText className="h-4 w-4" />
              Все медиа
            </Button>
            <Button
              variant={chatFilter === "all" ? "default" : "outline"}
              size="sm"
              onClick={() => setChatFilter("all")}
              className="flex items-center gap-2 whitespace-nowrap"
            >
              <Globe className="h-4 w-4" />
              Все чаты
            </Button>
          </div>

          {/* Список записей */}
          {filteredMeetings.length === 0 ? (
            <Card className="border-border">
              <CardContent className="pt-6">
                <div className="text-center py-12">
                  <History className="h-16 w-16 mx-auto text-muted-foreground mb-4 opacity-50" />
                  <h3 className="text-lg font-semibold mb-2">
                    {searchQuery ? "Ничего не найдено" : "Пока нет записей"}
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    {searchQuery
                      ? "Попробуйте изменить поисковый запрос"
                      : "Загрузи первую встречу, чтобы увидеть её здесь"}
                  </p>
                </div>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-3">
              {filteredMeetings.map((meeting) => (
                <Card
                  key={meeting.id}
                  className="border-border bg-card"
                >
                  <CardContent className="p-4">
                    <div className="flex items-start gap-3 mb-3">
                      <Mic className="h-5 w-5 text-muted-foreground mt-0.5 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-2 flex-wrap">
                          <div className="flex items-center gap-1 text-xs text-muted-foreground">
                            <Clock className="h-3 w-3" />
                            {formatDistanceToNow(new Date(meeting.createdAt), {
                              addSuffix: true,
                              locale: ru
                            })}
                          </div>
                          {meeting.chat && (
                            <span className="px-2 py-0.5 rounded-full bg-primary/20 text-primary text-xs font-medium">
                              {meeting.chat}
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-foreground line-clamp-2">
                          {meeting.title}
                        </p>
                      </div>
                    </div>

                    {/* Кнопки действий */}
                    <div className="flex gap-2 pt-2 border-t border-border">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          // Открываем детали встречи в модальном окне или через API
                          const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || 
                            (typeof window !== 'undefined' && window.location.hostname === 'localhost' 
                              ? 'http://localhost:8080' 
                              : 'https://api.pasekaproduction.ru')
                          const apiUrl = `${apiBaseUrl}/api/meetings/${meeting.id}?user_id=${typeof window !== 'undefined' ? (window as any).Telegram?.WebApp?.initDataUnsafe?.user?.id || localStorage.getItem('telegram_user')?.match(/"id":"(\d+)"/)?.[1] : ''}`
                          
                          fetch(apiUrl)
                            .then(res => res.json())
                            .then(data => {
                              if (data.success && data.meeting) {
                                const details = `Резюме: ${data.meeting.summary || 'Нет'}\n\nРасширенное резюме: ${data.meeting.summaryExtended || 'Нет'}\n\nПолный текст: ${data.meeting.transcript || 'Нет'}`
                                // Используем toast вместо alert
                                toast({
                                  title: "Детали встречи",
                                  description: details.substring(0, 500) + (details.length > 500 ? '...' : ''),
                                })
                              }
                            })
                            .catch(e => {
                              console.error(e)
                              toast({
                                title: "Ошибка",
                                description: "Не удалось загрузить детали встречи",
                                variant: "destructive",
                              })
                            })
                        }}
                        className="flex-1 border-primary/20 text-primary hover:bg-primary/10"
                      >
                        <Edit className="h-3 w-3 mr-1" />
                        Открыть
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDelete(meeting.id)}
                        className="flex-1 border-muted-foreground/20 text-muted-foreground hover:bg-destructive/10 hover:border-destructive/20 hover:text-destructive"
                      >
                        <Trash2 className="h-3 w-3 mr-1" />
                        Удалить
                      </Button>
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
