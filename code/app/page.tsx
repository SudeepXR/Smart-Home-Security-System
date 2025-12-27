"use client"

import type React from "react"
import { useState } from "react"
import { Shield } from "lucide-react"
import Aurora from "@/components/effects/aurora"
import { IP_SUD } from "./lib/config";
export default function LoginPage() {
  const [isRegister, setIsRegister] = useState(false)
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    // ======================
    // REGISTER
    // ======================
    if (isRegister) {
      if (password !== confirmPassword) {
        alert("Passwords do not match")
        return
      }

      try {
        const res = await fetch(`${IP_SUD}/signup`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            username,
            password,
            doorbell_ip: null,
            cctv_ip: null,
            file_destination: null,
          }),
        })

        const data = await res.json()

        if (!res.ok) {
          alert(data.error || "Registration failed")
          return
        }

        alert("Account created successfully!")
        setIsRegister(false)

      } catch {
        alert("Network error during signup")
      }

      return
    }

    // ======================
    // LOGIN
    // ======================
    try {
      const res = await fetch(`${IP_SUD}/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      })

      const data = await res.json()

      if (!res.ok) {
        alert(data.error || "Login failed")
        return
      }

      // 🔐 Store JWT token
      localStorage.setItem("token", data.access_token)

      // --- NEW: decode token to extract identity and persist user_id/email ---
      const getUserIdFromToken = (token: string): string | null => {
        try {
          const payload = JSON.parse(
            atob(token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/"))
          )
          return payload.sub || payload.identity || payload.user_id || null
        } catch {
          return null
        }
      }

      const uid = getUserIdFromToken(data.access_token)
      if (uid) localStorage.setItem("user_id", uid)
      // store email if backend returned it, otherwise save username as a fallback
      if (data.email) localStorage.setItem("email", data.email)
      else localStorage.setItem("email", username)

      window.location.href = "/dashboard"

    } catch {
      alert("Network error during login")
    }
  }

  return (
    // 1. Set relative and overflow-hidden to contain the background
    <div className="relative min-h-screen w-full flex items-center justify-center px-4 overflow-hidden bg-[#0a0a0a]">
      
      {/* 2. Place Aurora as a background layer */}
      <div className="absolute inset-0 z-0">
        <Aurora
          colorStops={["#00d2ff", "#3a7bd5", "#000000"]}
          blend={0.5}
          amplitude={1.0}
          speed={0.5}
        />
      </div>

      {/* 3. Ensure content is relative and has a higher z-index */}
      <div className="relative z-10 w-full max-w-md">
        <div className="text-center mb-12">
          <div className="flex justify-center mb-4">
            <div className="glass p-4 rounded-2xl glow-cyan bg-white/5 backdrop-blur-lg border border-white/10">
              <Shield className="w-12 h-12 text-primary" />
            </div>
          </div>
          <h1 className="text-4xl font-bold mb-2 text-white">SecureHome</h1>
          <p className="text-gray-400">Smart Home Security Control</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 mb-6">
          {/* Added a subtle background to the glass card for better contrast */}
          <div className="glass p-6 rounded-2xl space-y-4 bg-white/5 backdrop-blur-xl border border-white/10 shadow-2xl">
            <div>
              <label className="block text-sm font-medium mb-2 text-gray-200">Username</label>
              <input
                className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:ring-2 focus:ring-primary/50"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2 text-gray-200">Password</label>
              <input
                type="password"
                className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:ring-2 focus:ring-primary/50"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>

            {isRegister && (
              <div>
                <label className="block text-sm font-medium mb-2 text-gray-200">Confirm Password</label>
                <input
                  type="password"
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:ring-2 focus:ring-primary/50"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                />
              </div>
            )}
          </div>

          <button
            type="submit"
            className="w-full bg-primary text-primary-foreground py-3 rounded-lg font-semibold hover:opacity-90 transition-opacity shadow-lg"
          >
            {isRegister ? "Create Account" : "Sign In"}
          </button>
        </form>

        <div className="text-center text-sm">
          <button
            type="button"
            onClick={() => setIsRegister(!isRegister)}
            className="text-primary hover:underline font-medium"
          >
            {isRegister
              ? "Already have an account? Sign in"
              : "Don't have an account? Register"}
          </button>
        </div>
      </div>
    </div>
  )
}
