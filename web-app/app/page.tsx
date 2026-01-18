"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"

export default function HomePage() {
  const router = useRouter()

  useEffect(() => {
    const navigate = (path: string) => {
      try {
        router.push(path)
      } catch (error) {
        if (typeof window !== 'undefined') {
          window.location.href = path
        }
      }
    }

    // Проверяем, открыто ли приложение через Telegram Web App
    if (typeof window !== "undefined" && (window as any).Telegram?.WebApp) {
      const tg = (window as any).Telegram.WebApp
      tg.enableClosingConfirmation()

      const user = tg.initDataUnsafe?.user
      if (user) {
        localStorage.setItem("telegram_user", JSON.stringify({
          id: user.id.toString(),
          first_name: user.first_name,
          last_name: user.last_name,
          username: user.username,
          photo_url: user.photo_url,
        }))
        setTimeout(() => navigate("/assistant"), 100)
      } else {
        const savedUser = localStorage.getItem("telegram_user")
        if (savedUser) {
          setTimeout(() => navigate("/assistant"), 100)
        } else {
          setTimeout(() => navigate("/login"), 100)
        }
      }
    } else {
      const savedUser = localStorage.getItem("telegram_user")
      if (savedUser) {
        try {
          const parsed = JSON.parse(savedUser)
          if (parsed.id && parsed.id !== "demo") {
            setTimeout(() => navigate("/assistant"), 100)
          } else {
            setTimeout(() => navigate("/login"), 100)
          }
        } catch (e) {
          setTimeout(() => navigate("/login"), 100)
        }
      } else {
        setTimeout(() => navigate("/login"), 100)
      }
    }
  }, [router])

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-b from-slate-900 to-slate-800">
      <div className="text-center">
        {/* Анимированный логотип */}
        <div className="relative mb-8">
          <div className="w-20 h-20 mx-auto rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-lg shadow-blue-500/25 animate-pulse">
            <span className="text-3xl font-bold text-white">T</span>
          </div>
          {/* Кольцо загрузки */}
          <div className="absolute inset-0 w-20 h-20 mx-auto">
            <svg className="w-full h-full animate-spin" style={{ animationDuration: '2s' }} viewBox="0 0 100 100">
              <circle
                cx="50"
                cy="50"
                r="45"
                fill="none"
                stroke="rgba(59, 130, 246, 0.2)"
                strokeWidth="4"
              />
              <circle
                cx="50"
                cy="50"
                r="45"
                fill="none"
                stroke="url(#gradient)"
                strokeWidth="4"
                strokeLinecap="round"
                strokeDasharray="70 200"
              />
              <defs>
                <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="#3B82F6" />
                  <stop offset="100%" stopColor="#8B5CF6" />
                </linearGradient>
              </defs>
            </svg>
          </div>
        </div>

        {/* Название */}
        <h1 className="text-3xl font-bold text-white tracking-wider mb-3">TRACY</h1>
        <p className="text-slate-400 text-sm">Личный ассистент</p>

        {/* Точки загрузки */}
        <div className="flex justify-center gap-1.5 mt-6">
          <div className="w-2 h-2 rounded-full bg-blue-500 animate-bounce" style={{ animationDelay: '0ms' }}></div>
          <div className="w-2 h-2 rounded-full bg-blue-500 animate-bounce" style={{ animationDelay: '150ms' }}></div>
          <div className="w-2 h-2 rounded-full bg-blue-500 animate-bounce" style={{ animationDelay: '300ms' }}></div>
        </div>
      </div>
    </div>
  )
}

