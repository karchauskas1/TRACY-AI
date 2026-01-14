"use client"

import { useEffect, useState, useRef } from "react"
import { usePathname, useRouter } from "next/navigation"

interface DebugInfo {
  pathname: string
  userAgent: string
  isTelegram: boolean
  isMounted: boolean
  lastClick: {
    timestamp: number
    target: string
    className: string
    href?: string
  } | null
  lastNavigationAttempt: string | null
  lastError: {
    message: string
    timestamp: number
  } | null
  eventCounts: {
    pointerdown: number
    click: number
    touchstart: number
  }
  tgBootstrap: {
    readyCalledAt: number | null
    expandCalledAt: number | null
  }
  routerPathname: string
}

export function DebugOverlay() {
  const [isVisible, setIsVisible] = useState(false)
  const [debugInfo, setDebugInfo] = useState<DebugInfo>({
    pathname: "",
    userAgent: "",
    isTelegram: false,
    isMounted: false,
    lastClick: null,
    lastNavigationAttempt: null,
    lastError: null,
    eventCounts: {
      pointerdown: 0,
      click: 0,
      touchstart: 0,
    },
    tgBootstrap: {
      readyCalledAt: null,
      expandCalledAt: null,
    },
    routerPathname: "",
  })

  const pathname = usePathname()
  const router = useRouter()
  const mountedRef = useRef(false)

  useEffect(() => {
    // Проверяем query параметр ?debug=1
    const params = new URLSearchParams(window.location.search)
    if (params.get("debug") === "1") {
      setIsVisible(true)
    }

    // Проверяем mounted state
    mountedRef.current = true
    setDebugInfo((prev) => ({ ...prev, isMounted: true }))

    // Инициализация данных
    setDebugInfo((prev) => ({
      ...prev,
      pathname: window.location.pathname,
      userAgent: navigator.userAgent,
      isTelegram: !!(window as any).Telegram?.WebApp,
      routerPathname: pathname,
    }))

    // Проверяем TelegramBootstrap
    const checkBootstrap = () => {
      const tgBootstrap = (window as any).__tg_bootstrap
      if (tgBootstrap) {
        setDebugInfo((prev) => ({
          ...prev,
          tgBootstrap: {
            readyCalledAt: tgBootstrap.readyCalledAt || null,
            expandCalledAt: tgBootstrap.expandCalledAt || null,
          },
        }))
      }
    }
    checkBootstrap()
    const bootstrapInterval = setInterval(checkBootstrap, 100)

    // Слушаем изменения pathname
    const updatePathname = () => {
      setDebugInfo((prev) => ({
        ...prev,
        routerPathname: pathname,
        pathname: window.location.pathname,
      }))
    }
    updatePathname()

    // Обновляем при изменении pathname
    const pathnameInterval = setInterval(updatePathname, 100)

    // Глобальные обработчики событий (capture phase)
    const handlePointerDown = (e: PointerEvent) => {
      setDebugInfo((prev) => ({
        ...prev,
        eventCounts: {
          ...prev.eventCounts,
          pointerdown: prev.eventCounts.pointerdown + 1,
        },
        lastClick: {
          timestamp: Date.now(),
          target: (e.target as HTMLElement)?.tagName || "unknown",
          className: (e.target as HTMLElement)?.className || "",
          href: (e.target as HTMLAnchorElement)?.href || undefined,
        },
      }))
    }

    const handleClick = (e: MouseEvent) => {
      setDebugInfo((prev) => ({
        ...prev,
        eventCounts: {
          ...prev.eventCounts,
          click: prev.eventCounts.click + 1,
        },
        lastClick: {
          timestamp: Date.now(),
          target: (e.target as HTMLElement)?.tagName || "unknown",
          className: (e.target as HTMLElement)?.className || "",
          href: (e.target as HTMLAnchorElement)?.href || undefined,
        },
      }))
    }

    const handleTouchStart = (e: TouchEvent) => {
      setDebugInfo((prev) => ({
        ...prev,
        eventCounts: {
          ...prev.eventCounts,
          touchstart: prev.eventCounts.touchstart + 1,
        },
        lastClick: {
          timestamp: Date.now(),
          target: (e.target as HTMLElement)?.tagName || "unknown",
          className: (e.target as HTMLElement)?.className || "",
          href: (e.target as HTMLAnchorElement)?.href || undefined,
        },
      }))
    }

    // Добавляем обработчики в capture phase
    window.addEventListener("pointerdown", handlePointerDown, true)
    window.addEventListener("click", handleClick, true)
    window.addEventListener("touchstart", handleTouchStart, true)

    // Перехват навигации через Link
    const originalPushState = history.pushState
    history.pushState = function (...args) {
      setDebugInfo((prev) => ({
        ...prev,
        lastNavigationAttempt: args[2] as string || window.location.pathname,
      }))
      return originalPushState.apply(history, args)
    }

    // Перехват ошибок
    const handleError = (event: ErrorEvent) => {
      setDebugInfo((prev) => ({
        ...prev,
        lastError: {
          message: event.message || String(event.error),
          timestamp: Date.now(),
        },
      }))
    }

    const handleRejection = (event: PromiseRejectionEvent) => {
      setDebugInfo((prev) => ({
        ...prev,
        lastError: {
          message: `Unhandled rejection: ${event.reason}`,
          timestamp: Date.now(),
        },
      }))
    }

    window.addEventListener("error", handleError)
    window.addEventListener("unhandledrejection", handleRejection)

    // Перехват кликов на Link компонентах
    const handleLinkClick = (e: MouseEvent) => {
      const target = e.target as HTMLElement
      const link = target.closest("a")
      if (link && link.href) {
        setDebugInfo((prev) => ({
          ...prev,
          lastNavigationAttempt: link.href,
        }))
      }
    }

    document.addEventListener("click", handleLinkClick, true)

    return () => {
      clearInterval(bootstrapInterval)
      clearInterval(pathnameInterval)
      window.removeEventListener("pointerdown", handlePointerDown, true)
      window.removeEventListener("click", handleClick, true)
      window.removeEventListener("touchstart", handleTouchStart, true)
      window.removeEventListener("error", handleError)
      window.removeEventListener("unhandledrejection", handleRejection)
      document.removeEventListener("click", handleLinkClick, true)
      history.pushState = originalPushState
    }
  }, [pathname])

  const handleManualNav = (path: string, method: "router" | "location") => {
    setDebugInfo((prev) => ({
      ...prev,
      lastNavigationAttempt: path,
    }))

    if (method === "router") {
      console.log("[DebugOverlay] Manual nav via router.push:", path)
      router.push(path)
    } else {
      console.log("[DebugOverlay] Manual nav via window.location.assign:", path)
      window.location.assign(path)
    }
  }

  if (!isVisible) return null

  return (
    <div
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: "rgba(0, 0, 0, 0.9)",
        color: "#fff",
        padding: "16px",
        fontSize: "12px",
        fontFamily: "monospace",
        zIndex: 99999,
        overflow: "auto",
        pointerEvents: "auto",
      }}
    >
      <div style={{ marginBottom: "16px" }}>
        <button
          onClick={() => setIsVisible(false)}
          style={{
            padding: "8px 16px",
            backgroundColor: "#ff4444",
            color: "#fff",
            border: "none",
            borderRadius: "4px",
            cursor: "pointer",
            marginBottom: "16px",
          }}
        >
          Close Debug Overlay
        </button>
      </div>

      <div style={{ marginBottom: "16px" }}>
        <h2 style={{ marginBottom: "8px", color: "#4CAF50" }}>Debug Info</h2>
        <div style={{ marginBottom: "4px" }}>
          <strong>Pathname:</strong> {debugInfo.pathname}
        </div>
        <div style={{ marginBottom: "4px" }}>
          <strong>Router Pathname:</strong> {debugInfo.routerPathname}
        </div>
        <div style={{ marginBottom: "4px" }}>
          <strong>User Agent:</strong> {debugInfo.userAgent}
        </div>
        <div style={{ marginBottom: "4px" }}>
          <strong>Is Telegram:</strong> {debugInfo.isTelegram ? "✅ YES" : "❌ NO"}
        </div>
        <div style={{ marginBottom: "4px" }}>
          <strong>Is Mounted:</strong> {debugInfo.isMounted ? "✅ YES" : "❌ NO"}
        </div>
      </div>

      <div style={{ marginBottom: "16px" }}>
        <h2 style={{ marginBottom: "8px", color: "#2196F3" }}>Event Counts</h2>
        <div style={{ marginBottom: "4px" }}>
          <strong>pointerdown:</strong> {debugInfo.eventCounts.pointerdown}
        </div>
        <div style={{ marginBottom: "4px" }}>
          <strong>click:</strong> {debugInfo.eventCounts.click}
        </div>
        <div style={{ marginBottom: "4px" }}>
          <strong>touchstart:</strong> {debugInfo.eventCounts.touchstart}
        </div>
      </div>

      <div style={{ marginBottom: "16px" }}>
        <h2 style={{ marginBottom: "8px", color: "#FF9800" }}>Last Click</h2>
        {debugInfo.lastClick ? (
          <>
            <div style={{ marginBottom: "4px" }}>
              <strong>Timestamp:</strong> {new Date(debugInfo.lastClick.timestamp).toLocaleTimeString()}
            </div>
            <div style={{ marginBottom: "4px" }}>
              <strong>Target:</strong> {debugInfo.lastClick.target}
            </div>
            <div style={{ marginBottom: "4px" }}>
              <strong>Class:</strong> {debugInfo.lastClick.className || "(none)"}
            </div>
            {debugInfo.lastClick.href && (
              <div style={{ marginBottom: "4px" }}>
                <strong>Href:</strong> {debugInfo.lastClick.href}
              </div>
            )}
          </>
        ) : (
          <div>No clicks yet</div>
        )}
      </div>

      <div style={{ marginBottom: "16px" }}>
        <h2 style={{ marginBottom: "8px", color: "#9C27B0" }}>Telegram Bootstrap</h2>
        <div style={{ marginBottom: "4px" }}>
          <strong>ready() called at:</strong>{" "}
          {debugInfo.tgBootstrap.readyCalledAt
            ? new Date(debugInfo.tgBootstrap.readyCalledAt).toLocaleTimeString()
            : "❌ NOT CALLED"}
        </div>
        <div style={{ marginBottom: "4px" }}>
          <strong>expand() called at:</strong>{" "}
          {debugInfo.tgBootstrap.expandCalledAt
            ? new Date(debugInfo.tgBootstrap.expandCalledAt).toLocaleTimeString()
            : "❌ NOT CALLED"}
        </div>
      </div>

      <div style={{ marginBottom: "16px" }}>
        <h2 style={{ marginBottom: "8px", color: "#F44336" }}>Navigation</h2>
        <div style={{ marginBottom: "4px" }}>
          <strong>Last Navigation Attempt:</strong>{" "}
          {debugInfo.lastNavigationAttempt || "(none)"}
        </div>
      </div>

      <div style={{ marginBottom: "16px" }}>
        <h2 style={{ marginBottom: "8px", color: "#FF5722" }}>Errors</h2>
        {debugInfo.lastError ? (
          <>
            <div style={{ marginBottom: "4px" }}>
              <strong>Message:</strong> {debugInfo.lastError.message}
            </div>
            <div style={{ marginBottom: "4px" }}>
              <strong>Timestamp:</strong>{" "}
              {new Date(debugInfo.lastError.timestamp).toLocaleTimeString()}
            </div>
          </>
        ) : (
          <div>No errors</div>
        )}
      </div>

      <div style={{ marginBottom: "16px" }}>
        <h2 style={{ marginBottom: "8px", color: "#00BCD4" }}>Manual Navigation</h2>
        <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
          <button
            onClick={() => handleManualNav("/chat", "router")}
            style={{
              padding: "8px 16px",
              backgroundColor: "#2196F3",
              color: "#fff",
              border: "none",
              borderRadius: "4px",
              cursor: "pointer",
            }}
          >
            /chat (router.push)
          </button>
          <button
            onClick={() => handleManualNav("/calendar", "router")}
            style={{
              padding: "8px 16px",
              backgroundColor: "#2196F3",
              color: "#fff",
              border: "none",
              borderRadius: "4px",
              cursor: "pointer",
            }}
          >
            /calendar (router.push)
          </button>
          <button
            onClick={() => handleManualNav("/chat", "location")}
            style={{
              padding: "8px 16px",
              backgroundColor: "#FF9800",
              color: "#fff",
              border: "none",
              borderRadius: "4px",
              cursor: "pointer",
            }}
          >
            /chat (location.assign)
          </button>
          <button
            onClick={() => handleManualNav("/calendar", "location")}
            style={{
              padding: "8px 16px",
              backgroundColor: "#FF9800",
              color: "#fff",
              border: "none",
              borderRadius: "4px",
              cursor: "pointer",
            }}
          >
            /calendar (location.assign)
          </button>
        </div>
      </div>
    </div>
  )
}
