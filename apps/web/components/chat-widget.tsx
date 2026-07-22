"use client";

import { useEffect, useRef, useState } from "react";

import { cn } from "@/lib/utils";

// Chat calls are same-origin and proxied to FastAPI by the Next rewrite.
// The Ollama key never reaches this code — FastAPI holds it server-side.
const API = process.env.NEXT_PUBLIC_API_URL ?? "";

interface Message {
  role: "user" | "assistant";
  content: string;
}

const GREETING: Message = {
  role: "assistant",
  content:
    "Hi! I'm Ridgeline Assistant. Ask me about floor plans, pricing estimates, pets, or the neighborhood — or I can help you set up a tour.",
};

export function ChatWidget() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([GREETING]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [leadSaved, setLeadSaved] = useState(false);
  const sessionRef = useRef<number | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [messages, open]);

  useEffect(() => {
    const stored = sessionStorage.getItem("ridgeline_session");
    if (stored) sessionRef.current = Number(stored);
    if (sessionStorage.getItem("ridgeline_saved") === "1") setLeadSaved(true);
  }, []);

  async function send() {
    const text = input.trim();
    if (!text || busy) return;
    setInput("");
    setBusy(true);
    setMessages((m) => [...m, { role: "user", content: text }, { role: "assistant", content: "" }]);

    try {
      const res = await fetch(`${API}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionRef.current, message: text }),
      });
      if (!res.ok || !res.body) throw new Error(`chat failed: ${res.status}`);

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let done = false;
      while (!done) {
        const chunk = await reader.read();
        done = chunk.done;
        buffer += decoder.decode(chunk.value ?? new Uint8Array(), { stream: !done });
        const events = buffer.split("\n\n");
        buffer = events.pop() ?? "";
        for (const event of events) {
          if (!event.startsWith("data: ")) continue;
          const data = JSON.parse(event.slice(6));
          if (data.delta) {
            setMessages((m) => {
              const next = [...m];
              next[next.length - 1] = {
                role: "assistant",
                content: next[next.length - 1].content + data.delta,
              };
              return next;
            });
          }
          if (data.done && data.session_id) {
            sessionRef.current = data.session_id;
            sessionStorage.setItem("ridgeline_session", String(data.session_id));
          }
        }
      }

      // Fire lead extraction after the exchange; show the "saved" chip once
      // the office has a way to reach the visitor.
      if (sessionRef.current != null) {
        fetch(`${API}/api/chat/extract`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ session_id: sessionRef.current }),
        })
          .then((r) => (r.ok ? r.json() : null))
          .then((body) => {
            if (body?.has_contact) {
              setLeadSaved(true);
              sessionStorage.setItem("ridgeline_saved", "1");
            }
          })
          .catch(() => {});
      }
    } catch {
      setMessages((m) => {
        const next = [...m];
        next[next.length - 1] = {
          role: "assistant",
          content:
            "Sorry — I couldn't connect just now. Please call the office at 248-377-2680 (Mon–Fri 9:30–5).",
        };
        return next;
      });
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="fixed bottom-5 right-5 z-50">
      {open && (
        <div
          className="mb-3 flex h-[28rem] w-[min(22rem,calc(100vw-2.5rem))] flex-col overflow-hidden rounded-2xl border border-cream-dark bg-white shadow-2xl"
          role="dialog"
          aria-label="Chat with Ridgeline Assistant"
        >
          <div className="bg-pine-800 px-4 py-3 text-cream">
            <p className="font-display">Ridgeline Assistant</p>
            <p className="text-xs text-cream/70">
              Estimates only — the office confirms final pricing.
            </p>
          </div>

          <div ref={scrollRef} className="flex-1 space-y-3 overflow-y-auto p-4" aria-live="polite">
            {messages.map((m, i) => (
              <div
                key={i}
                className={cn(
                  "max-w-[85%] rounded-2xl px-3.5 py-2 text-sm whitespace-pre-wrap",
                  m.role === "user"
                    ? "ml-auto rounded-br-sm bg-pine-700 text-cream"
                    : "rounded-bl-sm bg-cream text-charcoal"
                )}
              >
                {m.content || (busy && i === messages.length - 1 ? "…" : "")}
              </div>
            ))}
            {leadSaved && (
              <p
                className="rounded-full bg-pine-100 px-3 py-1.5 text-center text-xs font-semibold text-pine-800"
                role="status"
              >
                ✓ Saved — the office will follow up.
              </p>
            )}
          </div>

          <form
            className="flex gap-2 border-t border-cream-dark p-3"
            onSubmit={(e) => {
              e.preventDefault();
              send();
            }}
          >
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              maxLength={2000}
              placeholder="Ask about floor plans, pets…"
              aria-label="Your message"
              className="w-full rounded-full border border-charcoal/20 px-3.5 py-2 text-sm"
            />
            <button
              type="submit"
              disabled={busy || !input.trim()}
              className="rounded-full bg-pine-700 px-4 py-2 text-sm font-semibold text-cream disabled:opacity-50"
            >
              Send
            </button>
          </form>
        </div>
      )}

      <button
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        className="ml-auto flex items-center gap-2 rounded-full bg-brass px-5 py-3 font-semibold text-charcoal shadow-lg hover:opacity-90"
      >
        {open ? "Close chat" : "Chat with us"}
      </button>
    </div>
  );
}
