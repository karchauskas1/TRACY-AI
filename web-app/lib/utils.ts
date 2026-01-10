import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(date: Date, locale: string = "ru"): string {
  return new Intl.DateTimeFormat(locale, {
    month: "long",
    year: "numeric",
  }).format(date)
}

export function formatTime(date: Date, format: "12" | "24" = "24"): string {
  if (format === "12") {
    return new Intl.DateTimeFormat("en-US", {
      hour: "numeric",
      minute: "2-digit",
      hour12: true,
    }).format(date)
  }
  return new Intl.DateTimeFormat("ru", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(date)
}

export function formatDateTime(date: Date, locale: string = "ru", timeFormat: "12" | "24" = "24"): string {
  const dateStr = new Intl.DateTimeFormat(locale, {
    day: "numeric",
    month: "long",
  }).format(date)
  const timeStr = formatTime(date, timeFormat)
  return `${dateStr}, ${timeStr}`
}


