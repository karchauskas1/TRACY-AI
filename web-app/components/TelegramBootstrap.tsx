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
        // Обязательные вызовы для корректной работы
        tg.ready()
        tg.expand()

        // Настройка темы (опционально, но лучше задать сразу)
        tg.setHeaderColor("#1a1a20")
        tg.setBackgroundColor("#1a1a20")

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
    }
  }, [])

  // Компонент не рендерит ничего
  return null
}
