// Question renderer - displays multiple choice, translation, and word match questions
import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import type { Question } from "@/types";

type Props = {
  question: Question;
  onAnswer: (answer: string) => void;
  disabled: boolean;
  languageCode: string;
};

// Normalize strings for comparison by removing punctuation and extra whitespace
function normalize(s: string): string {
  return s.trim().toLowerCase().replace(/[^\p{L}\p{N}\s]/gu, "").replace(/\s+/g, " ");
}

// Client-side answer checker for simple question types
export function checkAnswerLocal(q: Question, user: string, correct?: string): boolean {
  const target = (correct ?? (q as any).correct_answer ?? "").toString();
  if (!target) return false;
  if (q.type === "word_match") return user === "matched";
  return normalize(target) === normalize(user);
}

export default function QuestionRenderer({ question, onAnswer, disabled }: Props) {
  const [selected, setSelected] = useState<string | null>(null);
  const [matched, setMatched] = useState<Record<string, string>>({});
  const [pickedA, setPickedA] = useState<string | null>(null);
  const [pickedB, setPickedB] = useState<string | null>(null);
  const [typed, setTyped] = useState("");

  // Reset state when the question changes
  useEffect(() => {
    setSelected(null); setMatched({}); setPickedA(null); setPickedB(null); setTyped("");
  }, [question.id, question.type]);

  const submit = (value: string) => onAnswer(value);

  // Shuffle the right-side options for word match
  const bItems = useMemo(() => {
    if (question.type !== "word_match") return [] as string[];
    const arr = (question.data?.pairs || []).map((p: any) => p.b);
    return [...arr].sort(() => Math.random() - 0.5);
  }, [question.id]);

  // Word match logic: pair items from left and right columns
  useEffect(() => {
    if (question.type !== "word_match") return;
    if (pickedA && pickedB) {
      setMatched((m) => ({ ...m, [pickedA]: pickedB }));
      setPickedA(null); setPickedB(null);
      const totalPairs = (question.data?.pairs || []).length;
      if (Object.keys({ ...matched, [pickedA]: pickedB }).length >= totalPairs) {
        const allCorrect = (question.data?.pairs || []).every((p: any) => ({ ...matched, [pickedA]: pickedB })[p.a] === p.b);
        submit(allCorrect ? "matched" : "wrong");
      }
    }
  }, [pickedA, pickedB]);

  return (
    <div className="space-y-6">
      {/* Question header with type label and prompt */}
      <div className="text-center">
        <div className="text-xs font-heading font-bold uppercase tracking-widest text-primary mb-2">
          {typeLabel(question.type)}
        </div>
        <h2 className="font-heading text-2xl sm:text-3xl font-black" data-testid="question-prompt">
          {question.prompt}
        </h2>
        {question.prompt_translation && question.type !== "translation" && (
          <div className="text-sm text-muted-foreground mt-1">{question.prompt_translation}</div>
        )}
      </div>

      {/* Multiple choice: grid of options */}
      {question.type === "multiple_choice" && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3" data-testid="options-grid">
          {(question.data?.options || []).map((opt: string, i: number) => (
            <motion.button
              key={i}
              whileTap={{ scale: 0.97 }}
              disabled={disabled}
              onClick={() => { setSelected(opt); submit(opt); }}
              data-testid={`option-${i}`}
              className={`btn-outline text-left justify-start ${selected === opt ? "border-primary bg-primary/10" : ""}`}
            >
              <span className="w-8 h-8 rounded-lg bg-muted flex items-center justify-center text-sm font-heading font-bold mr-2">{i + 1}</span>
              {opt}
            </motion.button>
          ))}
        </div>
      )}

      {/* Translation: free-text input */}
      {question.type === "translation" && (
        <div className="space-y-4">
          <textarea
            data-testid="translation-input"
            value={typed}
            onChange={(e) => setTyped(e.target.value)}
            placeholder="Write your answer here..."
            className="w-full p-4 rounded-2xl bg-muted border-2 border-transparent focus:border-primary outline-none min-h-[120px] font-body"
            disabled={disabled}
          />
          <button disabled={!typed.trim() || disabled} onClick={() => submit(typed)} className="btn-primary w-full" data-testid="translation-submit">Check</button>
        </div>
      )}

      {/* Word match: two-column pairing */}
      {question.type === "word_match" && (
        <div className="grid grid-cols-2 gap-4" data-testid="wm-area">
          <div className="space-y-2">
            {(question.data?.pairs || []).map((p: any, i: number) => {
              const done = !!matched[p.a];
              return (
                <button key={i} disabled={done || disabled} onClick={() => setPickedA(p.a)} className={`w-full btn-outline justify-start ${done ? "opacity-40" : ""} ${pickedA === p.a ? "border-primary bg-primary/10" : ""}`}>
                  {p.a}
                </button>
              );
            })}
          </div>
          <div className="space-y-2">
            {bItems.map((b, i) => {
              const used = Object.values(matched).includes(b);
              return (
                <button key={i} disabled={used || disabled} onClick={() => setPickedB(b)} className={`w-full btn-outline justify-start ${used ? "opacity-40" : ""} ${pickedB === b ? "border-primary bg-primary/10" : ""}`}>
                  {b}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

// Map question type to a display label
function typeLabel(t: string) {
  return ({
    multiple_choice: "Select the correct one",
    translation: "Translate",
    word_match: "Match pairs",
  } as Record<string, string>)[t] || "Question";
}
