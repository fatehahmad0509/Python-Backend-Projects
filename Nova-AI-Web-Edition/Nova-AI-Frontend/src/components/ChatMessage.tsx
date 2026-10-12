import { motion } from "framer-motion";
import { Globe } from "lucide-react";
import Markdown from "./Markdown";
import { useStreamedText } from "../hooks/useStreamedText";
import type { MessageRead } from "../types/api";

interface ChatMessageProps {
  message: MessageRead;
  /** Called on each character tick during streaming (for auto-scrolling). */
  onStreamTick?: () => void;
}

export default function ChatMessage({ message, onStreamTick }: ChatMessageProps) {
  const isUser = message.role === "user";

  // Only recently received ('_isNew') assistant messages get the fake stream effect.
  // Messages loaded from history are displayed in full immediately.
  const { revealed, isStreaming } = useStreamedText(
    message.content,
    !isUser && Boolean(message._isNew),
    onStreamTick
  );

  if (isUser) {
    return (
      <motion.div
        initial={{ opacity: 0, x: 16 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.2 }}
        className="flex justify-end"
      >
        <div className="max-w-[80%] space-y-2 sm:max-w-[65%]">
          {message.image_base64 && message.image_mime_type && (
            <img
              src={`data:${message.image_mime_type};base64,${message.image_base64}`}
              alt="Sent image"
              className="ml-auto max-h-64 rounded-2xl border-2 border-accent object-cover"
            />
          )}
          {message.content && (
            <div className="rounded-2xl rounded-tr-sm bg-user-gradient px-4 py-2.5 text-sm text-white shadow-md">
              {message.content}
            </div>
          )}
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="flex items-start gap-3"
    >
      <img
        src="/logo.jpeg"
        alt="Nova AI"
        className="mt-0.5 h-8 w-8 shrink-0 rounded-full object-cover shadow-md"
      />
      <div className="max-w-[85%] rounded-2xl rounded-tl-sm bg-bg-aiMessage px-4 py-3 text-sm text-text-body sm:max-w-[75%]">
        {isStreaming ? (
          <span className="nova-stream whitespace-pre-wrap">
            {revealed.split(/(\s+)/).map((tok, i) =>
              tok.trim() === "" ? (
                <span key={i}>{tok}</span>
              ) : (
                <span key={i} className="nova-word">
                  {tok}
                </span>
              )
            )}
            <span
              aria-hidden="true"
              className="ml-0.5 inline-block h-4 w-[2px] align-middle bg-accent-light animate-pulse"
            />
          </span>
        ) : (
          <Markdown content={message.content} />
        )}
        {!isStreaming && message.sources && message.sources.length > 0 && (
          <div className="mt-3 flex flex-wrap items-center gap-2 border-t border-border pt-2.5">
            <span className="flex items-center gap-1 text-xs text-text-secondary">
              <Globe className="h-3.5 w-3.5" />
              Sources:
            </span>
            {message.sources.map((source, idx) => {
              const url = typeof source.url === "string" ? source.url : undefined;
              const title = typeof source.title === "string" ? source.title : url || `Source ${idx + 1}`;
              return url ? (
                <a
                  key={idx}
                  href={url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="rounded-full border border-border px-2.5 py-0.5 text-xs text-accent-light hover:bg-hover"
                >
                  {title}
                </a>
              ) : (
                <span key={idx} className="rounded-full border border-border px-2.5 py-0.5 text-xs text-text-secondary">
                  {title}
                </span>
              );
            })}
          </div>
        )}
      </div>
    </motion.div>
  );
}
