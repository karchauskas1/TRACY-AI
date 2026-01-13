"use client"

import { useState } from "react"

export default function ClickTestPage() {
  const [clicks, setClicks] = useState<string[]>([])

  const addClick = (type: string) => {
    const timestamp = new Date().toLocaleTimeString()
    setClicks(prev => [`${timestamp}: ${type}`, ...prev].slice(0, 10))
    alert(`✅ Клик работает! Тип: ${type}`)
  }

  return (
    <div style={{ 
      minHeight: '100vh', 
      padding: '20px',
      backgroundColor: '#1a1a20',
      color: 'white',
      fontFamily: 'system-ui'
    }}>
      <h1 style={{ marginBottom: '20px' }}>🧪 Тест кликов</h1>
      
      {/* Тест 1: Обычная кнопка */}
      <button
        onClick={() => addClick('button onClick')}
        style={{
          width: '100%',
          padding: '20px',
          marginBottom: '10px',
          fontSize: '18px',
          backgroundColor: '#8b5cf6',
          color: 'white',
          border: 'none',
          borderRadius: '8px',
          cursor: 'pointer',
          touchAction: 'manipulation'
        }}
      >
        Тест 1: Кнопка onClick
      </button>

      {/* Тест 2: Div с onClick */}
      <div
        onClick={() => addClick('div onClick')}
        style={{
          width: '100%',
          padding: '20px',
          marginBottom: '10px',
          fontSize: '18px',
          backgroundColor: '#10b981',
          color: 'white',
          borderRadius: '8px',
          cursor: 'pointer',
          touchAction: 'manipulation'
        }}
      >
        Тест 2: Div onClick
      </div>

      {/* Тест 3: Div с onTouchStart */}
      <div
        onTouchStart={(e) => {
          e.preventDefault()
          addClick('div onTouchStart')
        }}
        style={{
          width: '100%',
          padding: '20px',
          marginBottom: '10px',
          fontSize: '18px',
          backgroundColor: '#f59e0b',
          color: 'white',
          borderRadius: '8px',
          cursor: 'pointer',
          touchAction: 'manipulation'
        }}
      >
        Тест 3: Div onTouchStart
      </div>

      {/* Тест 4: Ссылка с href */}
      <a
        href="#test"
        onClick={(e) => {
          e.preventDefault()
          addClick('a tag onClick')
        }}
        style={{
          display: 'block',
          width: '100%',
          padding: '20px',
          marginBottom: '10px',
          fontSize: '18px',
          backgroundColor: '#ef4444',
          color: 'white',
          borderRadius: '8px',
          textDecoration: 'none',
          touchAction: 'manipulation'
        }}
      >
        Тест 4: Ссылка onClick
      </a>

      {/* Тест 5: Навигация */}
      <button
        onClick={() => {
          addClick('navigation button')
          const basePath = process.env.NODE_ENV === 'production' ? '/TRACY-AI' : ''
          setTimeout(() => {
            window.location.href = `${basePath}/assistant/`
          }, 1000)
        }}
        style={{
          width: '100%',
          padding: '20px',
          marginBottom: '20px',
          fontSize: '18px',
          backgroundColor: '#06b6d4',
          color: 'white',
          border: 'none',
          borderRadius: '8px',
          cursor: 'pointer',
          touchAction: 'manipulation'
        }}
      >
        Тест 5: Навигация → Assistant
      </button>

      {/* История кликов */}
      <div style={{
        backgroundColor: '#27272a',
        padding: '15px',
        borderRadius: '8px',
        marginTop: '20px'
      }}>
        <h2 style={{ marginBottom: '10px', fontSize: '16px' }}>История кликов:</h2>
        {clicks.length === 0 && (
          <p style={{ color: '#9ca3af' }}>Нажмите на любую кнопку выше</p>
        )}
        {clicks.map((click, i) => (
          <div key={i} style={{ 
            padding: '8px', 
            marginBottom: '5px',
            backgroundColor: '#3f3f46',
            borderRadius: '4px',
            fontSize: '14px'
          }}>
            {click}
          </div>
        ))}
      </div>

      {/* Информация */}
      <div style={{
        backgroundColor: '#1e293b',
        padding: '15px',
        borderRadius: '8px',
        marginTop: '20px',
        fontSize: '12px',
        color: '#94a3b8'
      }}>
        <p><strong>User Agent:</strong> {typeof window !== 'undefined' ? window.navigator.userAgent : 'Loading...'}</p>
        <p><strong>URL:</strong> {typeof window !== 'undefined' ? window.location.href : 'Loading...'}</p>
        <p><strong>Touch Support:</strong> {typeof window !== 'undefined' && 'ontouchstart' in window ? 'Yes ✅' : 'No ❌'}</p>
      </div>
    </div>
  )
}

