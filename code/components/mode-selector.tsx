"use client"

import { useState } from "react"
import { Shield, Home, Moon } from "lucide-react"
import { SpotlightCard } from "@/components/effects/spotlight-card"
import { IP_SUD, IP_MEG, IP_ESP } from "@/app/lib/config"


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
  apiBase = IP_SUD,
}: ModeSelectorProps) {
  const [busy, setBusy] = useState(false)

  const modes = [
    { id: "normal" as const, label: "Normal", icon: Home, description: "Standard protection" },
    { id: "child" as const, label: "Child Safety", icon: Shield, description: "Indoor monitoring" },
    { id: "night" as const, label: "Night Time", icon: Moon, description: "Enhanced security" },
  ]

  const sendModeToESP = async (selectedMode: "normal" | "child" | "night") => {
    try {
      await fetch(`${IP_ESP}/mode`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode: selectedMode }),
      })
    } catch (err) {
      console.error("ESP mode update failed:", err)
    }
  }

  const changeMode = async (newMode: "normal" | "child" | "night") => {
    setMode(newMode)

    if (!isArmed) {
      console.log("Mode changed locally (disarmed)")
      return
    }

    setBusy(true)
    try {
      const token = localStorage.getItem("token")

    const res = await fetch(`${apiBase}/api/system/arm`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ armed: true, mode: newMode }),
    })

      if (!res.ok) throw new Error("Backend error")

      await sendModeToESP(newMode)
    } catch (err) {
      console.error(err)
      alert("Failed to change mode on backend/ESP")
    } finally {
      setBusy(false)
    }
  }

  return (
    <SpotlightCard className="glass p-6 rounded-2xl">
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

            <div
              className={`w-3 h-3 rounded-full ${
                mode === id ? "bg-primary" : "border border-border"
              }`}
            />
          </button>
        ))}
      </div>

      <p className="text-xs text-muted-foreground mt-3">
        {isArmed
          ? "Changing mode will restart the system and update ESP."
          : "Arm system to activate."}
      </p>
    </SpotlightCard>
  )
}
