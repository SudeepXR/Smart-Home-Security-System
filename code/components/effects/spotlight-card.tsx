    "use client"

    import React, { useRef, useState } from "react"
    import { cn } from "@/lib/utils"

    interface Position {
    x: number
    y: number
    }

    interface SpotlightCardProps extends React.PropsWithChildren {
    className?: string
    spotlightColor?: `rgba(${number}, ${number}, ${number}, ${number})`
    }

    export function SpotlightCard({
    children,
    className,
    spotlightColor = "rgba(34, 211, 238, 0.8)",
    }: SpotlightCardProps) {
    const ref = useRef<HTMLDivElement>(null)
    const [position, setPosition] = useState<Position>({ x: 0, y: 0 })
    const [opacity, setOpacity] = useState(0)

    const handleMouseMove: React.MouseEventHandler<HTMLDivElement> = (e) => {
        if (!ref.current) return

        const rect = ref.current.getBoundingClientRect()
        setPosition({
        x: e.clientX - rect.left,
        y: e.clientY - rect.top,
        })
    }

    return (
        <div
        ref={ref}
        onMouseMove={handleMouseMove}
        onMouseEnter={() => setOpacity(0.2)}
        onMouseLeave={() => setOpacity(0)}
        className={cn(
            "relative overflow-hidden rounded-xl border bg-card p-0",
            className
        )}
        >
        {/* Spotlight layer */}
        <div
            className="pointer-events-none absolute inset-0 transition-opacity duration-300"
            style={{
            opacity,
            background: `radial-gradient(600px circle at ${position.x}px ${position.y}px, ${spotlightColor}, transparent 40%)`,
            }}
        />

        {/* Content */}
        <div className="relative z-10">{children}</div>
        </div>
    )
    }
