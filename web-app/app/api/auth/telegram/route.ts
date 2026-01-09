import { NextRequest, NextResponse } from "next/server"
import { createOrUpdateUser, createSession } from "@/lib/auth"
import crypto from "crypto"

const BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN

function verifyTelegramAuth(authData: any): boolean {
  if (!BOT_TOKEN) return false

  const { hash, ...data } = authData
  const dataCheckString = Object.keys(data)
    .sort()
    .map((key) => `${key}=${data[key]}`)
    .join("\n")

  const secretKey = crypto
    .createHash("sha256")
    .update(BOT_TOKEN)
    .digest()

  const calculatedHash = crypto
    .createHmac("sha256", secretKey)
    .update(dataCheckString)
    .digest("hex")

  return calculatedHash === hash
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()

    if (!verifyTelegramAuth(body)) {
      return NextResponse.json({ error: "Invalid auth data" }, { status: 401 })
    }

    const user = await createOrUpdateUser({
      id: body.id.toString(),
      first_name: body.first_name,
      last_name: body.last_name,
      username: body.username,
      photo_url: body.photo_url,
    })

    const token = createSession(user.id)

    const response = NextResponse.json({ success: true })
    response.cookies.set("session", token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      maxAge: 60 * 60 * 24 * 30, // 30 days
    })

    return response
  } catch (error) {
    console.error("Auth error:", error)
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    )
  }
}

