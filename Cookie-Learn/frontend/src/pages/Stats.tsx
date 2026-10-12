// Statistics page - shows user stats cards and a 14-day XP chart
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { UserStats } from "@/types";
import { Award, Book, Flame, Star, Target, Trophy, Zap } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Tooltip, CartesianGrid } from "recharts";

export default function Stats() {
  const [stats, setStats] = useState<UserStats | null>(null);
  useEffect(() => { api.get<UserStats>("/stats/me").then(({ data }) => setStats(data)); }, []);
  if (!stats) return <div className="text-muted-foreground">Loading...</div>;

  const cards = [
    { icon: Zap, label: "Toplam XP", value: stats.xp_total, color: "text-accent" },
    { icon: Flame, label: "Streak", value: `${stats.streak_days} days`, color: "text-orange-500" },
    { icon: Trophy, label: "Longest Streak", value: `${stats.longest_streak} days`, color: "text-primary" },
    { icon: Book, label: "Lessons Completed", value: stats.lessons_completed, color: "text-secondary" },
    { icon: Award, label: "Words Learned", value: stats.words_learned, color: "text-success" },
    { icon: Target, label: "Accuracy", value: `${Math.round(stats.accuracy * 100)}%`, color: "text-primary" },
    { icon: Star, label: "Seviye", value: stats.level_code, color: "text-accent" },
    { icon: Trophy, label: "Lig", value: stats.league_tier, color: "text-primary" },
  ];

  return (
    <div className="space-y-6">
      <h1 className="font-heading text-3xl font-black" data-testid="stats-title">Statistics</h1>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4" data-testid="stats-cards">
        {cards.map((c, i) => (
          <div key={i} className="card-surface p-5">
            <c.icon className={`w-6 h-6 ${c.color}`} />
            <div className="text-xs uppercase tracking-widest text-muted-foreground mt-2">{c.label}</div>
            <div className="font-heading text-2xl font-black capitalize mt-1">{c.value}</div>
          </div>
        ))}
      </div>

      {/* 14-day XP chart */}
      <div className="card-surface p-6" data-testid="stats-chart">
        <h2 className="font-heading text-xl font-black mb-4">Last 14 Days</h2>
        <div className="w-full h-72">
          <ResponsiveContainer>
            <LineChart data={stats.daily_xp.map(p => ({ ...p, dateShort: p.date.slice(5) }))}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis dataKey="dateShort" stroke="hsl(var(--muted-foreground))" fontSize={11} />
              <YAxis stroke="hsl(var(--muted-foreground))" fontSize={11} />
              <Tooltip contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: 12 }} />
              <Line type="monotone" dataKey="xp" stroke="hsl(var(--primary))" strokeWidth={3} dot={{ r: 4, fill: "hsl(var(--primary))" }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
