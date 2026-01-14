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
      // Проверяем, есть ли история (window.history.length > 1)
      // Но это не всегда надежно, поэтому используем другой подход:
      // Пробуем router.back(), но если через небольшую задержку pathname не изменился,
      // делаем fallback на /assistant
      
      const currentPath = window.location.pathname
      
      // Пробуем вернуться назад
      router.back()
      
      // Проверяем через 100мс, изменился ли pathname
      setTimeout(() => {
        if (window.location.pathname === currentPath) {
          // История пустая или back не сработал, переходим на /assistant
          router.replace("/assistant")
        }
      }, 100)
    } else {
      // SSR fallback
      router.replace("/assistant")
    }
  }, [router])

  return { handleBack }
}
