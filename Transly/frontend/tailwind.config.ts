import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        // Gece uçuş kulesi / boarding pass paleti
        paper: "#090D14",
        "paper-raised": "#121A28",
        "paper-sunken": "#080B11",
        ink: "#E9EEF6",
        "ink-muted": "#8896AA",
        line: "#233047",
        // Amber "beacon" - kalkış / kaynak dil
        accent: "#FFB020",
        "accent-soft": "rgba(255,176,32,0.13)",
        "accent-ink": "#FFCF87",
        "on-accent": "#1A1206",
        // Teal "signal" - varış / hedef dil
        signal: "#2DD4BF",
        "signal-soft": "rgba(45,212,191,0.13)",
        "signal-ink": "#8CF0E3",
        success: "#34D399",
        error: "#FB7185",
        "error-soft": "rgba(251,113,133,0.13)",
      },
      fontFamily: {
        display: ["var(--font-display)", "serif"],
        body: ["var(--font-body)", "sans-serif"],
        mono: ["var(--font-mono)", "monospace"],
      },
      borderRadius: {
        card: "18px",
      },
      boxShadow: {
        panel: "0 1px 0 0 rgba(255,255,255,0.04) inset, 0 20px 40px -24px rgba(0,0,0,0.7)",
        "glow-accent": "0 0 0 1px rgba(255,176,32,0.3), 0 10px 30px -10px rgba(255,176,32,0.45)",
        "glow-signal": "0 0 0 1px rgba(45,212,191,0.3), 0 10px 30px -10px rgba(45,212,191,0.4)",
      },
      keyframes: {
        rise: {
          "0%": { opacity: "0", transform: "translateY(10px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        scan: {
          "0%": { transform: "translateX(-140%)", opacity: "0" },
          "12%": { opacity: "1" },
          "100%": { transform: "translateX(240%)", opacity: "0" },
        },
        beacon: {
          "0%, 100%": { opacity: "1", boxShadow: "0 0 0 0 rgba(255,176,32,0.55)" },
          "50%": { opacity: "0.65", boxShadow: "0 0 0 5px rgba(255,176,32,0)" },
        },
        blob: {
          "0%, 100%": { transform: "translate(0, 0) scale(1)" },
          "50%": { transform: "translate(24px, -30px) scale(1.06)" },
        },
      },
      animation: {
        rise: "rise 0.55s cubic-bezier(0.16,1,0.3,1) both",
        scan: "scan 1.5s cubic-bezier(0.4,0,0.2,1) both",
        beacon: "beacon 2.6s ease-in-out infinite",
        blob: "blob 16s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};

export default config;
