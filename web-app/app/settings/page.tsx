"use client"

import { useState, useEffect } from "react"
import { SettingsPageClient } from "./SettingsPageClient"

export default function SettingsPage() {
  const [user, setUser] = useState<any>(null)

  useEffect(() => {
    // Для статического экспорта получаем пользователя из localStorage
    const userStr = localStorage.getItem("telegram_user")
    if (userStr) {
      try {
        setUser(JSON.parse(userStr))
      } catch (e) {
        console.error("Failed to parse user:", e)
      }
    }
  }, [])
  
  return <SettingsPageClient user={user} />
}

