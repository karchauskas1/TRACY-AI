import { NextRequest, NextResponse } from "next/server"
import { getSession } from "@/lib/auth"
import { prisma } from "@/lib/prisma"

export async function GET(request: NextRequest) {
  const session = await getSession(request)
  if (!session) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  try {
    const meetings = await prisma.meeting.findMany({
      where: { userId: session.id },
      orderBy: { createdAt: "desc" },
      take: 50,
    })

    return NextResponse.json({ meetings })
  } catch (error) {
    console.error("Error fetching meetings:", error)
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
    const formData = await request.formData()
    const file = formData.get("file") as File

    if (!file) {
      return NextResponse.json(
        { error: "No file provided" },
        { status: 400 }
      )
    }

    // TODO: Upload file to storage (Supabase or local)
    // For MVP, we'll store the file reference
    const audioUrl = `/uploads/${Date.now()}-${file.name}`

    // Create meeting
    const meeting = await prisma.meeting.create({
      data: {
        userId: session.id,
        title: file.name,
        audioUrl,
        status: "processing",
      },
    })

    // Create job for processing
    await prisma.job.create({
      data: {
        userId: session.id,
        type: "meeting_transcribe",
        status: "queued",
        payload: {
          audioUrl,
          meetingId: meeting.id,
        },
      },
    })

    // Trigger job processing (in production, use a queue system)
    // For MVP, we'll process it immediately
    fetch(`${process.env.NEXTAUTH_URL || "http://localhost:3000"}/api/jobs/run`, {
      method: "POST",
    }).catch(console.error)

    return NextResponse.json({ meeting })
  } catch (error) {
    console.error("Error creating meeting:", error)
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    )
  }
}

