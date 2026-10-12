"use client";

import { useState } from "react";
import AuthGuard from "@/components/AuthGuard";
import Navbar from "@/components/Navbar";
import UploadCard from "@/components/UploadCard";
import TranslationTicket from "@/components/TranslationTicket";
import { useAuth } from "@/lib/auth-context";
import * as api from "@/lib/api";
import { friendlyError, friendlyGeminiError } from "@/lib/friendly-error";
import type { TranslationResult } from "@/lib/types";

function TranslatePageContent() {
  const { user, withAuth, refreshProfile } = useAuth();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<TranslationResult | null>(null);

  const quotaExhausted =
    user?.daily_limit !== null &&
    user?.daily_limit !== undefined &&
    (user.translations_remaining_today ?? 0) <= 0;

  async function handleSubmit(file: File, targetLanguage: string) {
    setSubmitting(true);
    setError(null);
    setResult(null);

    try {
      const translated = await withAuth((token) => api.translateImage(token, file, targetLanguage));

      if (translated.success) {
        setResult(translated);
      } else {
        // The request reached the backend successfully, but the translation
        // itself failed at the Gemini level (e.g. no readable text in the image) -
        // show the reason.
        setError(friendlyGeminiError(translated.error));
      }
    } catch (err) {
      setError(friendlyError(err));
      setSubmitting(false);
      return;
    }

    setSubmitting(false);

    // Quota only changes server-side after a successful translation -
    // refetch so the navbar badge reflects the new remaining count.
    // Separate try/catch: even if refreshing the quota badge fails, the
    // translation itself already succeeded, so we shouldn't surface an error.
    try {
      await refreshProfile();
    } catch (err) {
      console.error("Failed to refresh quota info:", err);
    }
  }

  return (
    <main className="mx-auto max-w-4xl px-5 py-8">
      <h1 className="animate-rise font-display text-2xl font-medium">Translate your photo</h1>
      <p className="mt-1 animate-rise text-sm text-ink-muted">
        Upload a photo containing text, then pick your target language.
      </p>

      {quotaExhausted && (
        <p className="mt-4 animate-rise rounded-lg border border-error/25 bg-error-soft px-4 py-3 text-sm text-error">
          You've used up today's translation quota. You can try again tomorrow.
        </p>
      )}

      <div className="mt-6">
        <UploadCard submitting={submitting} onSubmit={handleSubmit} />
      </div>

      {error && (
        <p className="mt-6 animate-rise rounded-lg border border-error/25 bg-error-soft px-4 py-3 text-sm text-error">
          {error}
        </p>
      )}

      {result && (
        <div className="mt-8 space-y-4">
          <div className="flex animate-rise items-center gap-2 text-sm text-ink-muted">
            <span>Detected language:</span>
            <span className="font-mono text-xs uppercase text-ink">
              {result.detected_languages.join(", ") || "—"}
            </span>
          </div>
          {result.translations.map((item, i) => (
            <TranslationTicket key={i} item={item} targetLanguage={result.target_language} />
          ))}
        </div>
      )}
    </main>
  );
}

export default function TranslatePage() {
  return (
    <AuthGuard>
      <Navbar />
      <TranslatePageContent />
    </AuthGuard>
  );
}
