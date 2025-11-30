"use client"

if (typeof window !== "undefined" && !localStorage.getItem("user_id")) {
  window.location.href = "/";
}

import { useState } from "react"
import { ArrowLeft, Moon, Sun } from "lucide-react"
import Link from "next/link"

if (typeof window !== "undefined" && !localStorage.getItem("token")) window.location.replace("/")

export default function SettingsPage() {
  const [theme, setTheme] = useState("dark")
  const [notifications, setNotifications] = useState(true)
  const [motionAlerts, setMotionAlerts] = useState(true)
  const [doorbellAlerts, setDoorbellAlerts] = useState(true)

  return (
    <div className="p-8 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link href="/dashboard" className="p-2 hover:bg-card rounded-lg transition">
          <ArrowLeft className="w-6 h-6 text-foreground" />
        </Link>
        <div>
          <h1 className="text-3xl font-bold text-foreground">Settings</h1>
          <p className="text-muted-foreground">Manage preferences and devices</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Display Settings */}
        <div className="glass p-6 rounded-2xl space-y-4">
          <h2 className="text-lg font-semibold text-foreground">Display</h2>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-foreground block mb-3">Theme</label>
              <div className="flex gap-3">
                <button
                  onClick={() => setTheme("light")}
                  className={`flex-1 flex items-center justify-center gap-2 py-2 px-4 rounded-lg transition ${
                    theme === "light"
                      ? "bg-primary/20 text-primary border border-primary/50"
                      : "bg-secondary/50 text-foreground hover:bg-secondary"
                  }`}
                >
                  <Sun className="w-4 h-4" />
                  Light
                </button>
                <button
                  onClick={() => setTheme("dark")}
                  className={`flex-1 flex items-center justify-center gap-2 py-2 px-4 rounded-lg transition ${
                    theme === "dark"
                      ? "bg-primary/20 text-primary border border-primary/50"
                      : "bg-secondary/50 text-foreground hover:bg-secondary"
                  }`}
                >
                  <Moon className="w-4 h-4" />
                  Dark
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Notification Settings */}
        <div className="glass p-6 rounded-2xl space-y-4">
          <h2 className="text-lg font-semibold text-foreground">Notifications</h2>
          <div className="space-y-4">
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={notifications}
                onChange={(e) => setNotifications(e.target.checked)}
                className="w-4 h-4 accent-primary"
              />
              <span className="text-sm text-foreground">Enable all notifications</span>
            </label>
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={motionAlerts}
                onChange={(e) => setMotionAlerts(e.target.checked)}
                className="w-4 h-4 accent-primary"
              />
              <span className="text-sm text-foreground">Motion detection alerts</span>
            </label>
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={doorbellAlerts}
                onChange={(e) => setDoorbellAlerts(e.target.checked)}
                className="w-4 h-4 accent-primary"
              />
              <span className="text-sm text-foreground">Doorbell press alerts</span>
            </label>
          </div>
        </div>

        {/* Device Management */}
        <div className="glass p-6 rounded-2xl space-y-4">
          <h2 className="text-lg font-semibold text-foreground">Connected Devices</h2>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-secondary/50 rounded-lg">
              <div>
                <p className="font-semibold text-sm text-foreground">Front Door Camera</p>
                <p className="text-xs text-muted-foreground">Status: Online</p>
              </div>
              <div className="w-2 h-2 bg-primary rounded-full animate-pulse"></div>
            </div>
            <div className="flex items-center justify-between p-3 bg-secondary/50 rounded-lg">
              <div>
                <p className="font-semibold text-sm text-foreground">Backyard Camera</p>
                <p className="text-xs text-muted-foreground">Status: Online</p>
              </div>
              <div className="w-2 h-2 bg-primary rounded-full animate-pulse"></div>
            </div>
          </div>
        </div>

        {/* Account Settings */}
        <div className="glass p-6 rounded-2xl space-y-4">
          <h2 className="text-lg font-semibold text-foreground">Account</h2>
          <div className="space-y-3">
            <button className="w-full text-left p-3 hover:bg-card/50 rounded-lg transition text-sm text-foreground">
              Change Password
            </button>
            <button className="w-full text-left p-3 hover:bg-card/50 rounded-lg transition text-sm text-foreground">
              Two-Factor Authentication
            </button>
            <button className="w-full text-left p-3 hover:bg-destructive/10 rounded-lg transition text-sm text-destructive">
              Delete Account
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
