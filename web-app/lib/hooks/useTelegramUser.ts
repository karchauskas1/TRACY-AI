/**
 * Хук для получения user_id из Telegram WebApp
 * Гарантирует, что user_id будет получен до выполнения запросов
 */

import { useState, useEffect, useCallback } from 'react'

export interface TelegramUser {
  id: string
  first_name?: string
  last_name?: string
  username?: string
  photo_url?: string
}

export interface UseTelegramUserResult {
  user: TelegramUser | null
  userId: string | null
  isLoading: boolean
  error: string | null
  refresh: () => void
}

const MAX_RETRIES = 5
const RETRY_DELAY = 200

/**
 * Хук для получения пользователя из Telegram WebApp или localStorage
 */
export function useTelegramUser(): UseTelegramUserResult {
  const [user, setUser] = useState<TelegramUser | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadUser = useCallback(() => {
    if (typeof window === 'undefined') {
      setIsLoading(false)
      return
    }

    setIsLoading(true)
    setError(null)

    // Пробуем получить из Telegram WebApp
    const tg = (window as any).Telegram?.WebApp
    if (tg) {
      try {
        // Telegram WebApp уже инициализирован через TelegramBootstrap
        const tgUser = tg.initDataUnsafe?.user
        if (tgUser && tgUser.id) {
          const userData: TelegramUser = {
            id: tgUser.id.toString(),
            first_name: tgUser.first_name,
            last_name: tgUser.last_name,
            username: tgUser.username,
            photo_url: tgUser.photo_url,
          }
          
          // Сохраняем в localStorage для надежности
          localStorage.setItem('telegram_user', JSON.stringify(userData))
          
          setUser(userData)
          setIsLoading(false)
          return
        }
      } catch (e: any) {
        console.error('[useTelegramUser] Ошибка получения пользователя из Telegram WebApp:', e)
      }
    }

    // Пробуем получить из localStorage
    try {
      const savedUser = localStorage.getItem('telegram_user')
      if (savedUser) {
        const parsed = JSON.parse(savedUser)
        if (parsed && parsed.id) {
          setUser({
            id: parsed.id.toString(),
            first_name: parsed.first_name,
            last_name: parsed.last_name,
            username: parsed.username,
            photo_url: parsed.photo_url,
          })
          setIsLoading(false)
          return
        }
      }
    } catch (e: any) {
      console.error('[useTelegramUser] Ошибка парсинга сохраненного пользователя:', e)
    }

    // Если ничего не получилось
    setIsLoading(false)
    setError('Не удалось определить пользователя. Откройте приложение через Telegram.')
  }, [])

  useEffect(() => {
    // Пробуем сразу
    loadUser()

    // Если не получилось, пробуем еще раз с задержкой (для race condition)
    let retryCount = 0
    const retryInterval = setInterval(() => {
      if (!user && retryCount < MAX_RETRIES) {
        retryCount++
        console.log(`[useTelegramUser] Retry ${retryCount}/${MAX_RETRIES}`)
        loadUser()
      } else {
        clearInterval(retryInterval)
      }
    }, RETRY_DELAY)

    return () => clearInterval(retryInterval)
  }, [loadUser, user])

  const refresh = useCallback(() => {
    loadUser()
  }, [loadUser])

  return {
    user,
    userId: user?.id || null,
    isLoading,
    error,
    refresh,
  }
}

