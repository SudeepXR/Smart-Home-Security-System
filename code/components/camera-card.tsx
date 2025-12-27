"use client"

import Link from "next/link"
import { Eye, Volume2 } from "lucide-react"
import { SpotlightCard } from "@/components/effects/spotlight-card"

interface CameraCardProps {
  name: string
  location: string
  id: string
}

export default function CameraCard({ name, location, id }: CameraCardProps) {
  return (
    <SpotlightCard className="glass rounded-2xl overflow-hidden group">
      {/* Placeholder Camera Feed */}
      <div className="bg-secondary/50 aspect-video relative flex items-center justify-center overflow-hidden">
        <div className="absolute inset-0 bg-linear-to-br from-primary/10 to-transparent" />
        <div className="text-center z-10">
          <Eye className="w-12 h-12 text-primary/50 mx-auto mb-2" />
          <p className="text-xs text-muted-foreground">Live Feed</p>
        </div>
      </div>

      {/* Camera Info */}
      <div className="p-4 space-y-3">
        <div>
          <h3 className="font-semibold text-foreground">{name}</h3>
          <p className="text-xs text-muted-foreground">{location}</p>
        </div>

        {/* Controls */}
        <div className="flex gap-2">
          <Link
            href={`/dashboard/live-feed?camera=${id}`}
            className="flex-1 bg-primary/20 hover:bg-primary/30 text-primary py-2 rounded-lg text-sm font-medium transition-all"
          >
            View Live
          </Link>

          <button className="flex-1 bg-secondary/50 hover:bg-secondary text-foreground py-2 rounded-lg text-sm font-medium transition-all flex items-center justify-center gap-2">
            <Volume2 className="w-4 h-4" />
            Audio
          </button>
        </div>
      </div>
    </SpotlightCard>
  )
}
