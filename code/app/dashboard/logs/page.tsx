"use client"

import { useEffect, useState } from "react"
import { ArrowLeft, Trash2, User, X, Flag } from "lucide-react"
import Link from "next/link"

import { IP_SUD } from "../../lib/config"

type VisitorLog = {
  id: number
  name: string
  purpose: string | null
  timestamp: string | null
  image: string | null
  flag: number
}

export default function LogsPage() {
  const [logs, setLogs] = useState<VisitorLog[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [clearing, setClearing] = useState(false)
  const [selectedImage, setSelectedImage] = useState<string | null>(null)

  useEffect(() => {
    const token = localStorage.getItem("token")
    if (!token) window.location.href = "/"
  }, [])

  const fetchLogs = async (background: boolean = false) => {
    try {
      if (!background) {
        setLoading(true)
        setError(null)
      }

      const token = localStorage.getItem("token")
      const res = await fetch(`${IP_SUD}/visitors-pic`, {
        headers: { Authorization: `Bearer ${token}` },
      })

      if (!res.ok) throw new Error("Failed to fetch logs")

      const data = await res.json()
      setLogs(data)
    } catch (err) {
      console.error(err)
      if (!background) setError("Failed to load logs")
    } finally {
      if (!background) setLoading(false)
    }
  }

  useEffect(() => {
    fetchLogs(false)
    const interval = setInterval(() => fetchLogs(true), 3000)
    return () => clearInterval(interval)
  }, [])

  const flagVisitor = async (id: number) => {
    await fetch(`${IP_SUD}/api/visitors/${id}/flag`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${localStorage.getItem("token")}`,
      },
    })
    fetchLogs(true)
  }

  const unflagVisitor = async (id: number) => {
    await fetch(`${IP_SUD}/api/visitors/${id}/unflag`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${localStorage.getItem("token")}`,
      },
    })
    fetchLogs(true)
  }

  const clearLogs = async () => {
    if (logs.length === 0) return
    if (!window.confirm("Are you sure you want to delete ALL visitor logs?")) return

    try {
      setClearing(true)
      const res = await fetch(`${IP_SUD}/api/visitors/clear`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      })

      if (!res.ok) throw new Error("Failed to clear logs")

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
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-destructive/90 text-destructive-foreground text-sm font-medium disabled:opacity-60 hover:bg-destructive"
        >
          <Trash2 className="w-4 h-4" />
          {clearing ? "Clearing..." : "Clear All Logs"}
        </button>
      </div>

      {/* Logs */}
      <div className="glass rounded-2xl divide-y divide-border">
        {logs.map((log) => {
          const formattedTime = log.timestamp
            ? new Date(log.timestamp).toLocaleString()
            : "Unknown time"

          const isUnknown = log.name?.toLowerCase().includes("unknown")

          return (
            <div
              key={log.id}
              className={`
                p-6 flex items-stretch gap-4 transition-all duration-300
                ${log.flag === 1
                  ? "bg-red-500/10 border-l-4 border-red-500 animate-[pulse_1.5s_ease-in-out]"
                  : "hover:bg-card/50"}
              `}
            >
              {/* Image */}
              <div
                className="w-14 h-14 rounded-lg overflow-hidden bg-secondary/50 flex items-center justify-center cursor-pointer shrink-0"
                onClick={() => log.image && setSelectedImage(log.image)}
              >
                {log.image ? (
                  <img
                    src={`data:image/jpeg;base64,${log.image}`}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <User className="w-6 h-6 text-muted-foreground" />
                )}
              </div>

              {/* Info */}
              <div className="flex-1 min-w-0">
                <p className="font-semibold text-foreground">
                  {log.name || "Unknown visitor"}
                </p>

                {log.flag === 1 && (
                  <p className="mt-1 text-sm font-semibold text-red-500">
                    🚩 FLAGGED
                  </p>
                )}

                <p className="text-sm text-muted-foreground">
                  {log.purpose ? `Purpose: ${log.purpose}` : "No purpose recorded"}
                </p>

                <p className="text-xs text-muted-foreground mt-1">
                  {formattedTime}
                </p>
              </div>

              {/* Flag / Unflag Button */}
              {isUnknown && (
                <button
                  onClick={() =>
                    log.flag === 0
                      ? flagVisitor(log.id)
                      : unflagVisitor(log.id)
                  }
                  className={`
                    relative w-14 flex items-center justify-center rounded-lg transition
                    ${log.flag === 0
                      ? "bg-red-500/10 hover:bg-red-500/20"
                      : "bg-green-500/10 hover:bg-green-500/20"}
                  `}
                >
                  {/* Background icon */}
                  <Flag
                    className={`
                      absolute w-8 h-8 opacity-[0.10]
                      ${log.flag === 0 ? "text-red-500" : "text-green-500"}
                    `}
                  />
                  {/* Foreground label */}
                  <span
                    className={`
                      z-10 text-xs font-semibold
                      ${log.flag === 0 ? "text-red-600" : "text-green-600"}
                    `}
                  >
                    {log.flag === 0 ? "FLAG" : "UNFLAG"}
                  </span>
                </button>
              )}
            </div>
          )
        })}
      </div>

      {/* Image Popup */}
      {selectedImage && (
        <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center">
          <div className="relative max-w-lg w-full p-4">
            <button
              onClick={() => setSelectedImage(null)}
              className="absolute top-2 right-2 p-2 rounded-full bg-black/60 text-white hover:bg-black"
            >
              <X className="w-5 h-5" />
            </button>
            <img
              src={`data:image/jpeg;base64,${selectedImage}`}
              className="w-full h-auto rounded-xl"
            />
          </div>
        </div>
      )}
    </div>
  )
}