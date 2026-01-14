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
    let lastLogTime = 0
    const throttleMs = 1000

    const handlePointerDown = (e: PointerEvent) => {
      const now = Date.now()
      if (now - lastLogTime < throttleMs) return
      lastLogTime = now

      const target = (e.target as HTMLElement)?.tagName || 'unknown'
      window.__lastClick = {
        type: 'pointerdown',
        target,
        timestamp: now,
      }
      console.log('[ClickProbe] pointerdown', target, e.target)
    }

    const handleClick = (e: MouseEvent) => {
      const now = Date.now()
      if (now - lastLogTime < throttleMs) return
      lastLogTime = now

      const target = (e.target as HTMLElement)?.tagName || 'unknown'
      window.__lastClick = {
        type: 'click',
        target,
        timestamp: now,
      }
      console.log('[ClickProbe] click', target, e.target)
    }

    window.addEventListener('pointerdown', handlePointerDown, true)
    window.addEventListener('click', handleClick, true)

    return () => {
      window.removeEventListener('pointerdown', handlePointerDown, true)
      window.removeEventListener('click', handleClick, true)
    }
  }, [])

  return null
}
