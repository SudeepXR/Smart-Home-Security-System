"use client";

import { useState } from "react";
import { Send, Bot, User } from "lucide-react";
import { IP_SUD } from "@/app/lib/config";
if (typeof window !== "undefined" && !localStorage.getItem("user_id")) {
  window.location.href = "/";
}

export default function AssistantPage() {
  const [messages, setMessages] = useState([
    { sender: "bot", text: "👋 Hi! I'm your SecureHome Assistant. How can I help you today?" },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);


  const sendMessage = async () => {
  if (!input.trim()) return;

  const userMsg = { sender: "user", text: input };
  setMessages((prev) => [...prev, userMsg]);
  setInput("");
  setLoading(true);

  try {
    const token = localStorage.getItem("token");

    const res = await fetch(`${IP_SUD}/api/assistant`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ message: userMsg.text }),
    });

    const data = await res.json();

    setMessages((prev) => [
      ...prev,
      { sender: "bot", text: data.reply },
    ]);
  } catch (err) {
    setMessages((prev) => [
      ...prev,
      { sender: "bot", text: "⚠️ Backend assistant unavailable." },
    ]);
  } finally {
    setLoading(false);
  }
};


  return (
    <div className="p-8 space-y-6">

      {/* 🔥 NEW BUTTON */}

      <h1 className="text-3xl font-bold text-foreground">AI Assistant</h1>
      <p className="text-muted-foreground">Ask about recent entries, alerts, or system events.</p>

      <div className="glass rounded-2xl p-6 h-[77vh] flex flex-col">
        {/* Chat messages */}
        <div className="flex-1 overflow-y-auto space-y-4 mb-4 scrollbar-thin">
          {messages.map((msg, idx) => (
            <div key={idx} className={`flex ${msg.sender === "user" ? "justify-end" : "justify-start"}`}>
              <div
                className={`p-3 rounded-2xl max-w-[75%] ${
                  msg.sender === "user"
                    ? "bg-primary/20 text-primary"
                    : "bg-secondary/50 text-foreground"
                }`}
              >
                <div className="flex items-center gap-2 mb-1">
                  {msg.sender === "user" ? (
                    <User className="w-4 h-4" />
                  ) : (
                    <Bot className="w-4 h-4" />
                  )}
                  <span className="text-sm font-medium capitalize">
                    {msg.sender === "user" ? "You" : "Assistant"}
                  </span>
                </div>
                <p className="text-sm leading-relaxed">{msg.text}</p>
              </div>
            </div>
          ))}
          {loading && <p className="text-muted-foreground text-sm animate-pulse">Thinking...</p>}
        </div>

        {/* Input box */}
        <div className="flex items-center gap-3">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && sendMessage()}
            placeholder="Ask about your home's security..."
            className="flex-1 bg-secondary/40 border border-border text-foreground rounded-xl px-4 py-2 outline-none focus:ring-2 focus:ring-primary/50"
          />
          <button
            onClick={sendMessage}
            disabled={loading}
            className="bg-primary text-primary-foreground px-4 py-2 rounded-xl hover:opacity-90 transition flex items-center gap-2"
          >
            <Send className="w-4 h-4" />
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
