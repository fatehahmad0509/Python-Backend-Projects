import type { UserProfile } from "@/lib/types";

export default function QuotaBadge({
  user,
  kind = "image",
}: {
  user: UserProfile;
  kind?: "image" | "video";
}) {
  const dailyLimit = kind === "video" ? user.video_daily_limit : user.daily_limit;
  const usedToday = kind === "video" ? user.videos_used_today : user.translations_used_today;
  const remainingToday =
    kind === "video" ? user.videos_remaining_today : user.translations_remaining_today;

  if (dailyLimit === null) {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full border border-line bg-paper-raised px-3 py-1 font-mono text-xs text-ink-muted">
        <span className="h-1.5 w-1.5 animate-beacon rounded-full bg-success" />
        unlimited
      </span>
    );
  }

  const remaining = remainingToday ?? 0;
  const isLow = remaining === 0;
  const isTight = !isLow && remaining <= Math.max(1, Math.floor(dailyLimit / 3));

  const dotColor = isLow ? "bg-error" : isTight ? "bg-[#E0A72E]" : "bg-success";
  const label = kind === "video" ? "video" : "translation";

  return (
    <span
      title={`${usedToday}/${dailyLimit} ${label}s used today`}
      className="inline-flex items-center gap-1.5 rounded-full border border-line bg-paper-raised px-3 py-1 font-mono text-xs text-ink"
    >
      <span className={`h-1.5 w-1.5 rounded-full ${dotColor} ${!isLow ? "animate-beacon" : ""}`} />
      {remaining}/{dailyLimit} {kind === "video" ? "video" : ""} left
    </span>
  );
}
