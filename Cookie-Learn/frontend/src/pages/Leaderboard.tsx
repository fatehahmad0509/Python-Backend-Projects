// Leaderboard page - shows weekly rankings within the user's league tier
import { useEffect, useState } from "react";
import { api, assetUrl } from "@/lib/api";
import type { Leaderboard as LB } from "@/types";
import { Crown, Flame, Trophy } from "lucide-react";

const TIER_COLORS: Record<string, string> = {
  bronze: "text-amber-600",
  silver: "text-slate-400",
  gold: "text-yellow-500",
  platinum: "text-cyan-400",
  diamond: "text-blue-400",
  master: "text-purple-500",
};

export default function LeaderboardPage() {
  const [lb, setLb] = useState<LB | null>(null);
  useEffect(() => { api.get<LB>("/leaderboard").then(({ data }) => setLb(data)); }, []);
  if (!lb) return <div className="text-muted-foreground">Loading...</div>;
  return (
    <div className="space-y-6">
      {/* League header */}
      <div className="text-center card-surface p-8">
        <Trophy className={`w-14 h-14 mx-auto ${TIER_COLORS[lb.tier] || "text-primary"}`} />
        <div className="text-xs font-heading font-bold uppercase tracking-widest text-muted-foreground mt-2">Your League</div>
        <h1 className="font-heading text-4xl font-black capitalize" data-testid="lb-tier">{lb.tier}</h1>
        <div className="text-sm text-muted-foreground mt-1">Week starting: {lb.week_start}</div>
        {lb.my_rank && <div className="mt-3 inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-primary/10 text-primary font-heading font-bold"><Crown className="w-4 h-4" /> Your Rank: #{lb.my_rank}</div>}
      </div>
      {/* Rankings list */}
      <div className="card-surface divide-y divide-border" data-testid="lb-list">
        {lb.entries.map((e, i) => (
          <div key={e.user_id} className={`flex items-center gap-3 px-4 py-3 ${e.rank <= 3 ? "bg-primary/5" : ""}`}>
            <div className={`w-10 h-10 rounded-full flex items-center justify-center font-heading font-black ${e.rank === 1 ? "bg-yellow-500/20 text-yellow-500" : e.rank === 2 ? "bg-slate-400/20 text-slate-400" : e.rank === 3 ? "bg-amber-600/20 text-amber-600" : "bg-muted"}`}>
              {e.rank}
            </div>
            <div className="w-9 h-9 rounded-full bg-primary/20 border-2 border-primary flex items-center justify-center overflow-hidden">
              {e.avatar_url ? <img src={assetUrl(e.avatar_url)} className="w-full h-full object-cover" alt="" /> : <span className="font-heading font-bold text-primary">{e.username.slice(0,1).toUpperCase()}</span>}
            </div>
            <div className="flex-1">
              <div className="font-heading font-bold">{e.username}</div>
              <div className="text-xs text-muted-foreground flex items-center gap-1"><Flame className="w-3 h-3 text-orange-500" /> {e.streak_days} day</div>
            </div>
            <div className="font-heading font-black text-accent">{e.xp_week} XP</div>
          </div>
        ))}
        {lb.entries.length === 0 && <div className="p-6 text-center text-muted-foreground">No participants yet.</div>}
      </div>
    </div>
  );
}
