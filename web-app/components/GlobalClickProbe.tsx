"use client"

import { useEffect } from "react"

declare global {
  interface Window {
    __lastClick?: {
      type: string
      target: string
      timestamp: number
    }
  }
}

export function GlobalClickProbe() {
  useEffect(() => {
    // Проверяем debug режим
    const params = new URLSearchParams(window.location.search)
    const debugMode = params.get('debug') === '1'

    let lastLogTime = 0
    const throttleMs = debugMode ? 0 : 1000 // В debug режиме логируем все события

    const logEvent = (type: string, e: Event) => {
      const now = Date.now()
      if (!debugMode && now - lastLogTime < throttleMs) return
      lastLogTime = now

      const target = (e.target as HTMLElement)?.tagName || 'unknown'
      const eventInfo = {
        type,
        target,
        defaultPrevented: e.defaultPrevented,
        cancelBubble: (e as any).cancelBubble || false,
        eventPhase: e.eventPhase, // 1=CAPTURING, 2=AT_TARGET, 3=BUBBLING
        timestamp: now,
      }

      window.__lastClick = {
        type,
        target,
        timestamp: now,
      }

      if (debugMode) {
        console.log(`[ClickProbe] ${type}`, eventInfo, {
          target: e.target,
          currentTarget: e.currentTarget,
        })
      } else {
        console.log(`[ClickProbe] ${type}`, target, e.target)
      }
    }

    const handlePointerDown = (e: PointerEvent) => {
      logEvent('pointerdown', e)
    }

    const handlePointerUp = (e: PointerEvent) => {
      logEvent('pointerup', e)
    }

    const handleTouchStart = (e: TouchEvent) => {
      logEvent('touchstart', e)
    }

    const handleTouchEnd = (e: TouchEvent) => {
      logEvent('touchend', e)
    }

    const handleMouseDown = (e: MouseEvent) => {
      logEvent('mousedown', e)
    }

    const handleMouseUp = (e: MouseEvent) => {
      logEvent('mouseup', e)
    }

    const handleClick = (e: MouseEvent) => {
      logEvent('click', e)
    }

    // Добавляем все обработчики в capture phase (true)
    window.addEventListener('pointerdown', handlePointerDown, true)
    window.addEventListener('pointerup', handlePointerUp, true)
    window.addEventListener('touchstart', handleTouchStart, true)
    window.addEventListener('touchend', handleTouchEnd, true)
    window.addEventListener('mousedown', handleMouseDown, true)
    window.addEventListener('mouseup', handleMouseUp, true)
    window.addEventListener('click', handleClick, true)

    return () => {
      window.removeEventListener('pointerdown', handlePointerDown, true)
      window.removeEventListener('pointerup', handlePointerUp, true)
      window.removeEventListener('touchstart', handleTouchStart, true)
      window.removeEventListener('touchend', handleTouchEnd, true)
      window.removeEventListener('mousedown', handleMouseDown, true)
      window.removeEventListener('mouseup', handleMouseUp, true)
      window.removeEventListener('click', handleClick, true)
    }
  }, [])

  return null
}
