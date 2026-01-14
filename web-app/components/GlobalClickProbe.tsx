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
    const isTelegramWebApp = !!(window as any).Telegram?.WebApp

    // Важно: НЕ используем общий throttle на все события.
    // Иначе короткий тап может дать только pointerdown в логах (а pointerup/click "съедаются").
    const lastLogTimeByType = new Map<string, number>()
    const throttleMs = debugMode ? 0 : 1000 // В debug режиме логируем ВСЕ события без фильтрации

    // Диагностика/фолбэк: в некоторых WebView click может не приходить после pointerup/touchend.
    // Для Telegram Mini App делаем безопасный synth-click по завершению "тапа",
    // но только если реальный click НЕ пришёл в течение короткого окна.
    let lastClickSeenAt = 0
    let lastNavRescueAt = 0
    let lastPointerDown:
      | { x: number; y: number; time: number; pointerType?: string; target: EventTarget | null }
      | null = null
    let lastTouchStart: { x: number; y: number; time: number; target: EventTarget | null } | null = null

    const logEvent = (type: string, e: Event) => {
      const now = Date.now()
      if (!debugMode && throttleMs > 0) {
        const last = lastLogTimeByType.get(type) || 0
        if (now - last < throttleMs) return
        lastLogTimeByType.set(type, now)
      }

      const target = (e.target as HTMLElement)?.tagName || 'unknown'
      const asAny = e as any
      const coords =
        typeof asAny.clientX === 'number' && typeof asAny.clientY === 'number'
          ? { clientX: asAny.clientX, clientY: asAny.clientY }
          : undefined
      const eventInfo = {
        type,
        target,
        capture: true,
        defaultPrevented: e.defaultPrevented,
        cancelBubble: (e as any).cancelBubble || false,
        eventPhase: e.eventPhase, // 1=CAPTURING, 2=AT_TARGET, 3=BUBBLING
        isTrusted: (e as any).isTrusted ?? undefined,
        pointerType: (e as any).pointerType ?? undefined,
        buttons: (e as any).buttons ?? undefined,
        ...coords,
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
      lastPointerDown = {
        x: e.clientX,
        y: e.clientY,
        time: Date.now(),
        pointerType: e.pointerType,
        target: e.target,
      }
      logEvent('pointerdown', e)
    }

    const handlePointerUp = (e: PointerEvent) => {
      logEvent('pointerup', e)

      // Telegram-only: synth click для "тапа" если click не пришёл сам
      if (!isTelegramWebApp) return
      const down = lastPointerDown
      if (!down) return
      const now = Date.now()
      const dx = Math.abs(down.x - e.clientX)
      const dy = Math.abs(down.y - e.clientY)
      const isTap = dx <= 12 && dy <= 12 && now - down.time <= 800
      if (!isTap) return
      // Для мыши click должен приходить штатно
      if (e.pointerType === 'mouse') return

      const originTime = now
      const originTarget = e.target
      const x = e.clientX
      const y = e.clientY
      setTimeout(() => {
        // Если click уже пришёл — ничего не делаем
        if (lastClickSeenAt >= originTime) return

        const rawTarget = (originTarget as HTMLElement | null) || (document.elementFromPoint(x, y) as HTMLElement | null)
        const clickable = rawTarget?.closest?.('a[href],button,input,select,textarea,[role="button"]') as HTMLElement | null
        if (!clickable) return

        const asBtn = clickable as HTMLButtonElement
        if (typeof asBtn.disabled === 'boolean' && asBtn.disabled) return

        if (debugMode) {
          console.log('[ClickProbe] synth-click (pointerup)', {
            tag: clickable.tagName,
            id: clickable.id,
            className: clickable.className,
          })
        }
        clickable.dispatchEvent(
          new MouseEvent('click', {
            bubbles: true,
            cancelable: true,
            composed: true,
            view: window,
            clientX: x,
            clientY: y,
          })
        )
      }, 160)
    }

    const handleTouchStart = (e: TouchEvent) => {
      const t = e.touches?.[0]
      if (t) {
        lastTouchStart = { x: t.clientX, y: t.clientY, time: Date.now(), target: e.target }
      }
      logEvent('touchstart', e)
    }

    const handleTouchEnd = (e: TouchEvent) => {
      logEvent('touchend', e)

      // Telegram-only: synth click если click не пришёл сам
      if (!isTelegramWebApp) return
      const start = lastTouchStart
      const t = e.changedTouches?.[0]
      if (!start || !t) return
      const now = Date.now()
      const dx = Math.abs(start.x - t.clientX)
      const dy = Math.abs(start.y - t.clientY)
      const isTap = dx <= 12 && dy <= 12 && now - start.time <= 800
      if (!isTap) return

      const originTime = now
      const originTarget = e.target
      const x = t.clientX
      const y = t.clientY
      setTimeout(() => {
        if (lastClickSeenAt >= originTime) return

        const rawTarget = (originTarget as HTMLElement | null) || (document.elementFromPoint(x, y) as HTMLElement | null)
        const clickable = rawTarget?.closest?.('a[href],button,input,select,textarea,[role="button"]') as HTMLElement | null
        if (!clickable) return

        const asBtn = clickable as HTMLButtonElement
        if (typeof asBtn.disabled === 'boolean' && asBtn.disabled) return

        if (debugMode) {
          console.log('[ClickProbe] synth-click (touchend)', {
            tag: clickable.tagName,
            id: clickable.id,
            className: clickable.className,
          })
        }
        clickable.dispatchEvent(
          new MouseEvent('click', {
            bubbles: true,
            cancelable: true,
            composed: true,
            view: window,
            clientX: x,
            clientY: y,
          })
        )
      }, 160)
    }

    const handleMouseDown = (e: MouseEvent) => {
      logEvent('mousedown', e)
    }

    const handleMouseUp = (e: MouseEvent) => {
      logEvent('mouseup', e)
    }

    const handleClick = (e: MouseEvent) => {
      // Фиксируем факт прихода click (нужно, чтобы не делать synth-click поверх реального)
      lastClickSeenAt = Date.now()
      logEvent('click', e)

      // Telegram-only: если клики есть, но Next/React навигация не срабатывает,
      // делаем "nav rescue" для внутренних ссылок.
      // Сначала пробуем мягко: history.pushState + PopStateEvent (без полного reload).
      // Если по какой-то причине URL не меняется — fallback на window.location.assign().
      if (!isTelegramWebApp) return

      const targetEl = e.target as HTMLElement | null
      const link = (targetEl?.closest?.('a[href]') as HTMLAnchorElement | null) || null
      if (!link) return

      // Не трогаем внешние ссылки и target != _self
      const rawHref = link.getAttribute('href')
      if (!rawHref || rawHref.startsWith('#')) return
      if (link.target && link.target !== '_self') return

      let url: URL
      try {
        url = new URL(link.href, window.location.href)
      } catch {
        return
      }
      if (url.origin !== window.location.origin) return

      const beforeHref = window.location.href
      const scheduledAt = Date.now()
      setTimeout(() => {
        // Если навигация уже произошла — выходим
        if (window.location.href !== beforeHref) return

        // Дребезг/защита от циклов
        const now = Date.now()
        if (now - lastNavRescueAt < 500) return

        // Если слишком поздно — тоже не делаем
        if (now - scheduledAt > 1500) return

        lastNavRescueAt = now
        if (debugMode) {
          console.log('[ClickProbe] nav-rescue assign', {
            from: beforeHref,
            to: url.toString(),
            defaultPrevented: e.defaultPrevented,
            cancelBubble: (e as any).cancelBubble || false,
          })
        }
        try {
          const nextUrl = url.pathname + url.search + url.hash
          history.pushState(null, "", nextUrl)
          window.dispatchEvent(new PopStateEvent("popstate"))
        } catch {
          window.location.assign(url.toString())
        }
      }, 140)
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
