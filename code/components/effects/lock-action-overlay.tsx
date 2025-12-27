"use client"

import { motion, AnimatePresence } from "framer-motion"

interface LockActionOverlayProps {
  visible: boolean
  action: "arm" | "disarm" | null
  onFinish: () => void
}

export default function LockActionOverlay({
  visible,
  action,
  onFinish,
}: LockActionOverlayProps) {
  const locked = action === "arm"

  return (
    <AnimatePresence>
      {visible && action && (
        <motion.div
          className="fixed inset-0 z-50 flex items-center justify-center
                     bg-black/45 backdrop-blur-sm"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          {/* LOCK CONTAINER */}
          <motion.div
            initial={{ scale: 0.7, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.7, opacity: 0 }}
            transition={{ duration: 0.35, ease: "easeOut" }}
            onAnimationComplete={() => {
              setTimeout(onFinish, 900)
            }}
            className="relative flex flex-col items-center"
          >
            {/* SHACKLE */}
            <motion.div
              className="
                w-24 h-24
                border-[6px] border-cyan-400
                rounded-t-full
                border-b-0
                bg-transparent
              "
              animate={{
                y: locked ? 28 : 0,
              }}
              transition={{
                duration: 0.4,
                ease: "easeInOut",
              }}
            />

            {/* BODY */}
            <motion.div
              className="
                w-32 h-24
                -mt-2
                rounded-3xl
                bg-[#0b1220]
                border border-cyan-400
                flex items-center justify-center
                relative
              "
              animate={{
                boxShadow: locked
                  ? "0 0 45px rgba(0,255,255,0.85)"
                  : "0 0 16px rgba(255,255,255,0.25)",
              }}
              transition={{ duration: 0.35 }}
            >
              {/* INNER PLATE */}
              <div
                className="
                  absolute inset-3
                  rounded-2xl
                  bg-[#0f172a]
                  border border-cyan-400/40
                "
              />

              {/* KEY SLOT */}
              <div
                className="
                  relative z-10
                  w-3 h-8
                  rounded-sm
                  bg-cyan-400
                "
              />
            </motion.div>

            {/* STATUS TEXT (VERY SUBTLE) */}
            <motion.p
              className="mt-6 text-sm tracking-wide text-cyan-300"
              initial={{ opacity: 0 }}
              animate={{ opacity: 0.8 }}
              transition={{ delay: 0.2 }}
            >
              {locked ? "SYSTEM ARMED" : "SYSTEM DISARMED"}
            </motion.p>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
