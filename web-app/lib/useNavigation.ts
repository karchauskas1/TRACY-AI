"use client"

import { useRouter } from "next/navigation"
import { useCallback } from "react"

/**
 * Универсальный хук для навигации назад
 * Если есть history → router.back(), иначе → router.replace('/assistant')
 */
export function useNavigation() {
  const router = useRouter()

  const handleBack = useCallback(() => {
    if (typeof window !== "undefined") {
      const isTelegramWebApp = !!(window as any).Telegram?.WebApp

      // В Telegram WebView router.back()/router.replace периодически "ломают" клики после возврата.
      // Поэтому делаем максимально нативно: history.back(), а если не сработало — pushState + popstate на /assistant.
      const currentPath = window.location.pathname

      if (isTelegramWebApp) {
        history.back()
        setTimeout(() => {
          if (window.location.pathname === currentPath) {
            // Hard fallback: гарантированно возвращаемся на главный экран.
            // Это предотвращает "полу-состояния" после back, когда клики перестают работать.
            window.location.assign("/assistant")
          }
        }, 150)
        return
      }

      // В обычном браузере используем Next router
      router.back()
      setTimeout(() => {
        if (window.location.pathname === currentPath) {
          router.replace("/assistant")
        }
      }, 150)
    } else {
      // SSR fallback
      router.replace("/assistant")
    }
  }, [router])

  return { handleBack }
}
