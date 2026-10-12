"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";

export default function RootPage() {
  const { status } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (status === "authenticated") router.replace("/translate");
    if (status === "unauthenticated") router.replace("/login");
  }, [status, router]);

  return (
    <main className="flex min-h-screen items-center justify-center">
      <p className="flex items-center gap-2 font-mono text-sm text-ink-muted">
        <span className="h-3 w-3 animate-spin rounded-full border-2 border-line border-t-accent" />
        Loading…
      </p>
    </main>
  );
}
