"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { User } from "lucide-react"
import SecurityToggle from "@/components/security-toggle"
import ModeSelector from "@/components/mode-selector"
import StatusIndicator from "@/components/status-indicator"
import { SpotlightCard } from "@/components/effects/spotlight-card"
import { IP_SUD } from "../lib/config"



type VisitorLog = {
  id: number
  name: string
  purpose: string | null
  timestamp: string | null
}

export default function Dashboard() {
  const router = useRouter()
  const [hydrated, setHydrated] = useState(false) 
  const [authChecked, setAuthChecked] = useState(false)

  const [isArmed, setIsArmed] = useState(false)
  const [mode, setMode] = useState<"normal" | "child" | "night">("normal")
  const [alerts] = useState(2)

  const [visitorLogs, setVisitorLogs] = useState<VisitorLog[]>([])
  const [visitorLoading, setVisitorLoading] = useState(true)
  const [visitorError, setVisitorError] = useState<string | null>(null)

  // 🔒 JWT auth guard
  useEffect(() => {
    const token = localStorage.getItem("token")
    if (!token) {
      router.replace("/")
      return
    }
    setAuthChecked(true)
  }, [router])


// 🔁 Rehydrate armed state + mode from localStorage
useEffect(() => {
  if (!authChecked) return

  const savedArmed = localStorage.getItem("isArmed")
  const savedMode = localStorage.getItem("securityMode")

  if (savedArmed !== null) {
    setIsArmed(savedArmed === "true")
  }

  if (
    savedMode === "normal" ||
    savedMode === "child" ||
    savedMode === "night"
  ) {
    setMode(savedMode)
  }

  setHydrated(true) // ✅ mark hydration complete
}, [authChecked])


// 💾 Persist armed state + mode

useEffect(() => {
  if (!hydrated) return
  localStorage.setItem("isArmed", String(isArmed))
  localStorage.setItem("securityMode", mode)
}, [isArmed, mode, hydrated])



  const handleLogout = () => {
    localStorage.removeItem("token")
    router.replace("/")
  }

  const fetchVisitorLogs = async () => {
    try {
      setVisitorLoading(true)
      setVisitorError(null)

      const token = localStorage.getItem("token")

      const res = await fetch(`${IP_SUD}/visitors`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })

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
    if (authChecked) {
      fetchVisitorLogs()
    }
  }, [authChecked])

  const recent = visitorLogs.slice(0, 3)

  if (!authChecked) return null
  return (
    <div className="p-8 space-y-8">
      {/* Top Bar */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Security Control</h1>
          <p className="text-muted-foreground">Welcome back</p>
        </div>

        <div className="flex items-center gap-4">
          <div className="glass p-3 rounded-full">
            <User className="w-6 h-6 text-primary" />
          </div>

          <button
            type="button"
            onClick={handleLogout}
            className="px-3 py-2 text-sm rounded-lg border"
          >
            Logout
          </button>
        </div>
      </div>

      {/* Status */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <SpotlightCard className="glass p-6 rounded-2xl glow-cyan">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold">System Status</h2>
            <StatusIndicator status={isArmed ? "active" : "inactive"} />
          </div>

          <div className="space-y-3 text-sm">
            <div className="flex justify-between">
              <span>Armed</span>
              <span className="font-semibold">{isArmed ? "Yes" : "No"}</span>
            </div>
            <div className="flex justify-between">
              <span>Mode</span>
              <span className="font-semibold capitalize">{mode}</span>
            </div>
            <div className="flex justify-between">
              <span>Cameras</span>
              <span className="font-semibold">Online</span>
            </div>
          </div>
        </SpotlightCard>

        <ModeSelector mode={mode} setMode={setMode} isArmed={isArmed} />
      </div>

      <SecurityToggle isArmed={isArmed} setIsArmed={setIsArmed} mode={mode} />

      {/* Recent Activity */}
      <div className="glass p-6 rounded-2xl">
        <h2 className="text-lg font-semibold mb-4">Recent Activity</h2>

        {visitorLoading ? (
          <p>Loading visitor logs...</p>
        ) : visitorError ? (
          <p className="text-destructive">{visitorError}</p>
        ) : recent.length === 0 ? (
          <p>No recent visitor activity.</p>
        ) : (
          <div className="space-y-3">
            {recent.map((log) => (
              <div key={log.id} className="border-b pb-3">
                <p>{log.name}</p>
                <p className="text-xs text-muted-foreground">
                  {log.purpose || "No purpose"}
                </p>
                <p className="text-xs text-muted-foreground">
                  {log.timestamp
                    ? new Date(log.timestamp).toLocaleString()
                    : "Unknown time"}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
