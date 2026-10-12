import type { TranslationItem, VideoTranslationItem } from "@/lib/types";
import LanguagePill from "./LanguagePill";

const VIDEO_TYPE_LABELS: Record<VideoTranslationItem["type"], string> = {
  speech: "🎙️ Speech",
  on_screen_text: "🔤 On-screen text",
};

export default function TranslationTicket({
  item,
  targetLanguage,
}: {
  item: TranslationItem | VideoTranslationItem;
  targetLanguage: string;
}) {
  const typeLabel = "type" in item ? VIDEO_TYPE_LABELS[item.type] : null;

  return (
    <div className="ticket grid animate-rise grid-cols-1 md:grid-cols-2">
      <div className="p-5">
        {typeLabel && (
          <span className="mb-2 inline-block rounded-full bg-paper-sunken px-2 py-0.5 font-mono text-[11px] text-ink-muted">
            {typeLabel}
          </span>
        )}
        <LanguagePill tone="source">{item.source_language}</LanguagePill>
        <p className="mt-3 whitespace-pre-wrap text-sm leading-relaxed text-ink-muted">
          {item.original}
        </p>
      </div>
      <div className="ticket-seam p-5">
        <span className="scan-light" aria-hidden="true" />
        <LanguagePill tone="target">{targetLanguage}</LanguagePill>
        <p className="mt-3 whitespace-pre-wrap text-sm leading-relaxed text-ink">
          {item.translated}
        </p>
      </div>
    </div>
  );
}
