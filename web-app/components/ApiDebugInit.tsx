"use client"

import { useEffect } from "react"
import { getApiDebugger } from "../lib/apiDebug"

/**
 * Компонент для инициализации API debug системы
 * Должен быть добавлен в layout для автоматической инициализации
 */
export function ApiDebugInit() {
  useEffect(() => {
    // Инициализируем API debug систему при монтировании
    getApiDebugger()
  }, [])
  
  return null
}

