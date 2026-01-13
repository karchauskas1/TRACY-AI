import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"
import { Toaster } from "../components/ui/toaster"
import { LocaleProvider } from "../lib/locale-context"
import { ThemeProvider } from "../lib/theme-context"
import { ApiDebugInit } from "../components/ApiDebugInit"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "TRACY - AI Calendar Assistant",
  description: "Умный ассистент для управления календарем",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  // Инжектируем NEXT_PUBLIC_API_URL в window для runtime доступа
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://api.pasekaproduction.ru'
  
  return (
    <html lang="ru">
      <head>
        <script 
          src="https://telegram.org/js/telegram-web-app.js" 
          strategy="beforeInteractive"
        />
        <script
          dangerouslySetInnerHTML={{
            __html: `
              window.__NEXT_PUBLIC_API_URL__ = ${JSON.stringify(apiUrl)};
              
              // Ждем загрузки Telegram WebApp SDK
              if (typeof window !== 'undefined') {
                const checkTelegram = setInterval(() => {
                  if (window.Telegram && window.Telegram.WebApp) {
                    const tg = window.Telegram.WebApp;
                    tg.ready();
                    tg.expand();
                    clearInterval(checkTelegram);
                  }
                }, 50);
                
                // Останавливаем проверку через 5 секунд
                setTimeout(() => clearInterval(checkTelegram), 5000);
              }
            `,
          }}
        />
      </head>
      <body className={inter.className}>
        <ApiDebugInit />
        <ThemeProvider>
          <LocaleProvider>
            {children}
            <Toaster />
          </LocaleProvider>
        </ThemeProvider>
      </body>
    </html>
  )
}

