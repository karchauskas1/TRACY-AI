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
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-b from-slate-900 via-slate-800 to-slate-900">
      <div className="text-center">
        {/* Буква T с эффектом заполнения цветом */}
        <div className="relative inline-block">
          <svg
            viewBox="0 0 100 120"
            className="w-32 h-40"
            style={{ filter: 'drop-shadow(0 0 30px rgba(139, 92, 246, 0.4))' }}
          >
            <defs>
              {/* Градиент для заполнения */}
              <linearGradient id="fillGradient" x1="0%" y1="100%" x2="0%" y2="0%">
                <stop offset="0%" stopColor="#3B82F6" />
                <stop offset="50%" stopColor="#8B5CF6" />
                <stop offset="100%" stopColor="#EC4899" />
              </linearGradient>

              {/* Маска для анимации заполнения */}
              <mask id="fillMask">
                <rect x="0" y="0" width="100" height="120" fill="white" />
                <rect
                  x="0"
                  y="0"
                  width="100"
                  height="120"
                  fill="black"
                  className="animate-fill-up"
                />
              </mask>

              {/* Форма буквы T */}
              <clipPath id="letterT">
                <path d="M10 0 H90 V20 H58 V120 H42 V20 H10 Z" />
              </clipPath>
            </defs>

            {/* Контур буквы T (пустой) */}
            <path
              d="M10 0 H90 V20 H58 V120 H42 V20 H10 Z"
              fill="none"
              stroke="rgba(148, 163, 184, 0.3)"
              strokeWidth="2"
            />

            {/* Заполняющийся градиент */}
            <g clipPath="url(#letterT)">
              <rect
                x="0"
                y="0"
                width="100"
                height="120"
                fill="url(#fillGradient)"
                mask="url(#fillMask)"
              />
            </g>

            {/* Блик/свечение сверху */}
            <path
              d="M10 0 H90 V20 H58 V120 H42 V20 H10 Z"
              fill="none"
              stroke="url(#fillGradient)"
              strokeWidth="1"
              opacity="0.5"
              className="animate-pulse"
            />
          </svg>
        </div>
      </div>

      <style jsx>{`
        @keyframes fill-up {
          0% {
            transform: translateY(0);
          }
          100% {
            transform: translateY(-120px);
          }
        }

        .animate-fill-up {
          animation: fill-up 2s ease-in-out infinite;
        }
      `}</style>
    </div>
  )
}

