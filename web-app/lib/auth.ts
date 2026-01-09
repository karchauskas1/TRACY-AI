import { NextRequest } from 'next/server'
import { prisma } from './prisma'
import * as jwt from 'jsonwebtoken'

const JWT_SECRET = process.env.NEXTAUTH_SECRET || 'your-secret-key'

export interface SessionUser {
  id: string
  telegramId: string
  name: string
  avatarUrl?: string
}

export async function getSession(request: NextRequest): Promise<SessionUser | null> {
  try {
    const token = request.cookies.get('session')?.value
    if (!token) return null

    const decoded = jwt.verify(token, JWT_SECRET) as { userId: string }
    const user = await prisma.user.findUnique({
      where: { id: decoded.userId },
      select: {
        id: true,
        telegramId: true,
        name: true,
        avatarUrl: true,
      },
    })

    return user ? {
      id: user.id,
      telegramId: user.telegramId,
      name: user.name,
      avatarUrl: user.avatarUrl || undefined,
    } : null
  } catch {
    return null
  }
}

export function createSession(userId: string): string {
  return jwt.sign({ userId }, JWT_SECRET, { expiresIn: '30d' })
}

export async function createOrUpdateUser(telegramData: {
  id: string
  first_name: string
  last_name?: string
  username?: string
  photo_url?: string
}): Promise<SessionUser> {
  const name = `${telegramData.first_name} ${telegramData.last_name || ''}`.trim()
  const avatarUrl = telegramData.photo_url

  const user = await prisma.user.upsert({
    where: { telegramId: telegramData.id },
    update: {
      name,
      avatarUrl,
    },
    create: {
      telegramId: telegramData.id,
      name,
      avatarUrl,
    },
  })

  return {
    id: user.id,
    telegramId: user.telegramId,
    name: user.name,
    avatarUrl: user.avatarUrl || undefined,
  }
}

