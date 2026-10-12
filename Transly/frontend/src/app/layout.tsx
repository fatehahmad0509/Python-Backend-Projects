import type { Metadata } from "next";
import { AuthProvider } from "@/lib/auth-context";
import "./globals.css";

export const metadata: Metadata = {
  title: "Transly — translate any photo",
  description: "Snap a photo, get every piece of text in it translated instantly.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-paper font-body text-ink antialiased">
        <div className="ambient-glow" aria-hidden="true" />
        <div className="ambient-grid" aria-hidden="true" />
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
