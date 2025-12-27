// import { NextResponse } from "next/server"
// import { GoogleGenerativeAI } from "@google/generative-ai"

// // DB imports
// import {
//   getLastVisitor,
//   getAllVisitors,
//   type Visitor,
// } from "@/lib/queries"

// // ===============================
// // CONFIG
// // ===============================
// const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY || "")
// const CACHE_TTL_MS = 60 * 1000
// const RATE_LIMIT_MS = 1500

// const cache = new Map<string, { reply: string; timestamp: number }>()
// let lastRequestTime = 0

// // ===============================
// // HELPER FUNCTIONS
// // ===============================
// function formatVisitor(v: Visitor) {
//   const ts = new Date(v.timestamp).toLocaleString()
//   return `• ${v.name} — ${ts} (Purpose: ${v.purpose}, ID: ${v.id})`
// }

// function startOfDay(d: Date) {
//   const x = new Date(d)
//   x.setHours(0, 0, 0, 0)
//   return x
// }

// function endOfDay(d: Date) {
//   const x = new Date(d)
//   x.setHours(23, 59, 59, 999)
//   return x
// }

// function toMs(d: Date) {
//   return d.getTime()
// }

// function parseTimeToMinutes(hoursStr: string, minutesStr?: string, ampm?: string) {
//   let h = parseInt(hoursStr, 10)
//   const m = minutesStr ? parseInt(minutesStr, 10) : 0

//   if (ampm) {
//     if (ampm.toLowerCase() === "pm" && h !== 12) h += 12
//     if (ampm.toLowerCase() === "am" && h === 12) h = 0
//   }

//   return h * 60 + m
// }

// // ===============================
// // POST Handler
// // ===============================
// export async function POST(req: Request) {
//   const now = Date.now()

//   if (now - lastRequestTime < RATE_LIMIT_MS) {
//     return NextResponse.json({
//       reply: "⚠ Please wait a moment before sending another question.",
//     })
//   }
//   lastRequestTime = now

//   try {
//     const { message } = await req.json()
//     const q = message.trim().toLowerCase()

//     // ----- CACHE -----
//     const cached = cache.get(q)
//     if (cached && now - cached.timestamp < CACHE_TTL_MS) {
//       return NextResponse.json({ reply: cached.reply })
//     }

//     const mentionsVisitorsOrLogs =
//       q.includes("visitor") ||
//       q.includes("visitors") ||
//       q.includes("who came") ||
//       q.includes("who all came") ||
//       q.includes("who all came home") ||
//       q.includes("logs") ||
//       q.includes("entries")

//     // ===============================
//     // DATABASE LOGIC (no casts)
//     // ===============================

//     // ---- 1. Visitor before last ----
//     if (
//       q.includes("visitor before last") ||
//       q.includes("before the last visitor") ||
//       q.includes("before last visitor")
//     ) {
//       const rows = await getAllVisitors()

//       if (rows.length < 2) {
//         const reply = "I checked the SecureHome logs — there is no visitor recorded before the last one."
//         cache.set(q, { reply, timestamp: now })
//         return NextResponse.json({ reply })
//       }

//       const reply = `I checked the SecureHome logs — the visitor before the last one was:\n\n${formatVisitor(rows[1])}`
//       cache.set(q, { reply, timestamp: now })
//       return NextResponse.json({ reply })
//     }

//     // ---- 2. Last visitor ----
//     if (
//       q.includes("last visitor") ||
//       q.includes("who entered last") ||
//       q.includes("who came last") ||
//       q.includes("who came home last") ||
//       q.includes("recent visitor") ||
//       q.includes("latest visitor") ||
//       q.includes("last person") ||
//       q.includes("last entry") ||
//       q.includes("recent entry")
//     ) {
//       const row = await getLastVisitor()

//       if (!row) {
//         const reply = "I checked the SecureHome logs — no visitors found."
//         cache.set(q, { reply, timestamp: now })
//         return NextResponse.json({ reply })
//       }

//       const reply = `I checked the SecureHome logs — the most recent visitor was:\n\n${formatVisitor(row)}`
//       cache.set(q, { reply, timestamp: now })
//       return NextResponse.json({ reply })
//     }

//     // ---- 3. ID-based search ----
//     const idMatch = q.match(/\bid[: ]?(\d+)\b/)
//     if (idMatch) {
//       const id = parseInt(idMatch[1], 10)
//       const rows = await getAllVisitors()
//       const visitor = rows.find((v) => v.id === id)

//       const reply = visitor
//         ? `I checked the SecureHome logs — here are the details for visitor ID ${id}:\n\n${formatVisitor(visitor)}`
//         : `I checked the SecureHome logs — no visitor found with ID ${id}.`

