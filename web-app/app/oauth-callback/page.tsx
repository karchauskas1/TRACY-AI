'use client'

import { useEffect, useState } from 'react'

export default function OAuthCallbackPage() {
  const [status, setStatus] = useState<'loading' | 'success' | 'error' | 'no-code'>('loading')
  const [url, setUrl] = useState('')

  useEffect(() => {
    const currentUrl = window.location.href
    setUrl(currentUrl)

    const params = new URLSearchParams(window.location.search)
    const code = params.get('code')
    const error = params.get('error')

    if (error) {
      setStatus('error')
    } else if (code) {
      setStatus('success')
    } else {
      setStatus('no-code')
    }
  }, [])

  const copyURL = () => {
    navigator.clipboard.writeText(url).then(() => {
      alert('✅ URL скопирован! Теперь отправь его боту TRACY в Telegram.')
    }).catch(() => {
      // Fallback для старых браузеров
      const textarea = document.createElement('textarea')
      textarea.value = url
      document.body.appendChild(textarea)
      textarea.select()
      document.execCommand('copy')
      document.body.removeChild(textarea)
      alert('✅ URL скопирован! Теперь отправь его боту TRACY в Telegram.')
    })
  }

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '20px',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
    }}>
      <div style={{
        background: 'white',
        borderRadius: '20px',
        padding: '40px',
        maxWidth: '600px',
        width: '100%',
        boxShadow: '0 20px 60px rgba(0,0,0,0.3)'
      }}>
        <h1 style={{ color: '#333', marginBottom: '20px', fontSize: '28px' }}>
          🔐 TRACY - Подключение Google Calendar
        </h1>
        
        {status === 'loading' && (
          <div style={{
            padding: '20px',
            borderRadius: '10px',
            background: '#d1ecf1',
            border: '1px solid #bee5eb',
            color: '#0c5460',
            marginBottom: '20px'
          }}>
            <strong>⏳ Обработка авторизации...</strong>
          </div>
        )}

        {status === 'success' && (
          <>
            <div style={{
              padding: '20px',
              borderRadius: '10px',
              background: '#d4edda',
              border: '1px solid #c3e6cb',
              color: '#155724',
              marginBottom: '20px'
            }}>
              <strong>✅ Код авторизации получен!</strong><br />
              Теперь скопируй URL и отправь боту.
            </div>
            <div style={{
              background: '#fff3cd',
              border: '1px solid #ffeaa7',
              borderRadius: '8px',
              padding: '20px',
              margin: '20px 0'
            }}>
              <strong>📋 Инструкция:</strong>
              <ol style={{ marginLeft: '20px', marginTop: '10px' }}>
                <li style={{ margin: '8px 0', lineHeight: '1.6' }}>Скопируй <strong>весь URL</strong> из адресной строки браузера</li>
                <li style={{ margin: '8px 0', lineHeight: '1.6' }}>Открой бота TRACY в Telegram</li>
                <li style={{ margin: '8px 0', lineHeight: '1.6' }}>Отправь скопированный URL боту</li>
                <li style={{ margin: '8px 0', lineHeight: '1.6' }}>Бот обработает код и подключит Google Calendar</li>
              </ol>
            </div>
            <div style={{
              background: '#f8f9fa',
              border: '2px solid #dee2e6',
              borderRadius: '8px',
              padding: '15px',
              margin: '20px 0',
              wordBreak: 'break-all',
              fontFamily: "'Courier New', monospace",
              fontSize: '14px',
              color: '#212529'
            }}>
              {url}
            </div>
            <button
              onClick={copyURL}
              style={{
                display: 'inline-block',
                background: '#28a745',
                color: 'white',
                padding: '12px 24px',
                borderRadius: '8px',
                border: 'none',
                fontSize: '16px',
                fontWeight: '600',
                cursor: 'pointer',
                marginTop: '20px'
              }}
              onMouseOver={(e) => e.currentTarget.style.background = '#218838'}
              onMouseOut={(e) => e.currentTarget.style.background = '#28a745'}
            >
              📋 Копировать URL
            </button>
          </>
        )}

        {status === 'error' && (
          <>
            <div style={{
              padding: '20px',
              borderRadius: '10px',
              background: '#f8d7da',
              border: '1px solid #f5c6cb',
              color: '#721c24',
              marginBottom: '20px'
            }}>
              <strong>❌ Ошибка авторизации</strong>
              <p style={{ marginTop: '10px' }}>В URL есть параметр error. Отправь этот URL боту TRACY, и он покажет детали ошибки.</p>
            </div>
            <div style={{
              background: '#f8f9fa',
              border: '2px solid #dee2e6',
              borderRadius: '8px',
              padding: '15px',
              margin: '20px 0',
              wordBreak: 'break-all',
              fontFamily: "'Courier New', monospace",
              fontSize: '14px',
              color: '#212529'
            }}>
              {url}
            </div>
            <button
              onClick={copyURL}
              style={{
                display: 'inline-block',
                background: '#28a745',
                color: 'white',
                padding: '12px 24px',
                borderRadius: '8px',
                border: 'none',
                fontSize: '16px',
                fontWeight: '600',
                cursor: 'pointer',
                marginTop: '20px'
              }}
              onMouseOver={(e) => e.currentTarget.style.background = '#218838'}
              onMouseOut={(e) => e.currentTarget.style.background = '#28a745'}
            >
              📋 Копировать URL
            </button>
          </>
        )}

        {status === 'no-code' && (
          <div style={{
            padding: '20px',
            borderRadius: '10px',
            background: '#fff3cd',
            border: '1px solid #ffeaa7',
            margin: '20px 0'
          }}>
            <strong>⚠️ Не найден код авторизации</strong>
            <p style={{ marginTop: '10px' }}>В URL отсутствует параметр code. Убедись, что ты прошел полную авторизацию в Google.</p>
            <p style={{ marginTop: '10px' }}>Попробуй еще раз через настройки бота.</p>
          </div>
        )}
      </div>
    </div>
  )
}

