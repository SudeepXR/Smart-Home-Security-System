import { NextResponse } from "next/server";
import { GoogleGenerativeAI } from "@google/generative-ai";

// DB imports
import { getLastVisitor, getAllVisitors } from "@/lib/queries";

// ===============================
// CONFIG
// ===============================
const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY || "");
const CACHE_TTL_MS = 60 * 1000;
const RATE_LIMIT_MS = 1500;

const cache = new Map<string, { reply: string; timestamp: number }>();
let lastRequestTime = 0;

// ===============================
// POST Handler
// ===============================
export async function POST(req: Request) {
  const now = Date.now();

  if (now - lastRequestTime < RATE_LIMIT_MS) {
    return NextResponse.json({
      reply: "⚠️ Please wait a moment before sending another question.",
    });
  }
  lastRequestTime = now;

  try {
    const { message } = await req.json();
    const q = message.trim().toLowerCase();

    // ----- Cache -----
    const cached = cache.get(q);
    if (cached && now - cached.timestamp < CACHE_TTL_MS) {
      return NextResponse.json({ reply: cached.reply });
    }

    // ===============================
    // DATABASE LOGIC
    // ===============================
    if (
      q.includes("who entered last") ||
      q.includes("last") ||
      q.includes("last visitor") ||
      q.includes("recent visitor") ||
      q.includes("who came last")
    ) {
      const row = await getLastVisitor();

      if (!row) {
        const reply = "I checked the SecureHome logs — no visitors found.";
        cache.set(q, { reply, timestamp: now });
        return NextResponse.json({ reply });
      }

      const reply = `I checked the SecureHome logs — the most recent visitor was \n\n${row.name} at \n\n${row.timestamp}, for \n\n${row.purpose}.`;
      cache.set(q, { reply, timestamp: now });
      return NextResponse.json({ reply });
    }

    if (
      q.includes("all visitors") ||
      q.includes("visitor logs") ||
      q.includes("show visitors") ||
      q.includes("who all came") ||
      q.includes("list visitors")
    ) {
      const rows = await getAllVisitors();

      if (!rows.length) {
        const reply = "I checked the logs — no visitors recorded.";
        cache.set(q, { reply, timestamp: now });
        return NextResponse.json({ reply });
      }

      const list = rows
        .map((v) => `• ${v.name} — ${v.timestamp} (${v.purpose})`)
        .join("\n");

      const reply = `Here are the visitor logs:\n\n${list}`;
      cache.set(q, { reply, timestamp: now });
      return NextResponse.json({ reply });
    }

    // ===============================
    // GEMINI FALLBACK
    // ===============================
    const model = genAI.getGenerativeModel({ model: "gemini-2.5-flash" });

    const prompt = `
You are SecureHome Assistant — answer questions about the home, logs and security.
If the question requires checking logs, respond with:
"I'll check the SecureHome logs for that."

User: "${message}"
`;

    const result = await model.generateContent(prompt);
    const reply = result.response.text();

    cache.set(q, { reply, timestamp: now });
    return NextResponse.json({ reply });
  } catch (error: any) {
    console.error("❌ Gemini API error:", error);

    return NextResponse.json(
      {
        reply: "⚠️ Something went wrong while processing your request.",
      },
      { status: 500 }
    );
  }
}
