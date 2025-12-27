"use client"

import { useEffect } from "react"

export default function SettingsPage() {
	useEffect(() => {
		if (typeof window !== "undefined") {
			window.location.href = "/dashboard"
		}
	}, [])

	return null
}
