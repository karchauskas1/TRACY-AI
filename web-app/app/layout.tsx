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
  return (
    <html lang="ru">
      <head>
        <script src="https://telegram.org/js/telegram-web-app.js" async />
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

