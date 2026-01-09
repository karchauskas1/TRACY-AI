import { NextRequest, NextResponse } from "next/server"
import { getSession } from "@/lib/auth"
import { prisma } from "@/lib/prisma"

export async function GET(request: NextRequest) {
  const session = await getSession(request)
  if (!session) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  const { searchParams } = new URL(request.url)
  const from = searchParams.get("from")
  const to = searchParams.get("to")
  const date = searchParams.get("date")

  try {
    let events

    if (date) {
      // Get events for a specific day
      const startOfDay = new Date(date)
      startOfDay.setHours(0, 0, 0, 0)
      const endOfDay = new Date(date)
      endOfDay.setHours(23, 59, 59, 999)

      events = await prisma.event.findMany({
        where: {
          userId: session.id,
          startAt: {
            gte: startOfDay,
            lte: endOfDay,
          },
        },
        include: {
          calendarSource: {
            select: {
              color: true,
              name: true,
            },
          },
        },
        orderBy: {
          startAt: "asc",
        },
      })
    } else if (from && to) {
      // Get events for a date range
      events = await prisma.event.findMany({
        where: {
          userId: session.id,
          startAt: {
            gte: new Date(from),
            lte: new Date(to),
          },
        },
        include: {
          calendarSource: {
            select: {
              color: true,
              name: true,
            },
          },
        },
        orderBy: {
          startAt: "asc",
        },
      })
    } else {
      return NextResponse.json(
        { error: "Missing date or date range" },
        { status: 400 }
      )
    }

    return NextResponse.json({ events })
  } catch (error) {
    console.error("Error fetching events:", error)
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    )
  }
}

export async function POST(request: NextRequest) {
  const session = await getSession(request)
  if (!session) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  try {
    const body = await request.json()
    const {
      title,
      description,
      location,
      startAt,
      endAt,
      allDay,
      calendarSourceId,
      reminders,
    } = body

    const event = await prisma.event.create({
      data: {
        userId: session.id,
        title,
        description,
        location,
        startAt: new Date(startAt),
        endAt: endAt ? new Date(endAt) : null,
        allDay: allDay || false,
        calendarSourceId: calendarSourceId || null,
        reminders: reminders
          ? {
              create: reminders.map((minutes: number) => ({
                minutesBefore: minutes,
              })),
            }
          : undefined,
      },
      include: {
        calendarSource: true,
        reminders: true,
      },
    })

    // TODO: Sync to external calendar if calendarSourceId is set

    return NextResponse.json({ event })
  } catch (error) {
    console.error("Error creating event:", error)
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    )
  }
}

