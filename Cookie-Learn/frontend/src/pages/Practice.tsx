// Speaking practice page - chat with AI in target language with speech synthesis
import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import { motion } from "framer-motion";
import { Loader2, Send, MessageCircle, Volume2 } from "lucide-react";
import type { ChatMessage } from "@/types";
import { useAuth } from "@/contexts/AuthContext";

export default function Practice() {
  const { user } = useAuth();
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [text, setText] = useState("");
  const [sending, setSending] = useState(false);
  const listRef = useRef<HTMLDivElement>(null);
  const lang = user?.active_language_code || "en";

  // Load the most recent practice session on mount
  useEffect(() => {
    api.get("/ai/chat/sessions?session_kind=practice").then(({ data }) => {
      if (data.length) {
        setSessionId(data[0].session_id);
        api.get<ChatMessage[]>(`/ai/chat/${data[0].session_id}`).then(({ data }) => setMessages(data));
      }
    });
  }, []);

  useEffect(() => { listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: "smooth" }); }, [messages]);

  // Text-to-speech for AI responses
  function speak(t: string) {
    if (typeof window === "undefined") return;
    const u = new SpeechSynthesisUtterance(t);
    const map: Record<string, string> = { en: "en-US", tr: "tr-TR", de: "de-DE", fr: "fr-FR", es: "es-ES", it: "it-IT", ja: "ja-JP", ko: "ko-KR", ru: "ru-RU", az: "az-AZ" };
    u.lang = map[lang] || "en-US"; u.rate = 0.95;
    window.speechSynthesis.cancel(); window.speechSynthesis.speak(u);
  }

  // Send a message in the target language
  async function send() {
    if (!text.trim() || sending) return;
    const msg = text.trim();
    setText(""); setSending(true);
    setMessages((m) => [...m, { id: `tmp-${Date.now()}`, role: "user", content: msg, created_at: new Date().toISOString() }]);
    try {
      const { data } = await api.post("/ai/chat", { message: msg, session_id: sessionId, session_kind: "practice", language_code: lang });
      setSessionId(data.session_id);
      setMessages(data.messages);
    } catch {
      setMessages((m) => [...m, { id: `err-${Date.now()}`, role: "assistant", content: "Could not connect.", created_at: new Date().toISOString() }]);
    } finally { setSending(false); }
  }

  return (
    <div className="max-w-3xl mx-auto flex flex-col h-[calc(100vh-8rem)]">
      <div className="card-surface p-6 mb-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-2xl bg-secondary/20 border-2 border-secondary flex items-center justify-center"><MessageCircle className="w-6 h-6 text-secondary" /></div>
          <div>
            <div className="font-heading font-black text-lg">Speaking Practice</div>
            <div className="text-xs text-muted-foreground">Active language: <b className="uppercase">{lang}</b> · AI responds like a native speaker</div>
          </div>
        </div>
      </div>
      <div ref={listRef} className="flex-1 overflow-y-auto space-y-3 p-2" data-testid="practice-messages">
        {messages.length === 0 && <div className="text-center text-muted-foreground py-16">Practice your conversation skills. Type in the target language and Cookie will respond naturally.</div>}
        {messages.map((m) => (
          <motion.div key={m.id} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-[85%] px-4 py-3 rounded-2xl text-sm whitespace-pre-wrap flex flex-col gap-2 ${m.role === "user" ? "bg-secondary text-secondary-foreground rounded-tr-sm" : "bg-muted rounded-tl-sm"}`} data-testid={`practice-msg-${m.role}`}>
              <span>{m.content}</span>
              {m.role === "assistant" && (
                <button onClick={() => speak(m.content)} className="self-end p-1 rounded-lg hover:bg-background/50" aria-label="Speak"><Volume2 className="w-4 h-4" /></button>
              )}
            </div>
          </motion.div>
        ))}
        {sending && <div className="flex gap-2 text-muted-foreground text-sm items-center"><Loader2 className="w-4 h-4 animate-spin" /> Typing...</div>}
      </div>
      <div className="mt-3 flex gap-2">
        <input data-testid="practice-input" value={text} onChange={(e) => setText(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter") send(); }} placeholder="Write in target language..." className="flex-1 px-4 py-3 rounded-2xl bg-muted border-2 border-transparent focus:border-secondary outline-none" />
        <button onClick={send} disabled={sending || !text.trim()} className="btn-secondary" data-testid="practice-send"><Send className="w-5 h-5" /></button>
      </div>
    </div>
  );
}
