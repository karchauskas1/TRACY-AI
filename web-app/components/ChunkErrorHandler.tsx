"use client"

import { useEffect } from "react"
import { logger } from "../lib/logger"

/**
 * Глобальный обработчик ошибок загрузки чанков Next.js
 * 
 * Проблема: Telegram WebView агрессивно кеширует JS/HTML, что может привести к:
 * - ChunkLoadError при попытке загрузить старые чанки
 * - Навигация не работает из-за ошибок загрузки
 * 
 * Решение: При обнаружении ChunkLoadError делаем hard reload
 */
export function ChunkErrorHandler() {
  useEffect(() => {
    if (typeof window === "undefined") return

    // Обработка ChunkLoadError
    const handleChunkError = (event: ErrorEvent) => {
      const error = event.error || event.message || ""
      const errorString = String(error)

      // Проверяем на ChunkLoadError
      if (
        errorString.includes("ChunkLoadError") ||
        errorString.includes("Loading chunk") ||
        errorString.includes("Failed to fetch") ||
        errorString.includes("chunk") ||
        (errorString.includes("404") && errorString.includes("_next"))
      ) {
        logger.error("ChunkErrorHandler", "Chunk load error detected", {
          error: errorString,
          url: event.filename || window.location.href,
          timestamp: Date.now(),
        })

        // Делаем hard reload с cache-busting
        const currentUrl = new URL(window.location.href)
        currentUrl.searchParams.set("_reload", Date.now().toString())
        window.location.href = currentUrl.toString()
      }
    }

    // Обработка unhandled promise rejections (часто ChunkLoadError приходит через Promise)
    const handleUnhandledRejection = (event: PromiseRejectionEvent) => {
      const reason = event.reason || ""
      const reasonString = String(reason)

      if (
        reasonString.includes("ChunkLoadError") ||
        reasonString.includes("Loading chunk") ||
        reasonString.includes("Failed to fetch") ||
        (reasonString.includes("404") && reasonString.includes("_next"))
      ) {
        logger.error("ChunkErrorHandler", "Chunk load error (unhandled rejection)", {
          reason: reasonString,
          timestamp: Date.now(),
        })

        // Делаем hard reload с cache-busting
        const currentUrl = new URL(window.location.href)
        currentUrl.searchParams.set("_reload", Date.now().toString())
        window.location.href = currentUrl.toString()
      }
    }

    // Перехват ошибок загрузки через fetch (для _next/static)
    const originalFetch = window.fetch
    window.fetch = async function (...args) {
      try {
        const response = await originalFetch.apply(this, args)
        
        // Проверяем на 404 для _next/static
        if (!response.ok && response.status === 404) {
          const url = args[0]?.toString() || ""
          if (url.includes("_next/static") || url.includes("_next/data")) {
            logger.error("ChunkErrorHandler", "404 on Next.js chunk", {
              url,
              status: response.status,
              timestamp: Date.now(),
            })

            // Делаем hard reload
            const currentUrl = new URL(window.location.href)
            currentUrl.searchParams.set("_reload", Date.now().toString())
            window.location.href = currentUrl.toString()
            return response
          }
        }
        
        return response
      } catch (error) {
        const url = args[0]?.toString() || ""
        if (url.includes("_next/static") || url.includes("_next/data")) {
          logger.error("ChunkErrorHandler", "Fetch error on Next.js chunk", {
            url,
            error: String(error),
            timestamp: Date.now(),
          })

          // Делаем hard reload
          const currentUrl = new URL(window.location.href)
          currentUrl.searchParams.set("_reload", Date.now().toString())
          window.location.href = currentUrl.toString()
        }
        throw error
      }
    }

    window.addEventListener("error", handleChunkError)
    window.addEventListener("unhandledrejection", handleUnhandledRejection)

    return () => {
      window.removeEventListener("error", handleChunkError)
      window.removeEventListener("unhandledrejection", handleUnhandledRejection)
      window.fetch = originalFetch
    }
  }, [])

  return null
}
