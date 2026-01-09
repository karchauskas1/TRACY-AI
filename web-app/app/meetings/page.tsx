import { redirect } from "next/navigation"
import { cookies } from "next/headers"
import { getSession } from "@/lib/auth"
import { MeetingsPageClient } from "./MeetingsPageClient"
import { NextRequest } from "next/server"

export default async function MeetingsPage() {
  const cookieStore = await cookies()
  const request = new NextRequest("http://localhost", {
    headers: {
      cookie: cookieStore.toString(),
    },
  })
  const session = await getSession(request)

  if (!session) {
    redirect("/login")
  }

  return <MeetingsPageClient />
}