//       cache.set(q, { reply, timestamp: now })
//       return NextResponse.json({ reply })
//     }

//     // ---- 4. Name-based search ----
//     const namePatterns = [
//       /visits? by ([a-z ]+)/i,
//       /logs? for ([a-z ]+)/i,
//       /entries for ([a-z ]+)/i,
//       /when did ([a-z ]+) (visit|come)/i,
//       /did ([a-z ]+) (visit|come)/i,
//       /show all visits (?:of|by) ([a-z ]+)/i,
//     ]

//     let name: string | null = null
//     for (const r of namePatterns) {
//       const m = message.match(r)
//       if (m) {
//         name = m[1].trim()
//         break
//       }
//     }

//     if (name) {
//       const rows = await getAllVisitors()
//       const filtered = rows.filter((v) =>
//         v.name.toLowerCase().includes(name!.toLowerCase())
//       )

//       const reply = filtered.length
//         ? `I checked the SecureHome logs — here are the visits matching "${name}":\n\n${filtered
//             .map(formatVisitor)
//             .join("\n")}`
//         : `I checked the SecureHome logs — no visits found for "${name}".`

//       cache.set(q, { reply, timestamp: now })
//       return NextResponse.json({ reply })
//     }

//     // ---- 5. Purpose-based ----
//     const purposeMatch = message.match(/(?:purpose (?:was|of)|for) ([a-z ]+)/i)
//     if (purposeMatch && mentionsVisitorsOrLogs) {
//       const purpose = purposeMatch[1].trim()
//       const rows = await getAllVisitors()

//       const filtered = rows.filter((v) =>
//         v.purpose.toLowerCase().includes(purpose.toLowerCase())
//       )

//       const reply = filtered.length
//         ? `I checked the SecureHome logs — here are visitors whose purpose matches "${purpose}":\n\n${filtered
//             .map(formatVisitor)
//             .join("\n")}`
//         : `I checked the SecureHome logs — no visitors found with purpose "${purpose}".`

//       cache.set(q, { reply, timestamp: now })
//       return NextResponse.json({ reply })
//     }

//     // ---- 6. Time-based ----
//     const timeAtMatch = q.match(/(?:at|around)\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?/)
//     const timeBetweenMatch = q.match(/between\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\s+and\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?/)

//     if (mentionsVisitorsOrLogs && (timeAtMatch || timeBetweenMatch)) {
//       const rows = await getAllVisitors()

//       const withMinutes = rows.map((v) => {
//         const d = new Date(v.timestamp)
//         return { v, minutes: d.getHours() * 60 + d.getMinutes() }
//       })

//       let filtered: { v: Visitor; minutes: number }[] = []

//       if (timeBetweenMatch) {
//         const [, h1, m1, a1, h2, m2, a2] = timeBetweenMatch
//         const min1 = parseTimeToMinutes(h1, m1, a1)
//         const min2 = parseTimeToMinutes(h2, m2, a2)
//         filtered = withMinutes.filter((x) => x.minutes >= min1 && x.minutes <= min2)
//       } else if (timeAtMatch) {
//         const [, h, m, a] = timeAtMatch
//         const target = parseTimeToMinutes(h, m, a)
//         filtered = withMinutes.filter((x) => Math.abs(x.minutes - target) <= 15)
//       }

//       const reply = filtered.length
//         ? `I checked the SecureHome logs — here are visitors matching that time:\n\n${filtered
//             .map((x) => formatVisitor(x.v))
//             .join("\n")}`
//         : "I checked the SecureHome logs — no visitors found for that time."

//       cache.set(q, { reply, timestamp: now })
//       return NextResponse.json({ reply })
//     }

//     // ---- 7. Morning/Afternoon/Evening/Night ----
//     if (
//       mentionsVisitorsOrLogs &&
//       (q.includes("morning") || q.includes("afternoon") || q.includes("evening") || q.includes("night"))
//     ) {
//       let startMin = 0,
//         endMin = 1440,
//         label = ""

//       if (q.includes("morning")) {
//         label = "morning"
//         startMin = 300
//         endMin = 720
//       }
//       if (q.includes("afternoon")) {
//         label = "afternoon"
//         startMin = 720
//         endMin = 1020
//       }
//       if (q.includes("evening")) {
//         label = "evening"
//         startMin = 1020
//         endMin = 1260
//       }
//       if (q.includes("night")) {
//         label = "night"
//       }

//       const rows = await getAllVisitors()

//       const filtered = rows.filter((v) => {
//         const d = new Date(v.timestamp)
//         const min = d.getHours() * 60 + d.getMinutes()

