"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import QuotaBadge from "./QuotaBadge";

const NAV_ITEMS = [
  { href: "/translate", label: "Translate" },
  { href: "/translate/video", label: "Translate Video" },
  { href: "/history", label: "History" },
];

export default function Navbar() {
  const { user, logout } = useAuth();
  const pathname = usePathname();
  const router = useRouter();

  return (
    <header className="sticky top-0 z-20 border-b border-line bg-paper-raised/60 backdrop-blur-lg">
      <div className="mx-auto flex max-w-4xl flex-wrap items-center justify-between gap-x-4 gap-y-2 px-5 py-3">
        <div className="flex flex-wrap items-center gap-x-6 gap-y-2">
          <span className="flex items-center gap-2 font-display text-lg font-medium tracking-tight">
            <span className="inline-block h-2 w-2 rounded-full bg-accent shadow-glow-accent animate-beacon" />
            Transly
          </span>
          <nav className="flex flex-wrap items-center gap-1">
            {NAV_ITEMS.map((item) => {
              const active = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`relative rounded-full px-3 py-1.5 text-sm transition-colors duration-200 ${
                    active
                      ? "bg-accent-soft text-accent-ink"
                      : "text-ink-muted hover:bg-paper hover:text-ink"
                  }`}
                >
                  {item.label}
                  {active && (
                    <span className="absolute inset-x-3 -bottom-[5px] h-px bg-gradient-to-r from-transparent via-accent to-transparent" />
                  )}
                </Link>
              );
            })}
          </nav>
        </div>

        <div className="flex items-center gap-3">
          {user && (
            <div className="flex flex-wrap items-center gap-2">
              <QuotaBadge user={user} kind="image" />
              <QuotaBadge user={user} kind="video" />
            </div>
          )}
          <button
            onClick={() => {
              if (!confirm("Are you sure you want to log out?")) return;
              logout();
              router.replace("/login");
            }}
            className="text-sm text-ink-muted transition-colors hover:text-error"
          >
            Log out
          </button>
        </div>
      </div>
    </header>
  );
}
