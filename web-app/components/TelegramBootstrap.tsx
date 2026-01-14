"use client"

import { useEffect, useRef } from "react"

/**
 * Единый bootstrap компонент для инициализации Telegram WebApp
 * 
 * Требования:
 * - Выполняется ТОЛЬКО на клиенте
 * - Выполняется один раз
 * - Вызывается до пользовательских кликов
 * - НЕ зависит от роутов
 */
export function TelegramBootstrap() {
  const initializedRef = useRef(false)

  useEffect(() => {
    // Гарантируем выполнение только на клиенте
    if (typeof window === "undefined") return

    // Гарантируем выполнение только один раз
    if (initializedRef.current) return

    const initTelegram = () => {
      // Проверяем наличие Telegram WebApp SDK
      if (!window.Telegram?.WebApp) {
        return false
      }

      const tg = window.Telegram.WebApp

      // Инициализация выполняется только один раз
      if (initializedRef.current) return true

      try {
        // Инициализируем window.__tg_bootstrap для DebugOverlay
        if (!(window as any).__tg_bootstrap) {
          (window as any).__tg_bootstrap = {
            readyCalledAt: null,
            expandCalledAt: null,
          }
        }

        // Обязательные вызовы для корректной работы
        const readyCalledAt = Date.now()
        tg.ready()
        ;(window as any).__tg_bootstrap.readyCalledAt = readyCalledAt

        const expandCalledAt = Date.now()
        tg.expand()
        ;(window as any).__tg_bootstrap.expandCalledAt = expandCalledAt

        // Настройка темы (опционально, но лучше задать сразу)
        tg.setHeaderColor("#1a1a20")
        tg.setBackgroundColor("#1a1a20")

        // iOS/Telegram WebView: disable pinch zoom gestures (prevents "zoomable UI").
        // This should not affect taps/clicks, only gesture events.
        const preventGesture = (ev: Event) => {
          ev.preventDefault()
        }
        document.addEventListener("gesturestart", preventGesture, { passive: false } as any)
        document.addEventListener("gesturechange", preventGesture, { passive: false } as any)
        document.addEventListener("gestureend", preventGesture, { passive: false } as any)
        ;(window as any).__tg_bootstrap._gestureCleanup = () => {
          document.removeEventListener("gesturestart", preventGesture as any)
          document.removeEventListener("gesturechange", preventGesture as any)
          document.removeEventListener("gestureend", preventGesture as any)
        }

        // Помечаем как инициализированное
        initializedRef.current = true

        console.log("[TelegramBootstrap] ✅ Telegram WebApp initialized")
        return true
      } catch (error) {
        console.error("[TelegramBootstrap] ❌ Error initializing Telegram WebApp:", error)
        return false
      }
    }

    // Пробуем инициализировать сразу
    if (initTelegram()) {
      return
    }

    // Если SDK еще не загружен, ждем (максимум 5 секунд)
    let attempts = 0
    const maxAttempts = 100 // 5 секунд при интервале 50ms
    const checkInterval = setInterval(() => {
      attempts++
      if (initTelegram() || attempts >= maxAttempts) {
        clearInterval(checkInterval)
      }
    }, 50)

    // Cleanup
    return () => {
      clearInterval(checkInterval)
      const cleanup = (window as any).__tg_bootstrap?._gestureCleanup
      if (typeof cleanup === "function") cleanup()
    }
  }, [])

  // Компонент не рендерит ничего
  return null
}
