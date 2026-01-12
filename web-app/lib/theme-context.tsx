"use client"

import { createContext, useContext, useEffect, useState } from "react"

type Theme = "light" | "dark" | "system"

interface ThemeContextType {
  theme: Theme
  setTheme: (theme: Theme) => void
  resolvedTheme: "light" | "dark"
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined)

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = useState<Theme>("system")
  const [resolvedTheme, setResolvedTheme] = useState<"light" | "dark">("dark")

  useEffect(() => {
    // Загружаем сохраненную тему
    const savedTheme = localStorage.getItem("tracy_theme") as Theme | null
    if (savedTheme) {
      setThemeState(savedTheme)
    } else {
      // Проверяем системную тему
      if (typeof window !== "undefined") {
        const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches
        setThemeState(prefersDark ? "dark" : "light")
      }
    }
  }, [])

  useEffect(() => {
    // Определяем реальную тему
    let actualTheme: "light" | "dark" = "dark"
    
    if (theme === "system") {
      if (typeof window !== "undefined") {
        actualTheme = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"
      }
    } else {
      actualTheme = theme
    }
    
    setResolvedTheme(actualTheme)
    
    // Применяем тему к документу
    if (typeof window !== "undefined") {
      const root = window.document.documentElement
      if (actualTheme === "dark") {
        root.classList.add("dark")
      } else {
        root.classList.remove("dark")
      }
    }
  }, [theme])

  // Слушаем изменения системной темы
  useEffect(() => {
    if (theme !== "system") return
    
    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)")
    const handleChange = (e: MediaQueryListEvent) => {
      setResolvedTheme(e.matches ? "dark" : "light")
      if (typeof window !== "undefined") {
        const root = window.document.documentElement
        if (e.matches) {
          root.classList.add("dark")
        } else {
          root.classList.remove("dark")
        }
      }
    }
    
    mediaQuery.addEventListener("change", handleChange)
    return () => mediaQuery.removeEventListener("change", handleChange)
  }, [theme])

  const setTheme = (newTheme: Theme) => {
    setThemeState(newTheme)
    localStorage.setItem("tracy_theme", newTheme)
  }

  return (
    <ThemeContext.Provider value={{ theme, setTheme, resolvedTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  const context = useContext(ThemeContext)
  if (context === undefined) {
    throw new Error("useTheme must be used within a ThemeProvider")
  }
  return context
}



