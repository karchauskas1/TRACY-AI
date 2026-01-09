import { NextRequest, NextResponse } from "next/server"
import { getSession } from "@/lib/auth"
import { prisma } from "@/lib/prisma"

export async function GET(request: NextRequest) {
  const session = await getSession(request)
  if (!session) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  try {
    const connections = await prisma.calendarConnection.findMany({
      where: { userId: session.id },
      include: {
        calendarSources: {
          where: { isEnabled: true },
          orderBy: { isDefault: "desc" },
        },
      },
    })

    return NextResponse.json({ connections })
  } catch (error) {
    console.error("Error fetching calendars:", error)
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    )
  }
}

