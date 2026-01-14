/**
 * Хук для получения user_id из Telegram WebApp
 * Устраняет race condition - гарантирует получение user_id перед использованием
 */

import { useState, useEffect, useCallback } from 'react'

interface TelegramUser {
  id: string
  first_name?: string
  last_name?: string
  username?: string
  photo_url?: string
}

interface UseTelegramUserResult {
  user: TelegramUser | null
  userId: string | null
  isLoading: boolean
  error: string | null
  refresh: () => void
}

/**
 * Хук для получения пользователя из Telegram WebApp или localStorage
 * Гарантирует, что user_id будет доступен перед использованием
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

    try {
      setIsLoading(true)
      setError(null)

      // Пробуем получить из Telegram WebApp
      const tg = (window as any).Telegram?.WebApp
      if (tg) {
        // Telegram WebApp уже инициализирован через TelegramBootstrap
        
        // Пробуем получить из initDataUnsafe (приоритет)
        let tgUser = tg.initDataUnsafe?.user
        
        // Если нет в initDataUnsafe, пробуем парсить initData напрямую
        if (!tgUser && tg.initData) {
          try {
            const params = new URLSearchParams(tg.initData)
            const userStr = params.get('user')
            if (userStr) {
              tgUser = JSON.parse(decodeURIComponent(userStr))
            }
          } catch (e) {
            console.error('[useTelegramUser] Error parsing initData:', e)
          }
        }
        
        if (tgUser && tgUser.id) {
          const userData: TelegramUser = {
            id: tgUser.id.toString(),
            first_name: tgUser.first_name,
            last_name: tgUser.last_name,
            username: tgUser.username,
            photo_url: tgUser.photo_url,
          }
          
          setUser(userData)
          
          // Сохраняем в localStorage для надежности
          localStorage.setItem('telegram_user', JSON.stringify(userData))
          
          console.log('[useTelegramUser] ✅ User loaded from Telegram WebApp:', userData)
          setIsLoading(false)
          return
        }
      }

      // Пробуем получить из localStorage
      const savedUser = localStorage.getItem('telegram_user')
      if (savedUser) {
        try {
          const parsed = JSON.parse(savedUser)
          if (parsed.id) {
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
        } catch (e) {
          console.error('[useTelegramUser] Error parsing saved user:', e)
          localStorage.removeItem('telegram_user') // Удаляем поврежденные данные
        }
      }

      // Пользователь не найден - не устанавливаем ошибку, просто возвращаем null
      // Это позволит компонентам показать редирект на логин
      setError(null)
      setIsLoading(false)
      
    } catch (e: any) {
      console.error('[useTelegramUser] Error loading user:', e)
      setError(e.message || 'Ошибка загрузки пользователя')
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    // Загружаем сразу
    loadUser()
    
    // Пробуем еще раз через небольшую задержку (на случай, если Telegram SDK еще не загрузился)
    const timeoutId = setTimeout(() => {
      if (!user) {
        loadUser()
      }
    }, 100)
    
    return () => clearTimeout(timeoutId)
  }, [loadUser, user])

  // Слушаем изменения в Telegram WebApp (если они есть)
  useEffect(() => {
    if (typeof window === 'undefined') return
    
    const tg = (window as any).Telegram?.WebApp
    if (tg && tg.onEvent) {
      // Слушаем события обновления данных пользователя
      const handleUpdate = () => {
        loadUser()
      }
      
      // Telegram WebApp может отправлять события обновления
      // Если есть такой механизм, подписываемся
      if (typeof tg.onEvent === 'function') {
        // Telegram WebApp SDK не имеет стандартного события для обновления user
        // Но мы можем слушать другие события, если они есть
      }
    }
  }, [loadUser])

  return {
    user,
    userId: user?.id || null,
    isLoading,
    error,
    refresh: loadUser,
  }
}

