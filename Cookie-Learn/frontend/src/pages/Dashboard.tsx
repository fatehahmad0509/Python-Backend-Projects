// Dashboard page - daily goal, test launcher, daily quests, league info, XP overview
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { api } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import type { Language, DailyQuest } from "@/types";
import { Check, Flame, PlayCircle, Sparkles, Target, Trophy, Zap } from "lucide-react";
import { Progress } from "@/components/ui/progress";

const DIFFICULTIES = [
  { key: "easy", label: "Easy", sub: "A1 · Beginner", color: "success", emoji: "🌱" },
  { key: "medium", label: "Medium", sub: "B1 · Conversational", color: "accent", emoji: "🔥" },
  { key: "hard", label: "Hard", sub: "C1 · Advanced", color: "destructive", emoji: "⚡" },
];

export default function Dashboard() {
  const { user } = useAuth();
  const nav = useNavigate();
  const [langs, setLangs] = useState<Language[]>([]);
  const [selectedLang, setSelectedLang] = useState<string>(user?.active_language_code || "en");
  const [difficulty, setDifficulty] = useState<string>("easy");
  const [quests, setQuests] = useState<DailyQuest[]>([]);

  useEffect(() => {
    api.get<Language[]>("/languages").then(({ data }) => setLangs(data));
    api.get<DailyQuest[]>("/progress/daily-quests").then(({ data }) => setQuests(data));
  }, []);

  const dailyPct = user ? Math.min(100, Math.round((user.daily_xp_earned / Math.max(1, user.daily_goal_xp)) * 100)) : 0;

  function start() {
    const url = `/test?lang=${selectedLang}&difficulty=${difficulty}`;
    nav(url);
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-8">
      {/* Main content area */}
      <div className="space-y-6">
        {/* Daily goal card */}
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="card-surface p-6" data-testid="dashboard-daily">
          <div className="flex items-center justify-between gap-4 flex-wrap">
            <div>
              <div className="text-xs font-heading font-bold uppercase tracking-widest text-primary mb-1">Today's Goal</div>
              <div className="font-heading text-2xl font-black flex items-center gap-2">
                {Math.min(user?.daily_xp_earned || 0, user?.daily_goal_xp || 30)} / {user?.daily_goal_xp || 30} XP
                {(user?.daily_xp_earned || 0) >= (user?.daily_goal_xp || 30) && (
                  <span className="inline-flex items-center gap-1 text-sm font-heading font-bold text-success">
                    <Check className="w-4 h-4" /> Completed
                  </span>
                )}
              </div>
            </div>
            <div className="flex items-center gap-2 text-orange-500" data-testid="dashboard-streak">
              <Flame className="w-6 h-6 animate-flame" />
              <span className="font-heading font-black text-2xl">{user?.streak_days || 0}</span>
              <span className="text-sm text-muted-foreground">day streak</span>
            </div>
          </div>
          <Progress value={dailyPct} className="mt-4 h-3" data-testid="daily-progress" />
        </motion.div>

        {/* Test launcher card */}
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="card-surface p-6 sm:p-8 space-y-6" data-testid="test-launcher">
          <div>
            <h1 className="font-heading text-3xl sm:text-4xl font-black">Start New Test</h1>
            <p className="text-muted-foreground mt-1">Select a language and difficulty level to start a new assessment test.</p>
          </div>

          <div>
            <div className="text-xs font-heading font-bold uppercase tracking-widest text-muted-foreground mb-3">1. Select Language</div>
            <div className="grid grid-cols-3 sm:grid-cols-5 gap-2" data-testid="lang-picker">
              {langs.map((l) => (
                <button
                  key={l.code}
                  onClick={() => setSelectedLang(l.code)}
                  data-testid={`pick-lang-${l.code}`}
                  className={`p-3 rounded-2xl border-2 flex flex-col items-center gap-1 transition-colors ${
                    selectedLang === l.code ? "border-primary bg-primary/10" : "border-border hover:border-primary/50"
                  }`}
                >
                  <div className="text-2xl">{l.flag_emoji}</div>
                  <div className="text-xs font-heading font-bold">{l.native_name}</div>
                </button>
              ))}
            </div>
          </div>

          <div>
            <div className="text-xs font-heading font-bold uppercase tracking-widest text-muted-foreground mb-3">2. Select Difficulty</div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3" data-testid="difficulty-picker">
              {DIFFICULTIES.map((d) => (
                <button
                  key={d.key}
                  onClick={() => setDifficulty(d.key)}
                  data-testid={`pick-diff-${d.key}`}
                  className={`p-4 rounded-2xl border-2 text-left transition-colors ${
                    difficulty === d.key ? "border-primary bg-primary/10" : "border-border hover:border-primary/50"
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <span className="text-2xl">{d.emoji}</span>
                    <span className="font-heading font-black text-lg">{d.label}</span>
                  </div>
                  <div className="text-xs text-muted-foreground mt-1">{d.sub}</div>
                </button>
              ))}
            </div>
          </div>

          <button onClick={start} className="btn-primary w-full text-lg py-4" data-testid="start-test-btn" disabled={!selectedLang}>
            <PlayCircle className="w-6 h-6" /> Start Test
          </button>
          <div className="text-xs text-muted-foreground text-center">
            Test your knowledge with AI-generated questions. Complete the test to earn XP and track your progress.
          </div>
        </motion.div>
      </div>

      {/* Right sidebar */}
      <aside className="space-y-6">
        {/* Daily quests */}
        <div className="card-surface p-6" data-testid="daily-quests-card">
          <div className="flex items-center gap-2 mb-4">
            <Target className="w-5 h-5 text-primary" />
            <h3 className="font-heading font-black text-lg">Daily Quests</h3>
          </div>
          <div className="space-y-3">
            {quests.map((q) => {
              const pct = Math.min(100, Math.round((q.progress / Math.max(1, q.target)) * 100));
              return (
                <div key={q.id} className="p-3 rounded-2xl border-2 border-border" data-testid={`quest-${q.quest_type}`}>
                  <div className="flex items-center justify-between mb-1">
                    <div className="font-heading font-bold text-sm">{q.title}</div>
                    {q.completed ? <Check className="w-4 h-4 text-success" /> : <span className="text-xs text-muted-foreground">{q.progress}/{q.target}</span>}
                  </div>
                  <Progress value={pct} className="h-2" />
                </div>
              );
            })}
          </div>
        </div>

        {/* League info */}
        <div className="card-surface p-6" data-testid="league-card">
          <div className="flex items-center gap-2 mb-2">
            <Trophy className="w-5 h-5 text-accent" />
            <h3 className="font-heading font-black text-lg">League</h3>
          </div>
          <div className="capitalize font-heading text-2xl font-black text-accent">{user?.league_tier}</div>
          <div className="text-sm text-muted-foreground">Bu hafta {user?.league_xp_week || 0} XP</div>
          <button onClick={() => nav("/leaderboard")} className="btn-outline w-full mt-4 text-sm" data-testid="btn-open-leaderboard">Leaderboard</button>
        </div>

        {/* AI Teacher quick entry */}
        <button onClick={() => nav("/chat")} className="card-surface p-6 flex items-center gap-3 hover:border-primary w-full text-left" data-testid="ai-teacher-quick">
          <div className="w-12 h-12 rounded-2xl bg-primary/15 text-primary flex items-center justify-center text-2xl">🍪</div>
          <div>
            <div className="font-heading font-black">AI Teacher · Cookie</div>
            <div className="text-xs text-muted-foreground">Ask anything on your mind</div>
          </div>
        </button>

        {/* XP card */}
        <div className="card-surface p-6" data-testid="xp-card">
          <div className="flex items-center gap-2 mb-2">
            <Zap className="w-5 h-5 text-accent" />
            <h3 className="font-heading font-black text-lg">Toplam XP</h3>
          </div>
          <div className="text-4xl font-heading font-black text-accent">{user?.xp_total || 0}</div>
          <div className="text-xs text-muted-foreground mt-1">Record streak: {user?.longest_streak || 0} days</div>
        </div>
      </aside>
    </div>
  );
}
