"use client"

import { useEffect, useState } from "react"
import { ArrowLeft, Bell, Trash2, User } from "lucide-react"
import Link from "next/link"

import { IP_SUD } from "../../lib/config";


type VisitorLog = {
  name: string
  purpose: string | null
  timestamp: string | null
}


export default function LogsPage() {
  const [logs, setLogs] = useState<VisitorLog[]>([])
  const [loading, setLoading] = useState(true)           // initial load
  const [error, setError] = useState<string | null>(null)
  const [clearing, setClearing] = useState(false)
  useEffect(() => {
  const token = localStorage.getItem("token")
  if (!token) {
    window.location.href = "/"
  }
}, [])

  const fetchLogs = async (background: boolean = false) => {
  try {
    if (!background) {
      setLoading(true)
      setError(null)
    }

    const token = localStorage.getItem("token")

    const res = await fetch(`${IP_SUD}/visitors`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })

    if (!res.ok) {
      throw new Error("Failed to fetch logs")
    }

    const data = await res.json()
    setLogs(data)
  } catch (err) {
    console.error(err)
    if (!background) {
      setError("Failed to load logs")
    }
  } finally {
    if (!background) {
      setLoading(false)
    }
  }
}


  useEffect(() => {
    // initial load
    fetchLogs(false)

    // auto-refresh every 3 seconds
    const interval = setInterval(() => {
      fetchLogs(true) // background refresh, no "Loading..." flicker
    }, 3000)

    // cleanup on unmount
    return () => clearInterval(interval)
  }, [])

  const clearLogs = async () => {
    if (logs.length === 0) return

    const confirmed = window.confirm(
      "Are you sure you want to delete ALL visitor logs?"
    )
    if (!confirmed) return

    try {
      setClearing(true)
      const res = await fetch(`${IP_SUD}/api/visitors/clear`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      })


      if (!res.ok) {
        throw new Error("Failed to clear logs")
      }

      await fetchLogs(false)
      alert("Logs cleared")
    } catch (err) {
      console.error(err)
      alert("Error clearing logs")
    } finally {
      setClearing(false)
    }
  }

  return (
    <div className="p-8 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <Link href="/dashboard" className="p-2 hover:bg-card rounded-lg transition">
            <ArrowLeft className="w-6 h-6 text-foreground" />
          </Link>
          <div>
            <h1 className="text-3xl font-bold text-foreground">Visitor Log</h1>
            <p className="text-muted-foreground">
              All visitors detected by the door system
            </p>
          </div>
        </div>

        <button
          onClick={clearLogs}
          disabled={clearing || loading || logs.length === 0}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-destructive/90 text-destructive-foreground text-sm font-medium disabled:opacity-60 disabled:cursor-not-allowed hover:bg-destructive"
        >
          <Trash2 className="w-4 h-4" />
          {clearing ? "Clearing..." : "Clear All Logs"}
        </button>
      </div>

      {/* Logs List */}
      {loading ? (
        <div className="glass rounded-2xl p-6 text-muted-foreground">
          Loading visitor logs...
        </div>
      ) : error ? (
        <div className="glass rounded-2xl p-6 text-destructive">
          {error}
        </div>
      ) : logs.length === 0 ? (
        <div className="glass rounded-2xl p-6 text-muted-foreground">
          No visitor logs yet.
        </div>
      ) : (
        <div className="glass rounded-2xl divide-y divide-border">
          {logs.map((log, index) => {
            const formattedTime = log.timestamp
              ? new Date(log.timestamp).toLocaleString()
              : "Unknown time"

            return (
              <div
                key={`${log.timestamp}-${index}`}
                className="p-6 hover:bg-card/50 transition flex items-start gap-4"
              >
                <div className="p-3 bg-secondary/50 rounded-lg">
                  <div className="p-3 rounded-lg bg-green-500/20 shadow-[0_0_10px_2px_rgba(34,197,94,0.6)]">
                    <User className="w-5 h-5 text-green-500" />
                  </div>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-semibold text-foreground">
                    {log.name || "Unknown visitor"}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    {"Purpose : " + log.purpose || "No purpose recorded"}
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
  )
}
