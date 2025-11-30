"use client"

import { useState } from "react"
import { Lock, Unlock } from "lucide-react"

interface SecurityToggleProps {
  isArmed: boolean
  setIsArmed: (armed: boolean) => void
  mode: "normal" | "child" | "night"
  apiBase?: string
}

export default function SecurityToggle({
  isArmed,
  setIsArmed,
  mode,
  apiBase = "http://localhost:5000",
}: SecurityToggleProps) {
  const [loading, setLoading] = useState(false)

  const callArmApi = async (newState: boolean) => {
    setLoading(true)
    setIsArmed(newState) // optimistic UI

    try {
      const payload: any = { armed: newState }
      if (newState) payload.mode = mode // send mode ONLY when arming

      const res = await fetch(`${apiBase}/api/system/arm`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })

      if (!res.ok) {
        throw new Error("Backend error")
      }
    } catch (err) {
      console.error(err)
      setIsArmed(!newState) // revert UI
      alert("Failed to update system state")
    }

    setLoading(false)
  }

  return (
    <div className="grid grid-cols-2 gap-6">
      <button
        onClick={() => !loading && callArmApi(true)}
        disabled={loading || isArmed}
        className={`glass p-8 rounded-2xl transition-all duration-300 ${
          isArmed ? "glow-cyan ring-2 ring-primary/50 bg-primary/10" : "hover:bg-card/50"
        } ${loading ? "opacity-70 cursor-wait" : ""}`}
      >
        <div className="flex flex-col items-center gap-3">
          <div className={`p-4 rounded-2xl ${isArmed ? "bg-primary/20" : "bg-secondary"}`}>
            <Lock className={`w-8 h-8 ${isArmed ? "text-primary" : "text-muted-foreground"}`} />
          </div>
          <span className={`font-semibold ${isArmed ? "text-primary" : "text-foreground"}`}>Arm System</span>
          <span className="text-xs text-muted-foreground">
            {isArmed ? `System Protected (${mode})` : `Click to Arm (${mode})`}
          </span>
        </div>
      </button>

      <button
        onClick={() => !loading && callArmApi(false)}
        disabled={loading || !isArmed}
        className={`glass p-8 rounded-2xl transition-all duration-300 ${
          !isArmed ? "glow-cyan ring-2 ring-primary/50 bg-primary/10" : "hover:bg-card/50"
        } ${loading ? "opacity-70 cursor-wait" : ""}`}
      >
        <div className="flex flex-col items-center gap-3">
          <div className={`p-4 rounded-2xl ${!isArmed ? "bg-primary/20" : "bg-secondary"}`}>
            <Unlock className={`w-8 h-8 ${!isArmed ? "text-primary" : "text-muted-foreground"}`} />
          </div>
          <span className={`font-semibold ${!isArmed ? "text-primary" : "text-foreground"}`}>Disarm System</span>
          <span className="text-xs text-muted-foreground">
            {!isArmed ? "System Inactive" : "Click to Disarm"}
          </span>
        </div>
      </button>
    </div>
  )
}
