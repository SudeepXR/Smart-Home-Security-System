"use client"

interface StatusIndicatorProps {
  status: "active" | "inactive" | "alert"
}

export default function StatusIndicator({ status }: StatusIndicatorProps) {
  const colors = {
    active: "bg-primary text-primary glow-cyan",
    inactive: "bg-muted text-muted-foreground",
    alert: "bg-accent text-accent-foreground glow-amber",
  }

  return (
    <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full ${colors[status]}`}>
      <div className="w-2 h-2 rounded-full bg-current animate-pulse"></div>
      <span className="text-xs font-semibold capitalize">{status}</span>
    </div>
  )
}
