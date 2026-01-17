"use client"

import { useState } from "react"
import { format, startOfMonth, endOfMonth, eachDayOfInterval, isSameDay, isSameMonth, addMonths, subMonths, startOfWeek, endOfWeek, isToday } from "date-fns"
import { ru } from "date-fns/locale"
import { ChevronLeft, ChevronRight, Calendar } from "lucide-react"
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
  const getEventCount = (date: Date) => {
    const key = dateKey(date)
    return eventsByDate[key] || 0
  }

  return (
    <div className="space-y-4">
      {/* Glassmorphism Calendar Container */}
      <div 
        className="relative rounded-3xl overflow-hidden"
        style={{
          background: 'var(--calendar-glass-bg)',
          backdropFilter: 'blur(20px) saturate(180%)',
          WebkitBackdropFilter: 'blur(20px) saturate(180%)',
          border: '1px solid var(--calendar-glass-border)',
          boxShadow: 'var(--calendar-glass-shadow)',
        }}
      >
        {/* Header with gradient accent */}
        <div 
          className="px-5 py-4"
          style={{
            background: 'var(--calendar-header-bg)',
          }}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div 
                className="h-10 w-10 rounded-xl flex items-center justify-center"
                style={{
                  background: 'var(--calendar-accent-gradient)',
                  boxShadow: '0 4px 12px rgba(147, 112, 219, 0.3)',
                }}
              >
                <Calendar className="h-5 w-5 text-white" />
              </div>
              <div>
                <h2 className="text-xl font-bold capitalize tracking-tight">
                  {format(currentMonth, "LLLL", { locale: ru })}
                </h2>
                <p className="text-sm text-muted-foreground">
                  {format(currentMonth, "yyyy")}
                </p>
              </div>
            </div>
            
            <div className="flex items-center gap-1">
              <button
                onClick={goToPreviousMonth}
                className="h-9 w-9 rounded-xl flex items-center justify-center text-foreground/70 hover:text-foreground hover:bg-[hsl(var(--calendar-day-hover))] transition-all duration-200"
              >
                <ChevronLeft className="h-5 w-5" />
              </button>
              <button
                onClick={goToToday}
                className="px-3 h-9 rounded-xl text-sm font-medium text-foreground/70 hover:text-foreground hover:bg-[hsl(var(--calendar-day-hover))] transition-all duration-200"
              >
                Сегодня
              </button>
              <button
                onClick={goToNextMonth}
                className="h-9 w-9 rounded-xl flex items-center justify-center text-foreground/70 hover:text-foreground hover:bg-[hsl(var(--calendar-day-hover))] transition-all duration-200"
              >
                <ChevronRight className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>

        {/* Calendar Grid */}
        <div className="px-4 pb-4">
          {/* Week days header */}
          <div className="grid grid-cols-7 gap-1 mb-2">
            {weekDays.map((day, idx) => (
              <div
                key={day}
                className={cn(
                  "text-center text-xs font-semibold py-3 uppercase tracking-wider",
                  idx >= 5 ? "text-[hsl(var(--calendar-event-dot))]" : "text-muted-foreground"
                )}
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
              const isTodayDate = isToday(day)
              const eventCount = getEventCount(day)
              const hasEventsToday = eventCount > 0

              return (
                <button
                  key={day.toISOString()}
                  onClick={() => {
                    setCurrentMonth(day)
                    onDateSelect(day)
                  }}
                  className={cn(
                    "relative h-11 rounded-xl text-sm transition-all duration-200 flex flex-col items-center justify-center gap-0.5",
                    !isCurrentMonth && "text-muted-foreground/40",
                    isSelected && "ring-0",
                    !isSelected && isCurrentMonth && "hover:bg-[hsl(var(--calendar-day-hover))]",
                    isTodayDate && !isSelected && "font-bold"
                  )}
                  style={isSelected ? {
                    background: 'var(--calendar-accent-gradient)',
                    boxShadow: '0 4px 16px rgba(147, 112, 219, 0.4)',
                    transform: 'scale(1.05)',
                  } : isTodayDate ? {
                    border: '2px solid hsl(var(--calendar-today))',
                  } : undefined}
                >
                  <span className={cn(
                    "relative z-10",
                    isSelected && "text-white font-semibold"
                  )}>
                    {format(day, "d")}
                  </span>
                  
                  {/* Event indicators */}
                  {hasEventsToday && (
                    <div className="flex gap-0.5 justify-center">
                      {eventCount <= 3 ? (
                        Array.from({ length: eventCount }).map((_, i) => (
                          <span
                            key={i}
                            className={cn(
                              "h-1 w-1 rounded-full transition-colors",
                              isSelected 
                                ? "bg-white/80" 
                                : "bg-[hsl(var(--calendar-event-dot))]"
                            )}
                          />
                        ))
                      ) : (
                        <>
                          <span
                            className={cn(
                              "h-1 w-1 rounded-full",
                              isSelected ? "bg-white/80" : "bg-[hsl(var(--calendar-event-dot))]"
                            )}
                          />
                          <span
                            className={cn(
                              "h-1 w-1 rounded-full",
                              isSelected ? "bg-white/80" : "bg-[hsl(var(--calendar-event-dot))]"
                            )}
                          />
                          <span
                            className={cn(
                              "text-[8px] font-bold -mt-0.5",
                              isSelected ? "text-white/80" : "text-[hsl(var(--calendar-event-dot))]"
                            )}
                          >
                            +
                          </span>
                        </>
                      )}
                    </div>
                  )}
                </button>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}
