// Achievements page - displays all achievements with unlock status
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Achievement } from "@/types";
import * as Icons from "lucide-react";

export default function AchievementsPage() {
  const [list, setList] = useState<Achievement[]>([]);
  useEffect(() => { api.get<Achievement[]>("/stats/achievements").then(({ data }) => setList(data)); }, []);
  return (
    <div className="space-y-6">
      <h1 className="font-heading text-3xl font-black" data-testid="achievements-title">Achievements</h1>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4" data-testid="achievements-grid">
        {list.map((a) => {
          const Icon = (Icons as any)[a.icon] || Icons.Trophy;
          return (
            <div key={a.id} className={`card-surface p-5 text-center ${a.unlocked ? "" : "opacity-50 grayscale"}`} data-testid={`ach-${a.code}`}>
              <div className="w-14 h-14 mx-auto rounded-2xl flex items-center justify-center mb-3" style={{ background: `${a.color}22`, color: a.color }}>
                <Icon className="w-7 h-7" />
              </div>
              <div className="font-heading font-black">{a.title}</div>
              <div className="text-xs text-muted-foreground mt-1">{a.description}</div>
              <div className="text-xs font-heading font-bold text-accent mt-2">+{a.xp_reward} XP</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
