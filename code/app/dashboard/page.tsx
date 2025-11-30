"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Bell, User } from "lucide-react"
import SecurityToggle from "@/components/security-toggle"
import ModeSelector from "@/components/mode-selector"
import StatusIndicator from "@/components/status-indicator"


type VisitorLog = {
  id: number
  name: string
  purpose: string | null
  timestamp: string | null
}

export default function Dashboard() {
  const router = useRouter()

  const [authChecked, setAuthChecked] = useState(false)
  const [userEmail, setUserEmail] = useState<string | null>(null)

  const [isArmed, setIsArmed] = useState(false)
  const [mode, setMode] = useState<"normal" | "child" | "night">("normal")
  const [alerts, setAlerts] = useState(2)

  // visitor logs
  const [visitorLogs, setVisitorLogs] = useState<VisitorLog[]>([])
  const [visitorLoading, setVisitorLoading] = useState(true)
  const [visitorError, setVisitorError] = useState<string | null>(null)

  // 🔒 Auth guard
  useEffect(() => {
    const userId = window.localStorage.getItem("user_id")
    const email = window.localStorage.getItem("email")

    if (!userId) {
      router.replace("/")
      return
    }

    setUserEmail(email)
    setAuthChecked(true)
  }, [router])

  const handleLogout = () => {
    window.localStorage.removeItem("user_id")
    window.localStorage.removeItem("email")
    router.replace("/")
  }

  const fetchVisitorLogs = async () => {
    try {
      setVisitorLoading(true)
      setVisitorError(null)

      const res = await fetch("http://localhost:5000/api/visitors")
      if (!res.ok) throw new Error("Fetch failed")

      const data = await res.json()
      setVisitorLogs(data)
    } catch (err) {
      console.error(err)
      setVisitorError("Failed to load visitor logs")
    } finally {
      setVisitorLoading(false)
    }
  }

  useEffect(() => {
    fetchVisitorLogs()
  }, [])
  
  // take only the latest 3 logs
  const recent = visitorLogs.slice(0, 3)

  // don't render until auth check is done (prevents flash)
  if (!authChecked) {
    return null
    // or a loader:
    // return <div className="p-8 text-foreground">Checking access...</div>
  }

  return (
    <div className="p-8 space-y-8">
      {/* Top Bar */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Security Control</h1>
          <p className="text-muted-foreground">Welcome back to your home</p>
        </div>

        <div className="flex items-center gap-4">
          {/* logged in user email */}
          {userEmail && (
            <div className="text-right text-sm max-w-[200px]">
              <p className="text-muted-foreground">Logged in as</p>
              <p className="text-foreground font-semibold truncate">{userEmail}</p>
            </div>
          )}

          

          <div className="glass p-3 rounded-full">
            <User className="w-6 h-6 text-primary" />
          </div>

          <button
            type="button"
            onClick={handleLogout}
            className="px-3 py-2 text-sm rounded-lg border border-border bg-background hover:bg-muted transition"
          >
            Logout
          </button>
        </div>
      </div>

      {/* Status and Controls */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="glass p-6 rounded-2xl glow-cyan">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold text-foreground">System Status</h2>
            <StatusIndicator status={isArmed ? "active" : "inactive"} />
          </div>

          <div className="space-y-3 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Armed</span>
              <span className="text-primary font-semibold">{isArmed ? "Yes" : "No"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Mode</span>
              <span className="text-primary font-semibold capitalize">{mode}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Cameras</span>
              <span className="text-primary font-semibold">4 Online</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Alerts</span>
              <span className="text-accent font-semibold">{alerts} New</span>
            </div>
          </div>
        </div>

        <ModeSelector mode={mode} setMode={setMode} isArmed={isArmed} />
      </div>

      {/* Security Toggle */}
      <SecurityToggle isArmed={isArmed} setIsArmed={setIsArmed} mode={mode} />

      {/* Recent Activity (Updated to show real logs) */}
      <div className="glass p-6 rounded-2xl">
        <h2 className="text-lg font-semibold text-foreground mb-4">Recent Activity (Top 3 logs)</h2>

        {visitorLoading ? (
          <p className="text-muted-foreground">Loading visitor logs...</p>
        ) : visitorError ? (
          <p className="text-destructive">{visitorError}</p>
        ) : recent.length === 0 ? (
          <p className="text-muted-foreground">No recent visitor activity.</p>
        ) : (
          <div className="space-y-3">
            {recent.map((log) => {
              const formattedTime = log.timestamp
                ? new Date(log.timestamp).toLocaleString()
                : "Unknown time"

              const purposeText = log.purpose ? `Purpose: ${log.purpose}` : "No purpose recorded"

              return (
                <div
                  key={log.id}
                  className="flex items-start gap-3 pb-3 border-b border-border"
                >
                  <div className="w-2 h-2 rounded-full bg-primary mt-2" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-foreground">
                      {log.name || "Unknown visitor"}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {purposeText}
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">
                      {formattedTime}
                    </p>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
