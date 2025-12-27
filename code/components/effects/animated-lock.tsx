"use client"

import { motion, AnimatePresence } from "framer-motion"
import { Lock, Unlock } from "lucide-react"

interface AnimatedLockProps {
  locked: boolean
  active?: boolean
}

export default function AnimatedLock({
  locked,
  active = false,
}: AnimatedLockProps) {
  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={locked ? "locked" : "unlocked"}
        initial={{ scale: 0.75, rotate: -15, opacity: 0 }}
        animate={{
          scale: 1,
          rotate: 0,
          opacity: 1,
          boxShadow: active
            ? "0 0 25px rgba(0,255,255,0.6)"
            : "0 0 12px rgba(255,255,255,0.15)",
        }}
        exit={{ scale: 0.75, rotate: 15, opacity: 0 }}
        transition={{ duration: 0.4, ease: "easeInOut" }}
        className="p-4 rounded-2xl bg-secondary flex items-center justify-center"
      >
        {locked ? (
          <Lock className="w-8 h-8 text-primary" />
        ) : (
          <Unlock className="w-8 h-8 text-muted-foreground" />
        )}
      </motion.div>
    </AnimatePresence>
  )
}
