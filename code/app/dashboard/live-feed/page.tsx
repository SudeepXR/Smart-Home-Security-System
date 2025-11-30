"use client"

import { useSearchParams } from "next/navigation"
import { ArrowLeft } from "lucide-react"
import Link from "next/link"


export default function LiveFeedPage() {
  const searchParams = useSearchParams()
  const cameraId = searchParams.get("camera") || "cam1"

  const cameraNames: Record<string, string> = {
    cam1: "CCTV",
    cam2: "Backyard",
    cam3: "Living Room",
    cam4: "Garage",
  }

  return (
    <div className="p-8 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link href="/dashboard" className="p-2 hover:bg-card rounded-lg transition">
          <ArrowLeft className="w-6 h-6 text-foreground" />
        </Link>
        <div>
          <h1 className="text-3xl font-bold text-foreground">Live Feed</h1>
          <p className="text-muted-foreground">{cameraNames[cameraId] || "Camera Feed"}</p>
        </div>
      </div>

      {/* Camera Feed Section */}
      <div className="glass rounded-2xl overflow-hidden relative">
        <div className="bg-secondary/50 aspect-video lg:h-[600px] flex items-center justify-center relative">
          {/* Video Feed */}
          <img
            src="http://localhost:5000/video_feed"
            alt={`Live feed from ${cameraNames[cameraId]}`}
            className="object-contain w-full h-full"
          />

          {/* Overlay: REC indicator */}
          <div className="absolute top-4 right-4 flex items-center gap-2 bg-destructive/20 px-3 py-1.5 rounded-full">
            <div className="w-2 h-2 bg-destructive rounded-full animate-pulse"></div>
            <span className="text-xs text-destructive font-semibold">REC</span>
          </div>
        </div>
      </div>
    </div>
  )
}
