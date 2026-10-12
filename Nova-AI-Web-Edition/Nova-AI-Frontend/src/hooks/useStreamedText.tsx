import { useEffect, useRef, useState } from "react";

/**
 * No backend streaming; the full text arrives in one go. This hook displays it
 * on screen as if it is being "typed" smoothly, similar to ChatGPT/Gemini.
 *
 * The secret to smoothness:
 *  - Uses requestAnimationFrame instead of setInterval (syncs with frame, no jumping)
 *  - Reveals characters based on elapsed TIME rather than in blocks (consistent speed feel)
 *  - Gently eases out toward the end for a smooth finish
 *  - Even very short messages stream for a minimum duration (no instant "pop-in")
 */
export function useStreamedText(fullText: string, enabled: boolean, onTick?: () => void) {
  const [revealed, setRevealed] = useState<string>(() => (enabled ? "" : fullText));
  const [isStreaming, setIsStreaming] = useState<boolean>(enabled);
  const startedRef = useRef(false);

  useEffect(() => {
    if (!enabled || startedRef.current) return;
    startedRef.current = true;

    const total = fullText.length;
    if (total === 0) {
      setRevealed(fullText);
      setIsStreaming(false);
      return;
    }

    // ~55 chars/sec — a readable, fluid typing speed.
    // Enforce a minimum duration for short messages so they don't finish instantly and jump.
    const CHARS_PER_SEC = 55;
    const minMs = 350;
    const maxMs = 4000;
    const durationMs = Math.min(maxMs, Math.max(minMs, (total / CHARS_PER_SEC) * 1000));

    // Smooth deceleration toward the end (the stream doesn't stop abruptly, it glides to a finish).
    const easeOut = (t: number) => 1 - Math.pow(1 - t, 2.2);

    let startTs: number | null = null;
    let rafId = 0;
    let lastCount = -1;

    const frame = (ts: number) => {
      if (startTs === null) startTs = ts;
      const t = Math.min(1, (ts - startTs) / durationMs);
      const count = Math.floor(easeOut(t) * total);

      if (count !== lastCount) {
        lastCount = count;
        setRevealed(fullText.slice(0, count));
        onTick?.();
      }

      if (t < 1) {
        rafId = requestAnimationFrame(frame);
      } else {
        setRevealed(fullText);
        setIsStreaming(false);
        onTick?.();
      }
    };

    rafId = requestAnimationFrame(frame);
    return () => cancelAnimationFrame(rafId);
    // Animation runs only once on the initial mount.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled]);

  return { revealed, isStreaming };
}
