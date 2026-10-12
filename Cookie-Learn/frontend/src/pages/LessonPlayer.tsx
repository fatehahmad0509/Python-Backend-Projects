// Lesson player - walks through questions (static or AI-generated), tracks answers, shows XP result
import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "sonner";
import { X, Heart, Loader2, ArrowRight, Sparkles, RotateCcw, Zap } from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import type { Question } from "@/types";
import QuestionRenderer, { checkAnswerLocal } from "@/components/QuestionRenderer";
import { Progress } from "@/components/ui/progress";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";

type FeedbackState = { correct: boolean; explanation?: string; correctAnswer?: string } | null;

export default function LessonPlayer() {
  const { lessonId } = useParams();
  const nav = useNavigate();
  const { user, setUser } = useAuth();
  const activeLang = user?.active_language_code || "en";

  const [questions, setQuestions] = useState<Question[]>([]);
  const [idx, setIdx] = useState(0);
  const [loading, setLoading] = useState(true);
  const [feedback, setFeedback] = useState<FeedbackState>(null);
  const [answered, setAnswered] = useState(false);
  const [correctCount, setCorrectCount] = useState(0);
  const [heartsLost, setHeartsLost] = useState(0);
  const [startedAt, setStartedAt] = useState<number>(Date.now());
  const [finished, setFinished] = useState<any>(null);
  const [aiExplain, setAiExplain] = useState<string | null>(null);
  const [aiExplainLoading, setAiExplainLoading] = useState(false);
  const [isAiLesson, setIsAiLesson] = useState(false);
  const [topic, setTopic] = useState<string | null>(null);

  // On mount, load questions either from the lesson or generate with AI
  useEffect(() => {
    setLoading(true);
    if (lessonId) {
      api.get(`/languages/${activeLang}/curriculum`).then(({ data }) => {
        let found: any = null;
        for (const u of data) for (const s of u.sections) for (const l of s.lessons) if (l.id === lessonId) found = l;
        if (found?.is_ai_dynamic) {
          setIsAiLesson(true);
          setTopic(found.topic || null);
          return loadAi(found.topic || null);
        }
        return api.get<Question[]>(`/languages/lessons/${lessonId}/questions`).then((r) => setQuestions(r.data));
      }).finally(() => setLoading(false));
    } else {
      setIsAiLesson(true);
      loadAi(null).finally(() => setLoading(false));
    }
    setStartedAt(Date.now());
  }, [lessonId]);

  // Generate quiz questions via AI
  async function loadAi(topicArg: string | null) {
    try {
      const { data } = await api.post("/ai/quiz/generate", {
        language_code: activeLang,
        level_code: user?.level_code || "A1",
        topic: topicArg,
        num_questions: 6,
      });
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
    } catch (e: any) {
      toast.error("AI question generation failed — please try again later.");
    }
  }

  const q = questions[idx];
  const progress = questions.length ? Math.round(((idx + (answered ? 1 : 0)) / questions.length) * 100) : 0;

  // Handle user's answer: check correctness, record it, deduct hearts if wrong
  async function handleAnswer(userAnswer: string) {
    if (answered || !q) return;
    setAnswered(true);
    let isCorrect: boolean;
    let correctAnswer = (q as any).correct_answer;
    let explanation = q.explanation;

    if (isAiLesson) {
      isCorrect = checkAnswerLocal(q, userAnswer, correctAnswer);
    } else {
      try {
        const { data } = await api.post(`/languages/lessons/${lessonId}/check-answer`, { question_id: q.id, user_answer: userAnswer });
        isCorrect = data.is_correct;
        correctAnswer = data.correct_answer;
        explanation = data.explanation;
      } catch {
        isCorrect = checkAnswerLocal(q, userAnswer, correctAnswer);
      }
    }
    setFeedback({ correct: isCorrect, explanation: explanation || undefined, correctAnswer });
    if (isCorrect) setCorrectCount((c) => c + 1);
    else setHeartsLost((h) => h + 1);

    // Submit answer to backend
    try {
      const { data } = await api.post("/progress/answer", {
        question_id: isAiLesson ? null : q.id,
        lesson_id: lessonId || null,
        question_type: q.type,
        prompt: q.prompt,
        user_answer: userAnswer,
        correct_answer: correctAnswer,
        is_correct: isCorrect,
        language_code: activeLang,
        topic: topic,
      });
      if (user && typeof data.hearts === "number") setUser({ ...user, hearts: data.hearts });
    } catch (err: any) {
      if (err?.response?.status === 402 && user) {
        setUser({ ...user, hearts: 0 });
        toast.error("You're out of hearts!");
      }
    }
  }

  // Ask AI to explain the wrong answer
  async function askAI() {
    if (!q || !feedback) return;
    setAiExplainLoading(true);
    setAiExplain(null);
    try {
      const { data } = await api.post("/ai/explain-wrong", {
        language_code: activeLang,
        question_type: q.type,
        prompt: q.prompt,
        correct_answer: feedback.correctAnswer || "",
        user_answer: "See interaction",
      });
      setAiExplain(`${data.explanation}\n\n💡 ${data.correction_hint}\n\nExamples:\n• ${data.examples.join("\n• ")}`);
    } catch {
      setAiExplain("AI couldn't respond right now.");
    } finally {
      setAiExplainLoading(false);
    }
  }

  function next() {
    if (idx + 1 < questions.length) {
      setIdx(idx + 1);
      setAnswered(false);
      setFeedback(null);
      setAiExplain(null);
    } else {
      finishLesson();
    }
  }

  // Complete the lesson: send results to backend, calculate XP
  async function finishLesson() {
    const duration = Math.round((Date.now() - startedAt) / 1000);
    if (!lessonId) {
      setFinished({ xp_earned: correctCount * 2, streak_days: user?.streak_days, correct_count: correctCount, total: questions.length });
      return;
    }
    try {
      const { data } = await api.post("/progress/complete-lesson", {
        lesson_id: lessonId,
        correct_count: correctCount,
        total_count: questions.length,
        hearts_lost: heartsLost,
        duration_seconds: duration,
      });
      setFinished({ ...data, correct_count: correctCount, total: questions.length });
      if (user) setUser({ ...user, xp_total: user.xp_total + data.xp_earned, streak_days: data.streak_days, hearts: data.hearts, daily_xp_earned: data.daily_xp_earned });
      if (data.new_achievements?.length) {
        data.new_achievements.forEach((a: any) => toast.success(`🏆 New achievement: ${a.title}`));
      }
    } catch {
      toast.error("Lesson could not be saved");
    }
  }

  // Loading state
  if (loading || !q) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]" data-testid="lesson-loading">
        <Loader2 className="w-10 h-10 animate-spin text-primary" />
      </div>
    );
  }

  // No hearts state
  if (user && user.hearts <= 0 && !finished) {
    return (
      <div className="max-w-xl mx-auto py-16 text-center space-y-6" data-testid="lesson-no-hearts">
        <div className="text-7xl">💔</div>
        <h1 className="font-heading text-4xl font-black text-destructive">You're out of hearts!</h1>
        <p className="text-muted-foreground">
          You're out of hearts! Hearts regenerate over time, or you can refill them with gems.
        </p>
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <button
            onClick={async () => {
              try {
                const { data } = await api.post("/users/me/refill-hearts");
                setUser(data);
                toast.success("Hearts refilled!");
              } catch (e: any) {
                toast.error(e?.response?.data?.detail || "Not enough gems");
              }
            }}
            className="btn-primary"
            data-testid="btn-refill-hearts"
          >
            <Heart className="w-5 h-5" /> Refill with Gems ({(user.max_hearts) * 10} 💎)
          </button>
          <button onClick={() => nav("/dashboard")} className="btn-outline" data-testid="btn-back-dashboard">
            Back to Dashboard
          </button>
        </div>
        <div className="text-xs text-muted-foreground">
          Currently: <b>{user.gems} 💎 gems</b>
        </div>
      </div>
    );
  }

  // Finished state
  if (finished) {
    const accuracy = questions.length ? Math.round((finished.correct_count / finished.total) * 100) : 0;
    return (
      <div className="max-w-2xl mx-auto py-16 text-center space-y-6" data-testid="lesson-finished">
        <motion.div initial={{ scale: 0.6, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="text-7xl">🎉</motion.div>
        <h1 className="font-heading text-4xl font-black">Great job!</h1>
        <div className="grid grid-cols-3 gap-4">
          <div className="card-surface p-6"><div className="text-xs uppercase tracking-widest text-muted-foreground">XP</div><div className="font-heading text-3xl font-black text-accent">+{finished.xp_earned || 0}</div></div>
          <div className="card-surface p-6"><div className="text-xs uppercase tracking-widest text-muted-foreground">Accuracy</div><div className="font-heading text-3xl font-black text-success">{accuracy}%</div></div>
          <div className="card-surface p-6"><div className="text-xs uppercase tracking-widest text-muted-foreground">Streak</div><div className="font-heading text-3xl font-black text-orange-500">{finished.streak_days || 0}</div></div>
        </div>
        <div className="flex gap-3 justify-center">
          <button onClick={() => nav("/dashboard")} className="btn-primary" data-testid="finished-continue">Continue</button>
          <button onClick={() => { setFinished(null); setIdx(0); setCorrectCount(0); setHeartsLost(0); setAnswered(false); setFeedback(null); if (isAiLesson) loadAi(topic); }} className="btn-outline" data-testid="finished-retry"><RotateCcw className="w-4 h-4" /> Retry</button>
        </div>
      </div>
    );
  }

  // Active question UI
  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Top bar with close, progress bar, hearts */}
      <div className="flex items-center gap-4">
        <button onClick={() => nav("/dashboard")} data-testid="lesson-close" className="p-2 rounded-xl hover:bg-muted"><X className="w-6 h-6" /></button>
        <Progress value={progress} className="h-3 flex-1" data-testid="lesson-progress" />
        <div className="flex items-center gap-1 text-destructive font-heading font-black" data-testid="lesson-hearts">
          <Heart className="w-5 h-5 fill-destructive" />
          <span>{Math.max(0, (user?.hearts ?? 5))}</span>
        </div>
      </div>

      {isAiLesson && (
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 text-primary text-xs font-heading font-bold uppercase tracking-widest" data-testid="ai-badge">
          <Sparkles className="w-3.5 h-3.5" /> AI Practice · Gemini 3.1
        </div>
      )}

      <div className="card-surface p-6 sm:p-10">
        <QuestionRenderer question={q} onAnswer={handleAnswer} disabled={answered} languageCode={activeLang} />
      </div>

      {/* Feedback bar */}
      <AnimatePresence>
        {feedback && (
          <motion.div initial={{ y: 40, opacity: 0 }} animate={{ y: 0, opacity: 1 }} className={`sticky bottom-4 rounded-3xl p-5 border-b-8 ${feedback.correct ? "bg-success/15 border-success" : "bg-destructive/15 border-destructive"}`} data-testid="lesson-feedback">
            <div className="flex items-start justify-between gap-4 flex-wrap">
              <div className="flex-1 min-w-0">
                <div className={`font-heading text-lg font-black ${feedback.correct ? "text-success" : "text-destructive"}`}>
                  {feedback.correct ? "Awesome! Correct answer." : `Correct answer: ${feedback.correctAnswer}`}
                </div>
                {feedback.explanation && <div className="text-sm mt-1 text-muted-foreground">{feedback.explanation}</div>}
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

      {/* AI explanation dialog */}
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
