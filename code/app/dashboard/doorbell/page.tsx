"use client"

import { useState, useRef, useEffect } from "react"
import { ArrowLeft, Phone, PhoneOff, Mic, MicOff } from "lucide-react"
import Link from "next/link"


export default function DoorbellPage() {
  const [callState, setCallState] = useState<"idle" | "connecting" | "connected" | "error">("idle")
  const [isMuted, setIsMuted] = useState(false)
  const [statusMessage, setStatusMessage] = useState("Click 'Talk' to start audio communication")

  const localStreamRef = useRef<MediaStream | null>(null)
  const peerConnectionRef = useRef<RTCPeerConnection | null>(null)
  const remoteAudioRef = useRef<HTMLAudioElement>(null)

  useEffect(() => {
    return () => {
      endCall()
    }
  }, [])

  const startCall = async () => {
    try {
      setCallState("connecting")
      setStatusMessage("Requesting microphone access...")

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
        video: false,
      })

      localStreamRef.current = stream
      setStatusMessage("Microphone access granted. Connecting...")

      const configuration: RTCConfiguration = {
        iceServers: [
          { urls: "stun:stun.l.google.com:19302" },
          { urls: "stun:stun1.l.google.com:19302" },
        ],
      }

      const peerConnection = new RTCPeerConnection(configuration)
      peerConnectionRef.current = peerConnection

      stream.getTracks().forEach((track) => {
        peerConnection.addTrack(track, stream)
      })

      peerConnection.ontrack = (event) => {
        if (remoteAudioRef.current && event.streams[0]) {
          remoteAudioRef.current.srcObject = event.streams[0]
          setStatusMessage("Audio connected - Two-way communication active")
          setCallState("connected")
        }
      }

      peerConnection.onicecandidate = (event) => {
        if (event.candidate) {
          console.log("[Frontend] ICE candidate:", event.candidate)
          fetch("http://192.168.254.154:8000/candidate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              candidate: event.candidate.candidate,
              sdpMLineIndex: event.candidate.sdpMLineIndex,
              sdpMid: event.candidate.sdpMid,
            }),
          }).catch(err => console.error("Failed to send ICE candidate:", err))
        }
      }

      peerConnection.onconnectionstatechange = () => {
        console.log("[Frontend] Connection state:", peerConnection.connectionState)
        if (peerConnection.connectionState === "connected") {
          setCallState("connected")
          setStatusMessage("Audio connected - Two-way communication active")
        } else if (
          peerConnection.connectionState === "disconnected" ||
          peerConnection.connectionState === "failed"
        ) {
          setStatusMessage("Connection lost. Please try again.")
          setCallState("error")
        }
      }

      const offer = await peerConnection.createOffer()
      await peerConnection.setLocalDescription(offer)
      console.log("[Frontend] SDP Offer created:", offer)

      setStatusMessage("Sending offer to doorbell...")
      const response = await fetch("http://192.168.254.154:8000/offer", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          type: offer.type,
          sdp: offer.sdp,
        }),
      })

      const answerData = await response.json()
      console.log("[Frontend] Answer received:", answerData)

      await peerConnection.setRemoteDescription(
        new RTCSessionDescription(answerData)
      )
      setStatusMessage("Connected! Two-way audio active.")

    } catch (error) {
      console.error("[Frontend] Error starting call:", error)
      setCallState("error")
      if (error instanceof DOMException && error.name === "NotAllowedError") {
        setStatusMessage("Microphone access denied.")
      } else {
        setStatusMessage(`Error: ${error instanceof Error ? error.message : "Failed to start call"}`)
      }
      endCall()
    }
  }

  const endCall = () => {
    if (localStreamRef.current) {
      localStreamRef.current.getTracks().forEach((track) => track.stop())
      localStreamRef.current = null
    }

    if (peerConnectionRef.current) {
      peerConnectionRef.current.close()
      peerConnectionRef.current = null
    }

    if (remoteAudioRef.current) {
      remoteAudioRef.current.srcObject = null
    }

    setCallState("idle")
    setIsMuted(false)
    setStatusMessage("Click 'Talk' to start audio communication")
    console.log("[Frontend] Call ended")
  }

  const toggleMute = () => {
    if (localStreamRef.current) {
      const audioTracks = localStreamRef.current.getAudioTracks()
      audioTracks.forEach((track) => {
        track.enabled = !track.enabled
      })
      setIsMuted(!isMuted)
      setStatusMessage(isMuted ? "Microphone unmuted" : "Microphone muted")
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

      {/* Main Split Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Video Feed - Left Side */}
        <div className="lg:col-span-2 glass rounded-2xl overflow-hidden">
          <div
            className={`bg-secondary/50 aspect-video lg:aspect-auto lg:h-[500px] flex items-center justify-center relative ${callState === "connected" ? "ring-2 ring-primary" : ""}`}
          >
            <div className="text-center">
              <div className="w-24 h-24 bg-gradient-to-br from-primary/20 to-secondary rounded-full flex items-center justify-center mx-auto mb-4">
                <div className="w-16 h-16 bg-primary/30 rounded-full"></div>
              </div>
              <p className="text-foreground font-semibold mb-2">Visitor at Door</p>
              <p className="text-sm text-muted-foreground">Front Entrance</p>
              {callState === "connected" && (
                <div className="mt-4">
                  <div className="inline-flex items-center gap-2 text-primary">
                    <div className="w-2 h-2 bg-primary rounded-full animate-pulse"></div>
                    <span className="text-sm font-semibold">Audio Connected</span>
                  </div>
                </div>
              )}
              {callState === "connecting" && (
                <div className="mt-4">
                  <div className="inline-flex items-center gap-2 text-accent">
                    <div className="w-2 h-2 bg-accent rounded-full animate-pulse"></div>
                    <span className="text-sm font-semibold">Connecting...</span>
                  </div>
                </div>
              )}
            </div>

            {/* Call Status */}
            {callState === "idle" && (
              <div className="absolute top-4 left-4 bg-destructive/20 px-3 py-1.5 rounded-full">
                <p className="text-xs text-destructive font-semibold">INCOMING CALL</p>
              </div>
            )}
          </div>
        </div>

        {/* Chat & Controls - Right Side */}
        <div className="space-y-6">
          <div className="glass p-6 rounded-2xl space-y-4">
            <h3 className="font-semibold text-foreground mb-4">Audio Communication</h3>

            {/* Status Message */}
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

            {/* Talk / End Call Button */}
            {callState === "idle" || callState === "error" ? (
              <button
                onClick={startCall}
                className="w-full py-4 rounded-lg font-semibold transition-all flex items-center justify-center gap-2 bg-primary/20 hover:bg-primary/30 text-primary"
              >
                <Phone className="w-5 h-5" />
                Talk
              </button>
            ) : (
              <button
                onClick={endCall}
                disabled={callState === "connecting"}
                className="w-full py-4 rounded-lg font-semibold transition-all flex items-center justify-center gap-2 bg-destructive/20 hover:bg-destructive/30 text-destructive disabled:opacity-50"
              >
                <PhoneOff className="w-5 h-5" />
                End Call
              </button>
            )}

            {/* Mute/Unmute Button */}
            {(callState === "connected" || callState === "connecting") && (
              <button
                onClick={toggleMute}
                disabled={callState === "connecting"}
                className={`w-full py-3 rounded-lg font-semibold transition-all flex items-center justify-center gap-2 ${
                  isMuted
                    ? "bg-accent/20 hover:bg-accent/30 text-accent"
                    : "bg-secondary/50 hover:bg-secondary text-foreground"
                } disabled:opacity-50`}
              >
                {isMuted ? (
                  <>
                    <MicOff className="w-4 h-4" />
                    Unmute
                  </>
                ) : (
                  <>
                    <Mic className="w-4 h-4" />
                    Mute
                  </>
                )}
              </button>
            )}

            {/* Hidden audio element for remote audio playback */}
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
                <p className="text-foreground font-semibold">2:45 PM</p>
              </div>
              <div>
                <p className="text-muted-foreground">Date</p>
                <p className="text-foreground font-semibold">Today</p>
              </div>
            </div>
          </div>

          
        </div>
      </div>
    </div>
  )
}
