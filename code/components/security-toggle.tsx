"use client"

import { useState } from "react"
import { SpotlightCard } from "@/components/effects/spotlight-card"
import AnimatedLock from "@/components/effects/animated-lock"
import LockActionOverlay from "@/components/effects/lock-action-overlay"
import { IP_SUD, IP_MEG, IP_ESP } from "@/app/lib/config"

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
  apiBase = IP_SUD,
}: SecurityToggleProps) {
  const [loading, setLoading] = useState(false)

  // overlay state (UI ONLY)
  const [overlayAction, setOverlayAction] =
    useState<"arm" | "disarm" | null>(null)
  const [showOverlay, setShowOverlay] = useState(false)

  // ======================================================
  // 🚀 SEND ARMED STATE TO ESP8266
  // ======================================================
  const sendArmToESP = async (armed: boolean) => {
    try {
      await fetch(`${IP_ESP}/arm`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ armed }),
      })
    } catch (err) {
      console.error("ESP armed update failed:", err)
    }
  }

  const callArmApi = async (newState: boolean) => {
    setLoading(true)
    setIsArmed(newState)

    try {
      const payload: any = { armed: newState }
      if (newState) payload.mode = mode

      const token = localStorage.getItem("token")

      const res = await fetch(`${apiBase}/api/system/arm`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      })

      if (!res.ok) throw new Error("Backend error")

      await sendArmToESP(newState)
    } catch (err) {
      console.error(err)
      setIsArmed(!newState)
      alert("Failed to update system state")
    }

    setLoading(false)
  }

  return (
    <>
      <div className="grid grid-cols-2 gap-6">
        {/* ARM */}
        <SpotlightCard
          className={`rounded-2xl border-0 bg-transparent ${
            isArmed ? "ring-2 ring-primary/50" : ""
          }`}
        >
          <button
            onClick={() => {
              if (!loading) {
                setOverlayAction("arm")
                setShowOverlay(true)
                callArmApi(true)
              }
            }}
            disabled={loading || isArmed}
            className={`glass p-8 w-full rounded-2xl transition-all duration-300 ${
              isArmed ? "glow-cyan bg-primary/10" : "hover:bg-card/50"
            } ${loading ? "opacity-70 cursor-wait" : ""}`}
          >
            <div className="flex flex-col items-center gap-3">
              <AnimatedLock locked={true} active={isArmed} />

              <span className={`font-semibold ${isArmed ? "text-primary" : ""}`}>
                Arm System
              </span>
              <span className="text-xs text-muted-foreground">
                {isArmed
                  ? `System Protected (${mode})`
                  : `Click to Arm (${mode})`}
              </span>
            </div>
          </button>
        </SpotlightCard>

        {/* DISARM */}
        <SpotlightCard
          className={`rounded-2xl border-0 bg-transparent ${
            !isArmed ? "ring-2 ring-primary/50" : ""
          }`}
        >
          <button
            onClick={() => {
              if (!loading) {
                setOverlayAction("disarm")
                setShowOverlay(true)
                callArmApi(false)
              }
            }}
            disabled={loading || !isArmed}
            className={`glass p-8 w-full rounded-2xl transition-all duration-300 ${
              !isArmed ? "glow-cyan bg-primary/10" : "hover:bg-card/50"
            } ${loading ? "opacity-70 cursor-wait" : ""}`}
          >
            <div className="flex flex-col items-center gap-3">
              <AnimatedLock locked={false} active={!isArmed} />

              <span
                className={`font-semibold ${!isArmed ? "text-primary" : ""}`}
              >
                Disarm System
              </span>
              <span className="text-xs text-muted-foreground">
                {!isArmed ? "System Inactive" : "Click to Disarm"}
              </span>
            </div>
          </button>
        </SpotlightCard>
      </div>

      {/* 🔒 CENTER LOCK ACTION OVERLAY */}
      <LockActionOverlay
        visible={showOverlay}
        action={overlayAction}
        onFinish={() => {
          setShowOverlay(false)
          setOverlayAction(null)
        }}
      />
    </>
  )
}
