import { NextRequest, NextResponse } from "next/server"
import { getSession } from "@/lib/auth"
import { prisma } from "@/lib/prisma"

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  const session = await getSession(request)
  if (!session) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  try {
    const event = await prisma.event.findFirst({
      where: {
        id: params.id,
        userId: session.id,
      },
      include: {
        calendarSource: true,
        reminders: {
          orderBy: {
            minutesBefore: "asc",
          },
        },
      },
    })

    if (!event) {
      return NextResponse.json({ error: "Event not found" }, { status: 404 })
    }

    return NextResponse.json({ event })
  } catch (error) {
    console.error("Error fetching event:", error)
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    )
  }
}

export async function PATCH(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  const session = await getSession(request)
  if (!session) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  try {
    const body = await request.json()
    const { title, description, location, startAt, endAt, allDay, reminders } =
      body

    // Delete existing reminders
    await prisma.reminder.deleteMany({
      where: { eventId: params.id },
    })

    const event = await prisma.event.update({
      where: {
        id: params.id,
        userId: session.id,
      },
      data: {
        ...(title && { title }),
        ...(description !== undefined && { description }),
        ...(location !== undefined && { location }),
        ...(startAt && { startAt: new Date(startAt) }),
        ...(endAt !== undefined && { endAt: endAt ? new Date(endAt) : null }),
        ...(allDay !== undefined && { allDay }),
        ...(reminders && {
          reminders: {
            create: reminders.map((minutes: number) => ({
              minutesBefore: minutes,
            })),
          },
        }),
      },
      include: {
        calendarSource: true,
        reminders: true,
      },
    })

    // TODO: Sync to external calendar

    return NextResponse.json({ event })
  } catch (error) {
    console.error("Error updating event:", error)
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    )
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  const session = await getSession(request)
  if (!session) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  try {
    await prisma.event.delete({
      where: {
        id: params.id,
        userId: session.id,
      },
    })

    // TODO: Delete from external calendar

    return NextResponse.json({ success: true })
  } catch (error) {
    console.error("Error deleting event:", error)
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    )
  }
}

