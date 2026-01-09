"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { ArrowLeft, Search, Mic, Clock, Edit, Trash2, Filter, FileText, Globe, History } from "lucide-react"
import Link from "next/link"
import { Card, CardContent } from "../../../components/ui/card"
import { Button } from "../../../components/ui/button"
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
  const router = useRouter()
  const [meetings, setMeetings] = useState<Meeting[]>([])
  const [filteredMeetings, setFilteredMeetings] = useState<Meeting[]>([])
  const [searchQuery, setSearchQuery] = useState("")
  const [mediaFilter, setMediaFilter] = useState<"all" | "voice" | "video">("all")
  const [chatFilter, setChatFilter] = useState<"all" | string>("all")

  useEffect(() => {
    // Загружаем встречи из localStorage (для статического сайта)
    const storedMeetings = localStorage.getItem("tracy_meetings")
    if (storedMeetings) {
      try {
        const parsed = JSON.parse(storedMeetings)
        setMeetings(parsed)
        setFilteredMeetings(parsed)
      } catch (e) {
        console.error("Failed to parse meetings:", e)
        // Моковые данные для демонстрации
        const mockMeetings: Meeting[] = [
          {
            id: "1",
            title: "1273.",
            createdAt: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
            type: "voice",
            chat: "Personal"
          },
          {
            id: "2",
            title: "[основная тема]: Эксперт даёт развёрнутую обратную связь по проекту, указывая на ключевые недочёты в обосновании...",
            createdAt: new Date(Date.now() - 4 * 30 * 24 * 60 * 60 * 1000).toISOString(),
            type: "voice",
            chat: "Personal"
          },
          {
            id: "3",
            title: "[основная тема]: Обсуждение обратной связи по заявке на грант, включая вопросы оформления документов, финансирования...",
            createdAt: new Date(Date.now() - 4 * 30 * 24 * 60 * 60 * 1000).toISOString(),
            type: "voice",
            chat: "Personal"
          }
        ]
        setMeetings(mockMeetings)
        setFilteredMeetings(mockMeetings)
      }
    } else {
      // Моковые данные для демонстрации
      const mockMeetings: Meeting[] = [
        {
          id: "1",
          title: "1273.",
          createdAt: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
          type: "voice",
          chat: "Personal"
        },
        {
          id: "2",
          title: "[основная тема]: Эксперт даёт развёрнутую обратную связь по проекту, указывая на ключевые недочёты в обосновании...",
          createdAt: new Date(Date.now() - 4 * 30 * 24 * 60 * 60 * 1000).toISOString(),
          type: "voice",
          chat: "Personal"
        },
        {
          id: "3",
          title: "[основная тема]: Обсуждение обратной связи по заявке на грант, включая вопросы оформления документов, финансирования...",
          createdAt: new Date(Date.now() - 4 * 30 * 24 * 60 * 60 * 1000).toISOString(),
          type: "voice",
          chat: "Personal"
        }
      ]
      setMeetings(mockMeetings)
      setFilteredMeetings(mockMeetings)
    }
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
    if (confirm("Вы уверены, что хотите удалить эту запись?")) {
      const updated = meetings.filter(m => m.id !== id)
      setMeetings(updated)
      localStorage.setItem("tracy_meetings", JSON.stringify(updated))
      setFilteredMeetings(updated.filter(m => {
        if (searchQuery && !m.title.toLowerCase().includes(searchQuery.toLowerCase())) return false
        if (mediaFilter !== "all" && m.type !== mediaFilter) return false
        if (chatFilter !== "all" && m.chat !== chatFilter) return false
        return true
      }))
    }
  }

  const handleEdit = (id: string) => {
    router.push(`/meetings/${id}/edit`)
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
                        onClick={() => handleEdit(meeting.id)}
                        className="flex-1 border-primary/20 text-primary hover:bg-primary/10"
                      >
                        <Edit className="h-3 w-3 mr-1" />
                        Редактировать
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
