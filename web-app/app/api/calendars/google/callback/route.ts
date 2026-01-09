import { NextRequest, NextResponse } from "next/server"
import { getSession } from "@/lib/auth"
import { prisma } from "@/lib/prisma"
import { google } from "googleapis"

const CLIENT_ID = process.env.GOOGLE_CLIENT_ID
const CLIENT_SECRET = process.env.GOOGLE_CLIENT_SECRET
const REDIRECT_URI = process.env.GOOGLE_REDIRECT_URI || "http://localhost:3000/api/calendars/google/callback"

export async function GET(request: NextRequest) {
  const session = await getSession(request)
  if (!session) {
    return NextResponse.redirect(new URL("/login", request.url))
  }

  const { searchParams } = new URL(request.url)
  const code = searchParams.get("code")
  const state = searchParams.get("state") // User ID

  if (!code) {
    return NextResponse.redirect(new URL("/settings/calendars?error=no_code", request.url))
  }

  try {
    const oauth2Client = new google.auth.OAuth2(
      CLIENT_ID,
      CLIENT_SECRET,
      REDIRECT_URI
    )

    const { tokens } = await oauth2Client.getToken(code)
    oauth2Client.setCredentials(tokens)

    // Get calendar list
    const calendar = google.calendar({ version: "v3", auth: oauth2Client })
    const calendarsList = await calendar.calendarList.list()

    // Create connection
    // Convert tokens to JSON-compatible format
    const credentialsJson = {
      access_token: tokens.access_token,
      refresh_token: tokens.refresh_token,
      scope: tokens.scope,
      token_type: tokens.token_type,
      expiry_date: tokens.expiry_date,
    }
    
    const connection = await prisma.calendarConnection.create({
      data: {
        userId: session.id,
        provider: "google",
        credentials: credentialsJson as any, // In production, encrypt this
      },
    })

    // Create calendar sources
    if (calendarsList.data.items) {
      for (const cal of calendarsList.data.items) {
        if (cal.id) {
          await prisma.calendarSource.create({
            data: {
              connectionId: connection.id,
              userId: session.id,
              externalId: cal.id,
              name: cal.summary || "Unnamed Calendar",
              color: cal.backgroundColor || "#3b82f6",
              isDefault: cal.primary || false,
            },
          })
        }
      }
    }

    return NextResponse.redirect(new URL("/settings/calendars?success=google_connected", request.url))
  } catch (error) {
    console.error("Google OAuth error:", error)
    return NextResponse.redirect(new URL("/settings/calendars?error=oauth_failed", request.url))
  }
}

