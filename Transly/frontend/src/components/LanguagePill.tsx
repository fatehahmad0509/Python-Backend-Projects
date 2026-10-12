export default function LanguagePill({
  children,
  tone = "source",
}: {
  children: React.ReactNode;
  tone?: "source" | "target";
}) {
  const isTarget = tone === "target";

  return (
    <span
      className={`inline-flex shrink-0 items-center gap-1.5 whitespace-nowrap rounded-full border px-2.5 py-0.5 font-mono text-[11px] uppercase tracking-wide ${
        isTarget
          ? "border-signal/25 bg-signal-soft text-signal-ink"
          : "border-accent/25 bg-accent-soft text-accent-ink"
      }`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${isTarget ? "bg-signal" : "bg-accent"}`} />
      {children}
    </span>
  );
}
