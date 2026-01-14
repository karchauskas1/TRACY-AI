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
        // #region agent log
        fetch('http://127.0.0.1:7244/ingest/5297ce20-cdd6-4734-9a97-89b776b10890',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'TelegramBootstrap.tsx:35',message:'Before tg.ready()',data:{hasTelegram:!!window.Telegram,hasWebApp:!!window.Telegram?.WebApp},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
        // #endregion
        // Обязательные вызовы для корректной работы
        tg.ready()
        // #region agent log
        fetch('http://127.0.0.1:7244/ingest/5297ce20-cdd6-4734-9a97-89b776b10890',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'TelegramBootstrap.tsx:38',message:'After tg.ready()',data:{},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
        // #endregion
        tg.expand()
        // #region agent log
        fetch('http://127.0.0.1:7244/ingest/5297ce20-cdd6-4734-9a97-89b776b10890',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'TelegramBootstrap.tsx:41',message:'After tg.expand()',data:{},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
        // #endregion

        // Настройка темы (опционально, но лучше задать сразу)
        tg.setHeaderColor("#1a1a20")
        tg.setBackgroundColor("#1a1a20")

        // Помечаем как инициализированное
        initializedRef.current = true

        // #region agent log
        fetch('http://127.0.0.1:7244/ingest/5297ce20-cdd6-4734-9a97-89b776b10890',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'TelegramBootstrap.tsx:50',message:'Telegram WebApp initialized',data:{initialized:initializedRef.current},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
        // #endregion
        console.log("[TelegramBootstrap] ✅ Telegram WebApp initialized")
        return true
      } catch (error) {
        // #region agent log
        fetch('http://127.0.0.1:7244/ingest/5297ce20-cdd6-4734-9a97-89b776b10890',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'TelegramBootstrap.tsx:53',message:'Error initializing',data:{error:String(error)},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
        // #endregion
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
