import { NextRequest, NextResponse } from "next/server"
import { prisma } from "@/lib/prisma"
import OpenAI from "openai"

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
})

export async function POST(request: NextRequest) {
  // This endpoint should be called periodically (via cron or scheduled task)
  // For MVP, we'll process one job at a time

  try {
    // Find next queued job
    const job = await prisma.job.findFirst({
      where: {
        status: "queued",
      },
      orderBy: {
        createdAt: "asc",
      },
    })

    if (!job) {
      return NextResponse.json({ message: "No jobs to process" })
    }

    // Mark as processing
    await prisma.job.update({
      where: { id: job.id },
      data: { status: "processing" },
    })

    try {
      if (job.type === "meeting_transcribe") {
        const { audioUrl, meetingId } = job.payload as any

        // Transcribe audio
        // Note: For MVP, audioUrl should be a file path or URL
        // In production, download the file first or use a File object
        const transcription = await openai.audio.transcriptions.create({
          file: audioUrl as any, // This should be a File object
          model: "whisper-1",
          response_format: "verbose_json",
        })

        // Generate summary
        const summaryResponse = await openai.chat.completions.create({
          model: process.env.OPENROUTER_MODEL || "gpt-4o-mini",
          messages: [
            {
              role: "system",
              content:
                "Ты помощник для создания резюме встреч. Создай структурированное резюме на русском языке.",
            },
            {
              role: "user",
              content: `Создай резюме этой встречи:\n\n${transcription.text}`,
            },
          ],
        })

        const summary = summaryResponse.choices[0].message.content

        // Update meeting
        if (meetingId) {
          await prisma.meeting.update({
            where: { id: meetingId },
            data: {
              transcript: transcription.text,
              transcriptSegments: (transcription as any).segments || [],
              summary: summary || "",
              status: "completed",
            },
          })
        }

        // Mark job as done
        // Convert transcription to JSON-compatible format
        const resultJson = {
          transcription: {
            text: transcription.text,
            language: transcription.language,
            duration: transcription.duration,
            words: (transcription as any).words || [],
          },
          summary: summary,
        }
        
        await prisma.job.update({
          where: { id: job.id },
          data: {
            status: "done",
            result: resultJson as any,
          },
        })
      }

      return NextResponse.json({ success: true, jobId: job.id })
    } catch (error: any) {
      // Mark job as failed
      await prisma.job.update({
        where: { id: job.id },
        data: {
          status: "failed",
          error: error.message,
        },
      })

      throw error
    }
  } catch (error: any) {
    console.error("Job processing error:", error)
    return NextResponse.json(
      { error: error.message || "Internal server error" },
      { status: 500 }
    )
  }
}

