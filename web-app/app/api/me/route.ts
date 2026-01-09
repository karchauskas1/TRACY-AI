import { NextRequest, NextResponse } from "next/server"
import { getSession } from "@/lib/auth"
import { prisma } from "@/lib/prisma"

export async function GET(request: NextRequest) {
  const session = await getSession(request)
  if (!session) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  const user = await prisma.user.findUnique({
    where: { id: session.id },
    select: {
      id: true,
      telegramId: true,
      name: true,
      avatarUrl: true,
      locale: true,
      timezone: true,
      timeFormat: true,
    },
  })

  return NextResponse.json(user)
}

export async function PATCH(request: NextRequest) {
  const session = await getSession(request)
  if (!session) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  const body = await request.json()
  const { locale, timezone, timeFormat } = body

  const user = await prisma.user.update({
    where: { id: session.id },
    data: {
      ...(locale && { locale }),
      ...(timezone && { timezone }),
      ...(timeFormat && { timeFormat }),
    },
    select: {
      id: true,
      telegramId: true,
      name: true,
      avatarUrl: true,
      locale: true,
      timezone: true,
      timeFormat: true,
    },
  })

  return NextResponse.json(user)
}

