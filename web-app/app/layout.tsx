import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"
import { Toaster } from "../components/ui/toaster"
import { LocaleProvider } from "../lib/locale-context"
import { ThemeProvider } from "../lib/theme-context"
import { ApiDebugInit } from "../components/ApiDebugInit"
import { TelegramBootstrap } from "../components/TelegramBootstrap"
import { DebugOverlay } from "../components/DebugOverlay"
import { ChunkErrorHandler } from "../components/ChunkErrorHandler"

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
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
        <script src="https://telegram.org/js/telegram-web-app.js" />
        <script
          dangerouslySetInnerHTML={{
            __html: `
              window.__NEXT_PUBLIC_API_URL__ = ${JSON.stringify(apiUrl)};
            `,
          }}
        />
      </head>
      <body className={inter.className}>
        <ChunkErrorHandler />
        <TelegramBootstrap />
        <ApiDebugInit />
        <DebugOverlay />
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

