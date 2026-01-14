import { NextRequest, NextResponse } from 'next/server'
import { cookies } from 'next/headers'

export async function GET(request: NextRequest) {
  try {
    const cookieStore = await cookies()
    const sessionId = cookieStore.get('tracy_session')
    
    if (!sessionId) {
      return NextResponse.json(
        { error: 'Not authenticated' },
        { status: 401 }
      )
    }
    
    // TODO: Проверить sessionId в БД/Redis и вернуть user data
    // Пока возвращаем успех если cookie есть
    return NextResponse.json({
      success: true,
      authenticated: true,
    })
    
  } catch (error: any) {
    console.error('[Me] Error:', error)
    return NextResponse.json(
      { error: 'Internal server error', details: error.message },
      { status: 500 }
    )
  }
}
