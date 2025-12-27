"use client"

import { useState, useRef, useEffect } from "react"
import { ArrowLeft, PlugZap, Plug } from "lucide-react"
import Link from "next/link"
import { IP_SUD } from "../../lib/config"
import { IP_VID } from "../../lib/config"

export default function DoorbellPage() {
  const [callState, setCallState] = useState<"idle" | "connecting" | "connected" | "error">("idle")
  const [statusMessage, setStatusMessage] = useState("Click 'Connect' to start communication")
  const remoteAudioRef = useRef<HTMLAudioElement>(null)

  useEffect(() => {
    const token = localStorage.getItem("token")
    if (!token) {
      window.location.href = "/"
    }
  }, [])

  useEffect(() => {
    return () => {
      disconnect()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // ===========================
  // CONNECT
  // ===========================
  const connect = async () => {
    setCallState("connecting")
    setStatusMessage("Connecting to doorbell…")

    try {
      // Disarm system
      await fetch(`${IP_SUD}/api/system/arm`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify({ armed: false }),
      })

      // Start friend audio
      await fetch(`${IP_SUD}/api/communication/start`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      })

      // Start local audio
      await fetch("http://localhost:5000/api/com/start", {
        method: "POST",
      })

      setCallState("connected")
      setStatusMessage("Two-way communication active")
    } catch (err) {
      console.error("Connect error:", err)
      setCallState("error")
      setStatusMessage("Failed to connect. Try again.")
    }
  }

  // ===========================
  // DISCONNECT
  // ===========================
  const disconnect = async () => {
    try {
      setStatusMessage("Disconnecting…")

      await fetch(`${IP_SUD}/api/communication/stop`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      })

      await fetch("http://localhost:5000/api/com/stop", {
        method: "POST",
      })
    } catch {
      // ignore
    } finally {
      setCallState("idle")
      setStatusMessage("Click 'Connect' to start communication")
    }
  }

  return (
    <div className="p-8 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link href="/dashboard" className="p-2 hover:bg-card rounded-lg transition">
          <ArrowLeft className="w-6 h-6 text-foreground" />
        </Link>
        <div>
          <h1 className="text-3xl font-bold text-foreground">Doorbell</h1>
          <p className="text-muted-foreground">Front door visitor communication</p>
        </div>
      </div>

      {/* Main Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* VIDEO PANEL */}
        <div className="lg:col-span-2 glass rounded-2xl overflow-hidden">
          <div
            className={`bg-secondary/50 aspect-video lg:h-[500px] relative overflow-hidden ${
              callState === "connected" ? "ring-2 ring-primary" : ""
            }`}
          >
            {callState === "connected" ? (
              <>
                <img
                  src={`${IP_VID}/video`}
                  alt="Live feed"
                  className="absolute inset-0 w-full h-full object-cover"
                />

                {/* LIVE badge */}
                <div className="absolute top-4 left-4 bg-primary/20 px-3 py-1.5 rounded-full backdrop-blur">
                  <div className="flex items-center gap-2 text-primary">
                    <div className="w-2 h-2 bg-primary rounded-full animate-pulse" />
                    <span className="text-xs font-semibold">LIVE</span>
                  </div>
                </div>
              </>
            ) : (
              <div className="absolute inset-0 flex flex-col items-center justify-center text-center px-6">
                <div className="w-24 h-24 bg-linear-to-br from-primary/20 to-secondary rounded-full flex items-center justify-center mb-4">
                  <div className="w-16 h-16 bg-primary/30 rounded-full" />
                </div>

                <p className="text-foreground font-semibold mb-1">
                  Visitor at Door
                </p>
                <p className="text-sm text-muted-foreground">
                  Connect to view live video feed
                </p>

                {callState === "connecting" && (
                  <div className="mt-4 flex items-center gap-2 text-accent">
                    <div className="w-2 h-2 bg-accent rounded-full animate-pulse" />
                    <span className="text-sm font-semibold">Connecting…</span>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* CONTROLS */}
        <div className="space-y-6">
          <div className="glass p-6 rounded-2xl space-y-4">
            <h3 className="font-semibold text-foreground">Audio Communication</h3>

            <div
              className={`p-3 rounded-lg text-sm ${
                callState === "error"
                  ? "bg-destructive/20 text-destructive"
                  : callState === "connected"
                  ? "bg-primary/20 text-primary"
                  : callState === "connecting"
                  ? "bg-accent/20 text-accent"
                  : "bg-secondary/50 text-muted-foreground"
              }`}
            >
              {statusMessage}
            </div>

            {(callState === "idle" || callState === "error") && (
              <button
                onClick={connect}
                className="w-full py-4 rounded-lg font-semibold flex items-center justify-center gap-2 bg-primary/20 hover:bg-primary/30 text-primary"
              >
                <PlugZap className="w-5 h-5" />
                Connect
              </button>
            )}

            {callState !== "idle" && callState !== "error" && (
              <button
                onClick={disconnect}
                className="w-full py-4 rounded-lg font-semibold flex items-center justify-center gap-2 bg-destructive/20 hover:bg-destructive/30 text-destructive"
              >
                <Plug className="w-5 h-5 rotate-180" />
                Disconnect
              </button>
            )}

            <audio ref={remoteAudioRef} autoPlay playsInline className="hidden" />
          </div>

          {/* Visitor Info */}
          <div className="glass p-6 rounded-2xl space-y-4">
            <h3 className="font-semibold text-foreground">Visitor Info</h3>
            <div className="space-y-3 text-sm">
              <div>
                <p className="text-muted-foreground">Location</p>
                <p className="text-foreground font-semibold">Front Door</p>
              </div>
              <div>
                <p className="text-muted-foreground">Time</p>
                <p className="text-foreground font-semibold">Live</p>
              </div>
              <div>
                <p className="text-muted-foreground">Status</p>
                <p className="text-foreground font-semibold">
                  {callState === "connected" ? "Connected" : "Waiting"}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
