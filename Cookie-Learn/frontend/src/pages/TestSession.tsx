// Test session - AI-generated quiz with evaluation, feedback, XP rewards, and retry option
import { useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "sonner";
import { ArrowRight, Heart, Loader2, RotateCcw, Sparkles, X } from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import type { Question } from "@/types";
import QuestionRenderer from "@/components/QuestionRenderer";
import { Progress } from "@/components/ui/progress";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";

const DIFF_TO_LEVEL: Record<string, string> = { easy: "A1", medium: "B1", hard: "C1" };
const DIFF_LABEL: Record<string, string> = { easy: "Easy", medium: "Medium", hard: "Hard" };

type Feedback = { correct: boolean; feedback: string; correction: string; correct_answer: string } | null;

export default function TestSession() {
  const [params] = useSearchParams();
  const lang = params.get("lang") || "en";
  const difficulty = params.get("difficulty") || "easy";
  const level = DIFF_TO_LEVEL[difficulty] || "A1";
  const nav = useNavigate();
  const { user, setUser } = useAuth();

  const [questions, setQuestions] = useState<Question[]>([]);
  const [idx, setIdx] = useState(0);
  const [loading, setLoading] = useState(true);
  const [answered, setAnswered] = useState(false);
  const [feedback, setFeedback] = useState<Feedback>(null);
  const [correctCount, setCorrectCount] = useState(0);
  const [startedAt] = useState(Date.now());
  const [finished, setFinished] = useState<any>(null);
  const [aiExplain, setAiExplain] = useState<string | null>(null);
  const [aiExplainLoading, setAiExplainLoading] = useState(false);
  const [evaluating, setEvaluating] = useState(false);

  // Generate AI questions on mount
  useEffect(() => {
    setLoading(true);
    api.post("/ai/quiz/generate", {
      language_code: lang,
      level_code: level,
      num_questions: 6,
      types: ["multiple_choice", "translation", "word_match"],
    })
      .then(({ data }) => {
        const qs: Question[] = (data.questions || []).map((q: any, i: number) => ({
          id: `ai-${i}-${Date.now()}`,
          order_index: i,
          type: q.type,
          prompt: q.prompt,
          prompt_translation: q.prompt_translation,
          data: q.data,
          explanation: q.explanation,
          correct_answer: q.correct_answer,
        }));
        setQuestions(qs);
      })
      .catch(() => toast.error("AI couldn't generate questions. Try again."))
      .finally(() => setLoading(false));
  }, []);

  const q = questions[idx];
  const progress = questions.length ? Math.round(((idx + (answered ? 1 : 0)) / questions.length) * 100) : 0;

  // Handle answer: send to backend AI evaluation
  async function handleAnswer(userAnswer: string) {
    if (!q || answered) return;
    setAnswered(true);
    setEvaluating(true);
    try {
      const { data } = await api.post("/practice/evaluate", {
        language_code: lang,
        level_code: level,
        question_type: q.type,
        prompt: q.prompt,
        correct_answer: (q as any).correct_answer,
        user_answer: userAnswer,
        topic: null,
      });
      setFeedback({
        correct: data.is_correct,
        feedback: data.feedback,
        correction: data.correction,
        correct_answer: data.correct_answer,
      });
      if (data.is_correct) setCorrectCount((c) => c + 1);
      if (user && typeof data.hearts === "number") setUser({ ...user, hearts: data.hearts });
    } catch (err: any) {
      if (err?.response?.status === 402 && user) {
        setUser({ ...user, hearts: 0 });
        toast.error("You're out of hearts!");
      } else {
        toast.error("Could not evaluate.");
      }
      setAnswered(false);
    } finally {
      setEvaluating(false);
    }
  }

  function next() {
    if (idx + 1 < questions.length) {
      setIdx(idx + 1);
      setAnswered(false);
      setFeedback(null);
      setAiExplain(null);
    } else {
      finishSession();
    }
  }

  // Complete the test and save results
  async function finishSession() {
    try {
      const duration = Math.round((Date.now() - startedAt) / 1000);
      const { data } = await api.post("/practice/finish", {
        language_code: lang,
        difficulty,
        correct_count: correctCount,
        total_count: questions.length,
        duration_seconds: duration,
      });
      setFinished({ ...data, correct_count: correctCount, total: questions.length });
      if (user) setUser({ ...user, xp_total: user.xp_total + data.xp_earned, streak_days: data.streak_days, hearts: data.hearts, daily_xp_earned: data.daily_xp_earned });
      if (data.new_achievements?.length) data.new_achievements.forEach((a: any) => toast.success(`🏆 New achievement: ${a.title}`));
    } catch {
      toast.error("Result could not be saved");
    }
  }

  // Ask AI for a detailed explanation
  async function askAI() {
    if (!q || !feedback) return;
    setAiExplainLoading(true); setAiExplain(null);
    try {
      const { data } = await api.post("/ai/explain-wrong", {
        language_code: lang,
        question_type: q.type,
        prompt: q.prompt,
        correct_answer: feedback.correct_answer,
        user_answer: "See interaction",
      });
      setAiExplain(`${data.explanation}\n\n💡 ${data.correction_hint}\n\nExamples:\n• ${data.examples.join("\n• ")}`);
    } catch {
      setAiExplain("AI couldn't respond right now.");
    } finally {
      setAiExplainLoading(false);
    }
  }

  // Start a new test with fresh questions
  function restart() {
    setFinished(null); setIdx(0); setCorrectCount(0); setAnswered(false); setFeedback(null); setLoading(true); setQuestions([]);
    api.post("/ai/quiz/generate", {
      language_code: lang, level_code: level, num_questions: 6,
      types: ["multiple_choice", "translation", "word_match"],
    })
      .then(({ data }) => {
        const qs: Question[] = (data.questions || []).map((q: any, i: number) => ({
          id: `ai-${i}-${Date.now()}`, order_index: i, type: q.type, prompt: q.prompt,
          prompt_translation: q.prompt_translation, data: q.data, explanation: q.explanation, correct_answer: q.correct_answer,
        }));
        setQuestions(qs);
      })
      .finally(() => setLoading(false));
  }

  if (user && user.hearts <= 0 && !finished) {
    return (
      <div className="max-w-xl mx-auto py-16 text-center space-y-6" data-testid="test-no-hearts">
        <div className="text-7xl">💔</div>
        <h1 className="font-heading text-4xl font-black text-destructive">You're out of hearts!</h1>
        <p className="text-muted-foreground">You've run out of hearts! Hearts regenerate over time.</p>
        <div className="flex gap-3 justify-center">
          <button onClick={() => nav("/shop")} className="btn-primary" data-testid="go-shop">Go to Shop</button>
          <button onClick={() => nav("/dashboard")} className="btn-outline" data-testid="go-dashboard">Back to Dashboard</button>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="max-w-2xl mx-auto py-20 text-center space-y-4" data-testid="test-loading">
        <div className="relative w-16 h-16 mx-auto">
          <Sparkles className="w-16 h-16 text-primary animate-pulse-soft" />
        </div>
        <h2 className="font-heading text-2xl font-black">Preparing questions...</h2>
        <p className="text-muted-foreground">Gemini 3.1 is creating personalized questions for you...</p>
      </div>
    );
  }

  if (!q && !finished) {
    return (
      <div className="text-center py-20 space-y-4" data-testid="test-error">
        <div className="text-5xl">😔</div>
        <h2 className="font-heading text-2xl font-black">Could not generate question</h2>
        <button onClick={() => nav("/dashboard")} className="btn-primary">Go Back</button>
      </div>
    );
  }

  if (finished) {
    const accuracy = questions.length ? Math.round((finished.correct_count / finished.total) * 100) : 0;
    return (
      <div className="max-w-2xl mx-auto py-16 text-center space-y-6" data-testid="test-finished">
        <motion.div initial={{ scale: 0.6, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="text-7xl">
          {accuracy >= 80 ? "🎉" : accuracy >= 50 ? "👏" : "💪"}
        </motion.div>
        <h1 className="font-heading text-4xl font-black">
          {accuracy >= 80 ? "Great job!" : accuracy >= 50 ? "You're doing well!" : "Try again!"}
        </h1>
        <div className="text-sm text-muted-foreground">
          <b className="capitalize">{DIFF_LABEL[difficulty]}</b> · <b className="uppercase">{lang}</b>
        </div>
        <div className="grid grid-cols-3 gap-4">
          <div className="card-surface p-6"><div className="text-xs uppercase tracking-widest text-muted-foreground">XP</div><div className="font-heading text-3xl font-black text-accent">+{finished.xp_earned || 0}</div></div>
          <div className="card-surface p-6"><div className="text-xs uppercase tracking-widest text-muted-foreground">Accuracy</div><div className="font-heading text-3xl font-black text-success">{accuracy}%</div></div>
          <div className="card-surface p-6"><div className="text-xs uppercase tracking-widest text-muted-foreground">Streak</div><div className="font-heading text-3xl font-black text-orange-500">{finished.streak_days || 0}</div></div>
        </div>
        <div className="flex flex-wrap gap-3 justify-center">
          <button onClick={() => nav("/dashboard")} className="btn-primary" data-testid="finish-back-dashboard">Back to Dashboard</button>
          <button onClick={restart} className="btn-outline" data-testid="finish-restart"><RotateCcw className="w-4 h-4" /> New Test</button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Top bar */}
      <div className="flex items-center gap-4">
        <button onClick={() => nav("/dashboard")} data-testid="test-close" className="p-2 rounded-xl hover:bg-muted"><X className="w-6 h-6" /></button>
        <Progress value={progress} className="h-3 flex-1" data-testid="test-progress" />
        <div className="flex items-center gap-1 text-destructive font-heading font-black" data-testid="test-hearts">
          <Heart className="w-5 h-5 fill-destructive" />
          <span>{Math.max(0, user?.hearts ?? 5)}</span>
        </div>
      </div>

      <div className="flex items-center gap-2 flex-wrap">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 text-primary text-xs font-heading font-bold uppercase tracking-widest">
          <Sparkles className="w-3.5 h-3.5" /> AI Test · {DIFF_LABEL[difficulty]} · {lang.toUpperCase()}
        </div>
        <div className="text-xs text-muted-foreground">Question {idx + 1}/{questions.length}</div>
      </div>

      <div className="card-surface p-6 sm:p-10">
        <QuestionRenderer question={q} onAnswer={handleAnswer} disabled={answered || evaluating} languageCode={lang} />
      </div>

      {evaluating && (
        <div className="text-center text-sm text-muted-foreground flex items-center justify-center gap-2" data-testid="evaluating">
          <Loader2 className="w-4 h-4 animate-spin" /> AI is evaluating your answer...
        </div>
      )}

      <AnimatePresence>
        {feedback && (
          <motion.div initial={{ y: 40, opacity: 0 }} animate={{ y: 0, opacity: 1 }} className={`sticky bottom-4 rounded-3xl p-5 border-b-8 ${feedback.correct ? "bg-success/15 border-success" : "bg-destructive/15 border-destructive"}`} data-testid="test-feedback">
            <div className="flex items-start justify-between gap-4 flex-wrap">
              <div className="flex-1 min-w-0">
                <div className={`font-heading text-lg font-black ${feedback.correct ? "text-success" : "text-destructive"}`}>
                  {feedback.correct ? "Awesome! 🎉" : `Example correct answer: ${feedback.correct_answer}`}
                </div>
                {feedback.feedback && <div className="text-sm mt-1 text-muted-foreground whitespace-pre-wrap">{feedback.feedback}</div>}
                {feedback.correction && !feedback.correct && (
                  <div className="text-sm mt-2"><b>Correction suggestion:</b> {feedback.correction}</div>
                )}
              </div>
              <div className="flex gap-2">
                {!feedback.correct && (
                  <button onClick={askAI} className="btn-outline text-sm" data-testid="btn-ai-explain">
                    {aiExplainLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />} Explain with AI
                  </button>
                )}
                <button onClick={next} className={feedback.correct ? "btn-success" : "btn-danger"} data-testid="btn-continue">
                  Continue <ArrowRight className="w-5 h-5" />
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <Dialog open={!!aiExplain} onOpenChange={() => setAiExplain(null)}>
        <DialogContent data-testid="ai-explain-dialog">
          <DialogHeader>
            <DialogTitle className="font-heading font-black flex items-center gap-2"><Sparkles className="w-5 h-5 text-primary" /> Cookie Explains</DialogTitle>
          </DialogHeader>
          <div className="whitespace-pre-wrap text-sm">{aiExplain}</div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
