"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import AuthGuard from "@/components/AuthGuard";
import Navbar from "@/components/Navbar";
import HistoryItemCard from "@/components/HistoryItemCard";
import { useAuth } from "@/lib/auth-context";
import * as api from "@/lib/api";
import { friendlyError } from "@/lib/friendly-error";
import type { PaginatedTranslationHistory } from "@/lib/types";

const PAGE_SIZE = 10;

function HistoryPageContent() {
  const { withAuth } = useAuth();
  const [page, setPage] = useState(1);
  const [data, setData] = useState<PaginatedTranslationHistory | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [clearing, setClearing] = useState(false);

  async function load(targetPage: number) {
    setLoading(true);
    setError(null);
    try {
      const history = await withAuth((token) => api.getHistory(token, targetPage, PAGE_SIZE));
      setData(history);
    } catch (err) {
      setError(friendlyError(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load(page);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page]);

  async function handleClearAll() {
    if (!confirm("Are you sure you want to delete your entire translation history? This cannot be undone.")) return;
    setClearing(true);
    try {
      await withAuth((token) => api.deleteHistory(token));
      setPage(1);
      await load(1);
    } catch (err) {
      setError(friendlyError(err));
    } finally {
      setClearing(false);
    }
  }

  return (
    <main className="mx-auto max-w-4xl px-5 py-8">
      <div className="flex animate-rise items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-medium">History</h1>
          <p className="mt-1 text-sm text-ink-muted">Translations you've made before.</p>
        </div>
        {data && data.items.length > 0 && (
          <button
            onClick={handleClearAll}
            disabled={clearing}
            className="text-sm text-error transition-opacity hover:underline disabled:opacity-50"
          >
            {clearing ? "Deleting…" : "Delete all"}
          </button>
        )}
      </div>

      {error && (
        <p className="mt-6 animate-rise rounded-lg border border-error/25 bg-error-soft px-4 py-3 text-sm text-error">
          {error}
        </p>
      )}

      {loading && (
        <p className="mt-8 flex items-center gap-2 font-mono text-sm text-ink-muted">
          <span className="h-3 w-3 animate-spin rounded-full border-2 border-line border-t-accent" />
          Loading…
        </p>
      )}

      {!loading && data && data.items.length === 0 && (
        <div className="mt-10 animate-rise rounded-xl border border-dashed border-line p-8 text-center">
          <p className="font-display text-lg">No translations yet</p>
          <p className="mt-1 text-sm text-ink-muted">
            Head to the{" "}
            <Link href="/translate" className="text-accent hover:underline">
              Translate
            </Link>{" "}
            tab to translate your first photo.
          </p>
        </div>
      )}

      {!loading && data && data.items.length > 0 && (
        <>
          <div className="mt-6 space-y-4">
            {data.items.map((item) => (
              <HistoryItemCard key={item.id} item={item} />
            ))}
          </div>

          {data.pagination.total_pages > 1 && (
            <div className="mt-6 flex items-center justify-center gap-4">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="text-sm text-ink-muted hover:text-ink disabled:opacity-30"
              >
                ← Previous
              </button>
              <span className="font-mono text-xs text-ink-muted">
                {data.pagination.page} / {data.pagination.total_pages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(data.pagination.total_pages, p + 1))}
                disabled={page >= data.pagination.total_pages}
                className="text-sm text-ink-muted hover:text-ink disabled:opacity-30"
              >
                Next →
              </button>
            </div>
          )}
        </>
      )}
    </main>
  );
}

export default function HistoryPage() {
  return (
    <AuthGuard>
      <Navbar />
      <HistoryPageContent />
    </AuthGuard>
  );
}
