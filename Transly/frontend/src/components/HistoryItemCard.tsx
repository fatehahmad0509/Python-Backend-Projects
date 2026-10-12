"use client";

import { useState } from "react";
import type { TranslationHistoryItem } from "@/lib/types";
import TranslationTicket from "./TranslationTicket";
import LanguagePill from "./LanguagePill";

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString("en-US", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function HistoryItemCard({ item }: { item: TranslationHistoryItem }) {
  const [expanded, setExpanded] = useState(false);
  const firstItem = item.response_json.translations[0];

  return (
    <div className="ticket animate-rise p-5">
      <button
        onClick={() => setExpanded((v) => !v)}
        className="flex w-full flex-col gap-2 text-left"
      >
        <div className="flex items-start justify-between gap-3">
          <div className="flex min-w-0 flex-1 flex-wrap items-center gap-2">
            <span className="shrink-0 text-base leading-none" title={item.media_type === "VIDEO" ? "Video" : "Photo"}>
              {item.media_type === "VIDEO" ? "🎬" : "🖼️"}
            </span>
            <LanguagePill tone="source">{item.detected_languages.join(", ") || "?"}</LanguagePill>
            <span className="shrink-0 text-ink-muted">→</span>
            <LanguagePill tone="target">{item.target_language}</LanguagePill>
          </div>
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            className={`mt-1.5 h-4 w-4 shrink-0 text-ink-muted transition-transform duration-300 ${
              expanded ? "rotate-180" : ""
            }`}
          >
            <path d="M6 9l6 6 6-6" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
        <div className="flex items-center justify-between gap-3">
          {firstItem ? (
            <span className="min-w-0 flex-1 truncate text-sm text-ink-muted">
              {firstItem.original}
            </span>
          ) : (
            <span />
          )}
          <span className="shrink-0 font-mono text-xs text-ink-muted">
            {formatDate(item.created_at)}
          </span>
        </div>
      </button>

      {expanded && (
        <div className="mt-4 animate-rise space-y-4 border-t border-line pt-4">
          {item.response_json.translations.map((t, i) => (
            <TranslationTicket key={i} item={t} targetLanguage={item.target_language} />
          ))}
        </div>
      )}
    </div>
  );
}
