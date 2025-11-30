"use client"

import { useState } from "react"
import { Shield, Home, Moon } from "lucide-react"

interface ModeSelectorProps {
  mode: "normal" | "child" | "night"
  setMode: (mode: "normal" | "child" | "night") => void
  isArmed: boolean
  apiBase?: string
}

export default function ModeSelector({
  mode,
  setMode,
  isArmed,
  apiBase = "http://localhost:5000",
}: ModeSelectorProps) {
  const [busy, setBusy] = useState(false)

  const modes = [
    { id: "normal" as const, label: "Normal", icon: Home, description: "Standard protection" },
    { id: "child" as const, label: "Child Safety", icon: Shield, description: "Indoor monitoring" },
    { id: "night" as const, label: "Night Time", icon: Moon, description: "Enhanced security" },
  ]

  const changeMode = async (newMode: "normal" | "child" | "night") => {
    setMode(newMode) // update UI instantly

    // If disarmed → DO NOT call backend (your rule)
    if (!isArmed) {
      console.log("Mode changed locally (disarmed) — no backend call")
      return
    }

    // If armed → restart system_main with new mode
    setBusy(true)
    try {
      const res = await fetch(`${apiBase}/api/system/arm`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ armed: true, mode: newMode }),
      })

      if (!res.ok) {
        throw new Error("Backend error")
      }
    } catch (err) {
      console.error(err)
      alert("Failed to change mode on backend")
      // we keep the new mode in UI anyway
    }
    setBusy(false)
  }

  return (
    <div className="glass p-6 rounded-2xl">
      <h3 className="text-lg font-semibold text-foreground mb-4">Security Mode</h3>
      <div className="space-y-3">
        {modes.map(({ id, label, icon: Icon, description }) => (
          <button
            key={id}
            onClick={() => changeMode(id)}
            disabled={busy}
            className={`w-full flex items-center gap-3 p-3 rounded-lg transition-all ${
              mode === id
                ? "bg-primary/20 border border-primary/50 text-primary glow-cyan"
                : "bg-secondary/30 border border-border text-foreground hover:bg-secondary/50"
            }`}
          >
            <Icon className="w-5 h-5 flex-shrink-0" />
            <div className="text-left flex-1">
              <p className="font-semibold text-sm">{label}</p>
              <p className="text-xs text-muted-foreground">{description}</p>
            </div>
            <div className={`w-3 h-3 rounded-full ${mode === id ? "bg-primary" : "border border-border"}`}></div>
          </button>
        ))}
      </div>

      <p className="text-xs text-muted-foreground mt-3">
        {isArmed ? "Changing mode will restart the system." : "Arm system to activate."}
      </p>
    </div>
  )
}
