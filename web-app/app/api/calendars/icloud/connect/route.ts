import { NextRequest, NextResponse } from "next/server"
import { getSession } from "@/lib/auth"
import { prisma } from "@/lib/prisma"

export async function POST(request: NextRequest) {
  const session = await getSession(request)
  if (!session) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  try {
    const body = await request.json()
    const { email, password, serverUrl } = body

    if (!email || !password) {
      return NextResponse.json(
        { error: "Email and password required" },
        { status: 400 }
      )
    }

    const caldavUrl = serverUrl || `https://caldav.icloud.com:443/`

    // Test connection and discover calendars
    // For MVP, we'll create a basic connection
    // In production, implement proper CalDAV client using HTTP requests
    // CalDAV uses PROPFIND requests to discover calendars
    const calendars: any[] = [
      {
        url: `${caldavUrl}calendars/${email}/`,
        displayName: "iCloud Calendar",
      },
    ]

    // Create connection
    const connection = await prisma.calendarConnection.create({
      data: {
        userId: session.id,
        provider: "icloud",
        credentials: {
          email,
          password, // In production, encrypt this
          serverUrl: caldavUrl,
        },
      },
    })

    // Create calendar sources
    for (const cal of calendars) {
      await prisma.calendarSource.create({
        data: {
          connectionId: connection.id,
          userId: session.id,
          externalId: cal.url,
          name: cal.displayName || "iCloud Calendar",
          color: "#3b82f6",
          isDefault: false,
        },
      })
    }

    return NextResponse.json({ success: true, connectionId: connection.id })
  } catch (error: any) {
    console.error("iCloud connection error:", error)
    return NextResponse.json(
      { error: error.message || "Failed to connect to iCloud" },
      { status: 500 }
    )
  }
}

