"use client"

import { useState } from "react"
import { format, startOfMonth, endOfMonth, eachDayOfInterval, isSameDay, isSameMonth, addMonths, subMonths, startOfWeek, endOfWeek } from "date-fns"
import { ru } from "date-fns/locale"
import { ChevronLeft, ChevronRight } from "lucide-react"
import Link from "next/link"
import { Button } from "../ui/button"
import { cn } from "../../lib/utils"

interface CalendarGridProps {
  selectedDate: Date
  onDateSelect: (date: Date) => void
  eventsByDate: Record<string, number> // date string -> event count
  locale?: string
}

export function CalendarGrid({
  selectedDate,
  onDateSelect,
  eventsByDate,
  locale = "ru",
}: CalendarGridProps) {
  const [currentMonth, setCurrentMonth] = useState(selectedDate)

  const monthStart = startOfMonth(currentMonth)
  const monthEnd = endOfMonth(currentMonth)
  const calendarStart = startOfWeek(monthStart, { weekStartsOn: 1 })
  const calendarEnd = endOfWeek(monthEnd, { weekStartsOn: 1 })

  const days = eachDayOfInterval({ start: calendarStart, end: calendarEnd })

  const weekDays = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

  const goToPreviousMonth = () => {
    setCurrentMonth(subMonths(currentMonth, 1))
  }

  const goToNextMonth = () => {
    setCurrentMonth(addMonths(currentMonth, 1))
  }

  const goToToday = () => {
    const today = new Date()
    setCurrentMonth(today)
    onDateSelect(today)
  }

  const dateKey = (date: Date) => format(date, "yyyy-MM-dd")
  const hasEvents = (date: Date) => {
    const key = dateKey(date)
    return (eventsByDate[key] || 0) > 0
  }

  return (
    <div className="space-y-4">
      {/* Header - как на скриншоте */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="text-lg">📅</span>
            <h2 className="text-lg font-semibold">
              {format(currentMonth, "LLLL yyyy", { locale: ru })}
            </h2>
          </div>
          <span className="text-primary text-lg">🤖</span>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="icon"
            onClick={goToPreviousMonth}
            className="h-8 w-8 text-foreground hover:bg-accent"
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={goToNextMonth}
            className="h-8 w-8 text-foreground hover:bg-accent"
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
          <Button 
            variant="outline" 
            size="sm" 
            onClick={goToToday}
            className="bg-card border-border hover:bg-accent"
          >
            Сегодня
          </Button>
        </div>
      </div>

      {/* Calendar Grid */}
      <div className="rounded-lg bg-card border border-border p-4">
        {/* Week days header */}
        <div className="grid grid-cols-7 gap-1 mb-2">
          {weekDays.map((day) => (
            <div
              key={day}
              className="text-center text-xs font-medium text-muted-foreground py-2"
            >
              {day}
            </div>
          ))}
        </div>

        {/* Calendar days */}
        <div className="grid grid-cols-7 gap-1">
          {days.map((day) => {
            const isCurrentMonth = isSameMonth(day, currentMonth)
            const isSelected = isSameDay(day, selectedDate)
            const eventCount = eventsByDate[dateKey(day)] || 0

            return (
              <button
                key={day.toISOString()}
                onClick={() => {
                  setCurrentMonth(day)
                  onDateSelect(day)
                }}
                className={cn(
                  "relative h-10 rounded-lg text-sm transition-colors flex items-center justify-center",
                  !isCurrentMonth && "text-muted-foreground opacity-40",
                  isSelected
                    ? "bg-[hsl(var(--calendar-selected))] text-white font-medium"
                    : isCurrentMonth && "hover:bg-accent/50 text-foreground"
                )}
              >
                <span>{format(day, "d")}</span>
                {hasEvents(day) && (
                  <span
                    className={cn(
                      "absolute bottom-1 left-1/2 -translate-x-1/2 h-1.5 w-1.5 rounded-full",
                      isSelected 
                        ? "bg-white" 
                        : "bg-[hsl(var(--calendar-event-dot))]"
                    )}
                  />
                )}
              </button>
            )
          })}
        </div>
      </div>
    </div>
  )
}

