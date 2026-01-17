/**
 * Next.js API Route Handler для проксирования запросов к backend API
 * 
 * Решает проблему CORS в Telegram Mini App WebView
 * Используется как для Mini App, так и для обычного браузера
 */

import { NextRequest, NextResponse } from 'next/server'

// Backend API base URL из переменных окружения
const INTERNAL_API_BASE = process.env.INTERNAL_API_BASE || process.env.NEXT_PUBLIC_API_URL || 'https://api.pasekaproduction.ru'

interface ProxyRequest {
  path: string
  method: 'GET' | 'POST' | 'PUT' | 'DELETE'
  body?: any
  params?: Record<string, any>
}

export async function POST(request: NextRequest) {
  try {
    // Получаем данные запроса
    const proxyData: ProxyRequest = await request.json()
    
    const { path, method, body, params } = proxyData
    
    if (!path) {
      return NextResponse.json(
        { error: 'path is required' },
        { status: 400 }
      )
    }
    
    // Строим URL с параметрами
    const url = new URL(path, INTERNAL_API_BASE)
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        url.searchParams.append(key, String(value))
      })
    }
    
    console.log(`[Proxy] ${method} ${url.toString()}`)
    
    // Выполняем запрос к backend
    const fetchOptions: RequestInit = {
      method,
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': 'Tracy-WebApp-Proxy/1.0',
      },
    }
    
    if (body && (method === 'POST' || method === 'PUT')) {
      fetchOptions.body = JSON.stringify(body)
    }
    
    const response = await fetch(url.toString(), fetchOptions)
    
    // Получаем данные
    let data: any
    const contentType = response.headers.get('content-type')
    
    if (contentType?.includes('application/json')) {
      data = await response.json()
    } else {
      data = await response.text()
    }
    
    console.log(`[Proxy] Response: ${response.status}`)
    
    // Возвращаем ответ с тем же статусом
    return NextResponse.json(data, { 
      status: response.status,
      headers: {
        'Content-Type': 'application/json',
      }
    })
    
  } catch (error: any) {
    console.error('[Proxy] Error:', error)
    
    // Обработка различных типов ошибок
    if (error.name === 'AbortError' || error.message?.includes('timeout')) {
      return NextResponse.json(
        { error: 'Request timeout', details: error.message },
        { status: 504 }
      )
    }
    
    if (error.message?.includes('ECONNREFUSED') || error.message?.includes('ENOTFOUND')) {
      return NextResponse.json(
        { error: 'Backend API unavailable', details: error.message },
        { status: 503 }
      )
    }
    
    return NextResponse.json(
      { error: 'Proxy error', details: error.message },
      { status: 500 }
    )
  }
}

// Методы GET, PUT, DELETE тоже поддерживаем
export async function GET(request: NextRequest) {
  return NextResponse.json(
    { 
      error: 'Use POST method with body: { path, method, params, body }',
      example: {
        path: '/api/events',
        method: 'GET',
        params: { user_id: 123 }
      }
    },
    { status: 405 }
  )
}