//         if (label === "night") return min >= 1260 || min < 300
//         return min >= startMin && min <= endMin
//       })

//       const reply = filtered.length
//         ? `I checked the SecureHome logs — here are visitors who came in the ${label}:\n\n${filtered
//             .map(formatVisitor)
//             .join("\n")}`
//         : `I checked the SecureHome logs — no visitors came in the ${label}.`

//       cache.set(q, { reply, timestamp: now })
//       return NextResponse.json({ reply })
//     }

//     // ---- 8. Date-based queries ----
//     const lastDaysMatch = q.match(/last (\d+) days?/)
//     let rangeStart: number | null = null
//     let rangeEnd: number | null = null
//     let label: string | null = null

//     const today = new Date()

//     if (mentionsVisitorsOrLogs) {
//       if (q.includes("today")) {
//         rangeStart = toMs(startOfDay(today))
//         rangeEnd = toMs(endOfDay(today))
//         label = "today"
//       } else if (q.includes("yesterday")) {
//         const y = new Date(today)
//         y.setDate(y.getDate() - 1)
//         rangeStart = toMs(startOfDay(y))
//         rangeEnd = toMs(endOfDay(y))
//         label = "yesterday"
//       } else if (q.includes("this week")) {
//         const d = new Date(today)
//         const diff = (d.getDay() + 6) % 7
//         d.setDate(d.getDate() - diff)
//         rangeStart = toMs(startOfDay(d))
//         rangeEnd = toMs(endOfDay(today))
//         label = "this week"
//       } else if (q.includes("last week")) {
//         const d = new Date(today)
//         const diff = (d.getDay() + 6) % 7
//         d.setDate(d.getDate() - diff - 7)
//         const sw = startOfDay(d)
//         const ew = new Date(sw)
//         ew.setDate(ew.getDate() + 6)
//         rangeStart = toMs(sw)
//         rangeEnd = toMs(endOfDay(ew))
//         label = "last week"
//       } else if (lastDaysMatch) {
//         const n = parseInt(lastDaysMatch[1], 10)
//         const start = new Date(today)
//         start.setDate(start.getDate() - (n - 1))
//         rangeStart = toMs(startOfDay(start))
//         rangeEnd = toMs(endOfDay(today))
//         label = `last ${n} days`
//       }
//     }

//     if (rangeStart !== null && rangeEnd !== null && label) {
//       const rows = await getAllVisitors()

//       const filtered = rows.filter((v) => {
//         const ts = new Date(v.timestamp).getTime()
//         return ts >= rangeStart! && ts <= rangeEnd!
//       })

//       const reply = filtered.length
//         ? `I checked the SecureHome logs — here are visitors from ${label}:\n\n${filtered
//             .map(formatVisitor)
//             .join("\n")}`
//         : `I checked the SecureHome logs — no visitors found for ${label}.`

//       cache.set(q, { reply, timestamp: now })
//       return NextResponse.json({ reply })
//     }

//     // ---- 9. List all visitors ----
//     if (
//       q.includes("all visitors") ||
//       q.includes("visitor logs") ||
//       q.includes("show visitors") ||
//       q.includes("full logs") ||
//       q.includes("entire log") ||
//       q.includes("who all came") ||
//       q.includes("list visitors") ||
//       q.includes("show me all entries") ||
//       q.includes("show visitor history")
//     ) {
//       const rows = await getAllVisitors()

//       const reply = rows.length
//         ? `Here are the visitor logs:\n\n${rows.map(formatVisitor).join("\n")}`
//         : "I checked the logs — no visitors recorded."

//       cache.set(q, { reply, timestamp: now })
//       return NextResponse.json({ reply })
//     }

//     // ===============================
//     // GEMINI FALLBACK
//     // ===============================
//     const model = genAI.getGenerativeModel({ model: "gemini-2.5-flash" })
//     const prompt = `
// You are SecureHome Assistant — answer questions about the home, logs and security.

// If the question requires checking logs, always respond with:
// "I'll check the SecureHome logs for that."

// Fields in visitor logs:
// - name
// - timestamp (text like "2025-11-17 15:25:37")
// - purpose
// - id

// Be precise, short, and security-focused.

// User said: "${message}"
// `

//     const result = await model.generateContent(prompt)
//     const reply = result.response.text()

//     cache.set(q, { reply, timestamp: now })
//     return NextResponse.json({ reply })

//   } catch (error) {
//     console.error("❌ Error:", error)

//     return NextResponse.json(
//       { reply: "⚠ Something went wrong while processing your request." },
//       { status: 500 }
//     )
//   }
// }
