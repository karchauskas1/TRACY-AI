"use client"

import { useRouter } from "next/navigation"
import { Button } from "../../components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card"

export default function TestNavigationPage() {
  const router = useRouter()

  const handleNavigation = (path: string) => {
    console.log("[Test] Navigating to:", path)
    try {
      router.push(path)
      console.log("[Test] Navigation initiated")
    } catch (error) {
      console.error("[Test] Navigation error:", error)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Test Navigation</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Button onClick={() => handleNavigation("/assistant")} className="w-full">
            Go to Assistant
          </Button>
          <Button onClick={() => handleNavigation("/calendar")} className="w-full">
            Go to Calendar
          </Button>
          <Button onClick={() => handleNavigation("/login")} className="w-full">
            Go to Login
          </Button>
          <Button onClick={() => handleNavigation("/settings")} className="w-full">
            Go to Settings
          </Button>
          <div className="mt-4 p-4 bg-muted rounded">
            <p className="text-sm text-muted-foreground">
              Current URL: {typeof window !== "undefined" ? window.location.href : ""}
            </p>
            <p className="text-sm text-muted-foreground mt-2">
              basePath: {process.env.NEXT_PUBLIC_BASE_PATH || "/TRACY-AI"}
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

