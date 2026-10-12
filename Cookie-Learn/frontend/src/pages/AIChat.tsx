// AI Teacher chat page - converses with the AI language tutor "Cookie"
import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import { motion } from "framer-motion";
import { Loader2, Send, Sparkles } from "lucide-react";
import type { ChatMessage } from "@/types";
import { useAuth } from "@/contexts/AuthContext";

export default function AIChat() {
  const { user } = useAuth();
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [text, setText] = useState("");
  const [sending, setSending] = useState(false);
  const listRef = useRef<HTMLDivElement>(null);

  // Load the most recent teacher chat session on mount
  useEffect(() => {
    api.get("/ai/chat/sessions?session_kind=teacher").then(({ data }) => {
      if (data.length) {
        setSessionId(data[0].session_id);
        api.get<ChatMessage[]>(`/ai/chat/${data[0].session_id}`).then(({ data }) => setMessages(data));
      }
    });
  }, []);

  // Auto-scroll to the latest message
  useEffect(() => { listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: "smooth" }); }, [messages]);

  // Send a message to the AI and get a response
  async function send() {
    if (!text.trim() || sending) return;
    const msg = text.trim();
    setText("");
    setSending(true);
    setMessages((m) => [...m, { id: `tmp-${Date.now()}`, role: "user", content: msg, created_at: new Date().toISOString() }]);
    try {
      const { data } = await api.post("/ai/chat", { message: msg, session_id: sessionId, session_kind: "teacher", language_code: user?.active_language_code });
      setSessionId(data.session_id);
      setMessages(data.messages);
    } catch {
      setMessages((m) => [...m, { id: `err-${Date.now()}`, role: "assistant", content: "AI is not available right now.", created_at: new Date().toISOString() }]);
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="max-w-3xl mx-auto flex flex-col h-[calc(100vh-8rem)]">
      {/* Chat header */}
      <div className="card-surface p-6 mb-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-2xl bg-primary/20 border-2 border-primary flex items-center justify-center text-2xl">🍪</div>
          <div>
            <div className="font-heading font-black text-lg">Cookie · AI Teacher</div>
            <div className="text-xs text-muted-foreground flex items-center gap-1"><Sparkles className="w-3 h-3" /> Gemini 3.1 Flash Lite</div>
          </div>
        </div>
      </div>
      {/* Messages list */}
      <div ref={listRef} className="flex-1 overflow-y-auto space-y-3 p-2" data-testid="chat-messages">
        {messages.length === 0 && (
          <div className="text-center text-muted-foreground py-16">
            <p className="mb-2">You can ask Cookie any language question.</p>
            <p className="text-xs">E.g.: "What's the difference between 'Have to' and 'Must'?"</p>
          </div>
        )}
        {messages.map((m) => (
          <motion.div key={m.id} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-[85%] px-4 py-3 rounded-2xl text-sm whitespace-pre-wrap ${m.role === "user" ? "bg-primary text-primary-foreground rounded-tr-sm" : "bg-muted rounded-tl-sm"}`} data-testid={`chat-msg-${m.role}`}>
              {m.content}
            </div>
          </motion.div>
        ))}
        {sending && <div className="flex gap-2 text-muted-foreground text-sm items-center"><Loader2 className="w-4 h-4 animate-spin" /> Cookie is thinking...</div>}
      </div>
      {/* Input bar */}
      <div className="mt-3 flex gap-2">
        <input
          data-testid="chat-input"
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter") send(); }}
          placeholder="Ask something..."
          className="flex-1 px-4 py-3 rounded-2xl bg-muted border-2 border-transparent focus:border-primary outline-none"
        />
        <button onClick={send} disabled={sending || !text.trim()} className="btn-primary" data-testid="chat-send">
          <Send className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
}
