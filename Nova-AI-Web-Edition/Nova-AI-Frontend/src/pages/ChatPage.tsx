// src/pages/ChatPage.tsx
import { useCallback, useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { useNavigate, useParams } from "react-router-dom";
import { Lightbulb, Code2, Target, Salad, RefreshCw, AlertTriangle, X } from "lucide-react";
import { useAppStore } from "../store/useAppStore";
import Sidebar, { SidebarToggleButton } from "../components/Sidebar";
import ChatMessage from "../components/ChatMessage";
import { TypingIndicator, WebSearchIndicator, ThinkingIndicator, ImageAnalyzingIndicator } from "../components/TypingIndicator";
import ChatInput from "../components/ChatInput";

const SUGGESTIONS = [
  { icon: Lightbulb, text: "What do you think about the future of AI?" },
  { icon: Code2, text: "Write a quicksort algorithm in Python" },
  { icon: Target, text: "Say something to motivate me today" },
  { icon: Salad, text: "Suggest a healthy weekly meal plan" },
];

const WEB_KEYWORDS = [
  "news", "weather", "price", "dollar", "gold", "stock market", "how many", "euro",
  "today", "current", "who", "breaking", "match", "score", "rate", "bitcoin",
  "crypto", "election", "earthquake", "fire", "traffic", "flight", "bus",
  "cinema", "movie", "series", "concert", "event", "stock", "interest",
  "news", "weather", "price", "today", "current", "latest", "score",
];

function shouldSearch(message: string): boolean {
  const lower = message.toLowerCase();
  return WEB_KEYWORDS.some((kw) => lower.includes(kw));
}

export default function ChatPage() {
  const { conversationId } = useParams();
  const navigate = useNavigate();

  const currentConversation = useAppStore((s) => s.currentConversation);
  const isLoadingConversation = useAppStore((s) => s.isLoadingConversation);
  const conversationError = useAppStore((s) => s.conversationError);
  const isSending = useAppStore((s) => s.isSending);
  const isAnalyzingImage = useAppStore((s) => s.isAnalyzingImage);
  const sendError = useAppStore((s) => s.sendError);
  const clearSendError = useAppStore((s) => s.clearSendError);
  const fetchConversation = useAppStore((s) => s.fetchConversation);
  const sendMessage = useAppStore((s) => s.sendMessage);
  const clearCurrentConversation = useAppStore((s) => s.clearCurrentConversation);

  const scrollRef = useRef<HTMLDivElement>(null);

  const [showThinking, setShowThinking] = useState(false);
  const [isWebSearching, setIsWebSearching] = useState(false);

  useEffect(() => {
    if (!isSending) {
      setShowThinking(false);
      setIsWebSearching(false);
      return;
    }
    const timer = setTimeout(() => setShowThinking(true), 3000);
    return () => clearTimeout(timer);
  }, [isSending]);

  useEffect(() => {
    if (!conversationId) {
      clearCurrentConversation();
    }
  }, [conversationId, clearCurrentConversation]);

  useEffect(() => {
    if (!conversationId) return;
    if (currentConversation?.id === conversationId) return;
    fetchConversation(conversationId);
  }, [conversationId, currentConversation?.id, fetchConversation]);

  const scrollToBottom = useCallback((smooth: boolean) => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: smooth ? "smooth" : "auto",
    });
  }, []);

  useEffect(() => {
    scrollToBottom(true);
  }, [currentConversation?.messages.length, isSending, scrollToBottom]);

  useEffect(() => {
    if (!sendError) return;
    const timer = setTimeout(() => clearSendError(), 5000);
    return () => clearTimeout(timer);
  }, [sendError, clearSendError]);

  const handleSend = async (message: string, image?: { base64: string; mimeType: string }) => {
    if (!message && !image) return;

    if (!image && shouldSearch(message)) {
      setIsWebSearching(true);
    }

    try {
      const newId = await sendMessage({
        message,
        conversationId: conversationId ?? null,
        imageBase64: image?.base64 ?? null,
        imageMimeType: image?.mimeType ?? null,
      });
      if (!conversationId && newId) {
        navigate(`/chat/${newId}`, { replace: true });
      }
    } catch {
      // Already surfaced via the `sendError` banner
    }
  };

  const showEmptyState = !conversationId && !currentConversation?.messages.length;

  return (
    <div className="flex h-screen bg-bg-main">
      <Sidebar />

      <div className="relative flex min-w-0 flex-1 flex-col">
        <div className="pointer-events-none absolute inset-x-0 top-4 z-50 flex justify-center px-4">
          <AnimatePresence>
            {sendError && (
              <motion.div
                initial={{ opacity: 0, y: -24 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -24 }}
                transition={{ duration: 0.25, ease: "easeOut" }}
                className="pointer-events-auto flex w-full max-w-md items-start gap-2 rounded-xl border border-danger/30 bg-bg-card px-4 py-3 text-sm text-danger shadow-lg shadow-black/20"
              >
                <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
                <span className="flex-1">{sendError}</span>
                <button
                  onClick={clearSendError}
                  aria-label="Close"
                  className="shrink-0 rounded-lg p-0.5 text-danger/70 hover:text-danger"
                >
                  <X className="h-4 w-4" />
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <header className="flex items-center gap-2 border-b border-border px-4 py-3">
          <SidebarToggleButton />
          <div className="flex items-center gap-2">
            <img src="/logo.jpeg" alt="Nova AI" className="h-6 w-6 rounded-md object-cover" />
            <span className="font-semibold text-text-heading">Nova AI</span>
          </div>
        </header>

        <div ref={scrollRef} className="flex-1 overflow-y-auto">
          {showEmptyState ? (
            <div className="mx-auto flex h-full max-w-2xl flex-col items-center justify-center px-6 text-center">
              <img src="/logo.jpeg" alt="Nova AI logo" className="mb-4 h-16 w-16 rounded-2xl object-cover shadow-lg shadow-accent/20" />
              <h1 className="text-2xl font-bold text-text-heading">Welcome to Nova AI</h1>
              <p className="mt-2 text-sm text-text-secondary">
                Chat with Nova, ask questions, and explore more.
              </p>

              <div className="mt-8 grid w-full grid-cols-1 gap-3 sm:grid-cols-2">
                {SUGGESTIONS.map(({ icon: Icon, text }) => (
                  <button
                    key={text}
                    onClick={() => handleSend(text)}
                    className="flex items-start gap-3 rounded-xl border border-border bg-bg-card p-4 text-left text-sm text-text-body transition hover:border-accent/50 hover:bg-hover"
                  >
                    <Icon className="mt-0.5 h-4 w-4 shrink-0 text-accent-light" />
                    {text}
                  </button>
                ))}
              </div>
            </div>
          ) : isLoadingConversation ? (
            <div className="flex h-full items-center justify-center">
              <div className="h-8 w-8 animate-spin rounded-full border-2 border-accent border-t-transparent" />
            </div>
          ) : conversationError && !currentConversation ? (
            <div className="flex h-full flex-col items-center justify-center gap-3 px-6 text-center">
              <p className="max-w-sm text-sm text-text-secondary">{conversationError}</p>
              <button
                onClick={() => conversationId && fetchConversation(conversationId)}
                className="flex items-center gap-2 rounded-xl border border-accent/40 bg-accent/10 px-4 py-2 text-sm font-medium text-accent-light transition hover:bg-accent/20"
              >
                <RefreshCw className="h-4 w-4" />
                Retry
              </button>
            </div>
          ) : (
            <div className="mx-auto max-w-3xl space-y-5 px-4 py-6">
              {currentConversation?.messages.map((m) => (
                <ChatMessage key={m.id} message={m} onStreamTick={() => scrollToBottom(false)} />
              ))}

              {isSending && (
                <div className="flex items-start gap-3">
                  <img
                    src="/logo.jpeg"
                    alt="Nova AI"
                    className="mt-0.5 h-8 w-8 shrink-0 rounded-full object-cover shadow-md"
                  />
                  <AnimatePresence mode="wait">
                    {isAnalyzingImage ? (
                      <motion.div key="image"
                        initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -6 }}
                        transition={{ duration: 0.25, ease: "easeOut" }}>
                        <ImageAnalyzingIndicator />
                      </motion.div>
                    ) : isWebSearching ? (
                      <motion.div key="web"
                        initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -6 }}
                        transition={{ duration: 0.25, ease: "easeOut" }}>
                        <WebSearchIndicator />
                      </motion.div>
                    ) : showThinking ? (
                      <motion.div key="thinking"
                        initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -6 }}
                        transition={{ duration: 0.25, ease: "easeOut" }}>
                        <ThinkingIndicator />
                      </motion.div>
                    ) : (
                      <motion.div key="typing"
                        initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -6 }}
                        transition={{ duration: 0.25, ease: "easeOut" }}>
                        <div className="rounded-2xl rounded-tl-sm bg-bg-aiMessage px-4 py-3">
                          <TypingIndicator />
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              )}
            </div>
          )}
        </div>

        <div className="border-t border-border bg-bg-main px-4 py-3">
          <div className="mx-auto max-w-3xl">
            <ChatInput onSend={handleSend} isSending={isSending} />
            <p className="mt-2 text-center text-xs text-text-secondary">
              Nova can make mistakes. We recommend verifying important information.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
