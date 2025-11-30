"use client"

import type React from "react"
import { useState } from "react"
import { Shield } from "lucide-react"

export default function LoginPage() {
  const [isRegister, setIsRegister] = useState(false)
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [housePassword, setHousePassword] = useState("")

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    // REGISTER MODE
    if (isRegister) {
      if (password !== confirmPassword) {
        alert("Passwords do not match")
        return
      }

      try {
        const res = await fetch("http://127.0.0.1:5000/api/users/create", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            email,
            password,
            house_password: housePassword, // 🌟 include house password
          }),
        })

        const data = await res.json()
        if (data.status !== "ok") {
          alert(data.error || "Registration failed")
          return
        }

        alert("Account created successfully!")
        setIsRegister(false) // switch to login screen

      } catch (err) {
        alert("Network error while creating user")
      }

      return
    }

    // LOGIN MODE
    try {
      const res = await fetch("http://127.0.0.1:5000/api/users/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      })

      const data = await res.json()

      if (data.status !== "ok") {
        alert(data.error || "Login failed")
        return
      }

      // save user locally
      localStorage.setItem("user_id", data.user_id.toString())
      localStorage.setItem("email", data.email)

      window.location.href = "/dashboard"

    } catch (err) {
      alert("Network error while logging in")
    }
  }

  return (
    <div className="min-h-screen bg-background flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        {/* Title */}
        <div className="text-center mb-12">
          <div className="flex justify-center mb-4">
            <div className="glass p-4 rounded-2xl glow-cyan">
              <Shield className="w-12 h-12 text-primary" />
            </div>
          </div>
          <h1 className="text-4xl font-bold text-foreground mb-2">SecureHome</h1>
          <p className="text-muted-foreground">Smart Home Security Control</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 mb-6">
          <div className="glass p-6 rounded-2xl space-y-4">

            {/* Email */}
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">Email</label>
              <input
                type="email"
                className="w-full bg-input border border-border rounded-lg px-4 py-2.5"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            {/* Password */}
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">Password</label>
              <input
                type="password"
                className="w-full bg-input border border-border rounded-lg px-4 py-2.5"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>

            {/* Confirm Password (Register Only) */}
            {isRegister && (
              <>
                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">Confirm Password</label>
                  <input
                    type="password"
                    className="w-full bg-input border border-border rounded-lg px-4 py-2.5"
                    placeholder="••••••••"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    required
                  />
                </div>

                {/* 🌟 House Password (Register Only) */}
                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">House Password</label>
                  <input
                    type="password"
                    className="w-full bg-input border border-border rounded-lg px-4 py-2.5"
                    placeholder="Enter home password"
                    value={housePassword}
                    onChange={(e) => setHousePassword(e.target.value)}
                    required
                  />
                </div>
              </>
            )}

          </div>

          <button
            type="submit"
            className="w-full bg-primary text-primary-foreground font-semibold py-3 rounded-lg glow-cyan"
          >
            {isRegister ? "Create Account" : "Sign In"}
          </button>
        </form>

        <div className="text-center text-sm text-muted-foreground space-y-2">
          <button
            type="button"
            onClick={() => setIsRegister(!isRegister)}
            className="text-primary hover:underline"
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
