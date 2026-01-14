import { NextRequest, NextResponse } from 'next/server'
import crypto from 'crypto'

/**
 * Верификация Telegram initData
 * 
 * Telegram передает initData в формате: key=value&key2=value2&hash=...
 * Нужно проверить подпись hash используя HMAC SHA256 с Bot Token
 */
function verifyTelegramInitData(initData: string, botToken: string): { valid: boolean; user?: any } {
  try {
    // Парсим initData
    const params = new URLSearchParams(initData)
    const hash = params.get('hash')
    
    if (!hash) {
      return { valid: false }
    }
    
    // Удаляем hash из параметров для проверки
    params.delete('hash')
    
    // Сортируем параметры по ключу и создаем data-check-string
    // Формат: key=value\nkey2=value2 (каждая пара на новой строке)
    const dataCheckString = Array.from(params.entries())
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([key, value]) => `${key}=${value}`)
      .join('\n')
    
    // Вычисляем секретный ключ: HMAC_SHA256("WebAppData", bot_token)
    const secretKey = crypto
      .createHmac('sha256', 'WebAppData')
      .update(botToken)
      .digest()
    
    // Вычисляем hash: HMAC_SHA256(secret_key, data_check_string)
    const calculatedHash = crypto
      .createHmac('sha256', secretKey)
      .update(dataCheckString)
      .digest('hex')
    
    // Проверяем hash
    if (calculatedHash !== hash) {
      console.error('[Auth] Hash mismatch', {
        calculated: calculatedHash,
        received: hash,
        dataCheckString: dataCheckString.substring(0, 100) + '...',
      })
      return { valid: false }
    }
    
    // Извлекаем user из параметров
    const userStr = params.get('user')
    if (!userStr) {
      return { valid: false }
    }
    
    const user = JSON.parse(decodeURIComponent(userStr))
    
    // Проверяем auth_date (не старше 24 часов)
    const authDate = parseInt(params.get('auth_date') || '0')
    const now = Math.floor(Date.now() / 1000)
    if (now - authDate > 86400) { // 24 часа
      console.error('[Auth] Auth date too old', { authDate, now, diff: now - authDate })
      return { valid: false }
    }
    
    return { valid: true, user }
  } catch (error) {
    console.error('[Auth] Error verifying initData:', error)
    return { valid: false }
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { initData } = body
    
    if (!initData || typeof initData !== 'string') {
      return NextResponse.json(
        { error: 'initData is required' },
        { status: 400 }
      )
    }
    
    // Получаем Bot Token из переменных окружения
    const botToken = process.env.TELEGRAM_BOT_TOKEN
    if (!botToken) {
      console.error('[Auth] TELEGRAM_BOT_TOKEN not set')
      return NextResponse.json(
        { error: 'Server configuration error' },
        { status: 500 }
      )
    }
    
    // Верифицируем initData
    const verification = verifyTelegramInitData(initData, botToken)
    
    if (!verification.valid || !verification.user) {
      return NextResponse.json(
        { error: 'Invalid initData signature' },
        { status: 401 }
      )
    }
    
    // Возвращаем данные пользователя
    // В production здесь можно создать сессию (JWT/cookie)
    return NextResponse.json({
      success: true,
      user: {
        id: verification.user.id.toString(),
        first_name: verification.user.first_name || '',
        last_name: verification.user.last_name || '',
        username: verification.user.username || '',
        photo_url: verification.user.photo_url || '',
      }
    })
    
  } catch (error: any) {
    console.error('[Auth] Error:', error)
    return NextResponse.json(
      { error: 'Internal server error', details: error.message },
      { status: 500 }
    )
  }
}
