// TypeScript type definitions matching the backend API schemas
export type Language = {
  id: string;
  code: string;
  name: string;
  native_name: string;
  flag_emoji: string;
  is_active: boolean;
  order_index: number;
};

export type User = {
  id: string;
  email: string;
  username: string;
  full_name?: string | null;
  avatar_url?: string | null;
  bio?: string | null;
  is_admin: boolean;
  active_language_code?: string | null;
  native_language_code: string;
  level_code: string;
  xp_total: number;
  hearts: number;
  max_hearts: number;
  gems: number;
  streak_days: number;
  longest_streak: number;
  daily_goal_xp: number;
  daily_xp_earned: number;
  league_tier: string;
  league_xp_week: number;
  created_at: string;
};

export type Lesson = {
  id: string;
  order_index: number;
  title: string;
  description?: string | null;
  xp_reward: number;
  icon: string;
  is_ai_dynamic: boolean;
  topic?: string | null;
  completed: boolean;
  best_accuracy: number;
};

export type Section = {
  id: string;
  order_index: number;
  title: string;
  description?: string | null;
  lessons: Lesson[];
};

export type Unit = {
  id: string;
  order_index: number;
  title: string;
  description?: string | null;
  color: string;
  icon: string;
  cefr_level: string;
  sections: Section[];
};

export type QuestionType =
  | "multiple_choice"
  | "translation"
  | "word_match";

export type Question = {
  id: string;
  order_index: number;
  type: QuestionType;
  prompt: string;
  prompt_translation?: string | null;
  data: any;
  explanation?: string | null;
  correct_answer?: string;
};

export type Achievement = {
  id: string;
  code: string;
  title: string;
  description: string;
  icon: string;
  color: string;
  condition_type: string;
  condition_value: number;
  xp_reward: number;
  unlocked: boolean;
  unlocked_at?: string | null;
};

export type DailyQuest = {
  id: string;
  quest_type: string;
  title: string;
  target: number;
  progress: number;
  completed: boolean;
  xp_reward: number;
  icon: string;
};

export type UserStats = {
  xp_total: number;
  streak_days: number;
  longest_streak: number;
  lessons_completed: number;
  words_learned: number;
  accuracy: number;
  total_answers: number;
  correct_answers: number;
  daily_xp: { date: string; xp: number }[];
  level_code: string;
  league_tier: string;
  league_xp_week: number;
};

export type LeaderboardEntry = {
  user_id: string;
  username: string;
  avatar_url?: string | null;
  xp_week: number;
  streak_days: number;
  rank: number;
};

export type Leaderboard = {
  tier: string;
  week_start: string;
  entries: LeaderboardEntry[];
  my_rank?: number | null;
};

export type ChatMessage = { id: string; role: "user" | "assistant"; content: string; created_at: string };
