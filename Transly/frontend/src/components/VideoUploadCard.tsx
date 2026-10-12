"use client";

import { useRef, useState } from "react";
import { MAX_VIDEO_DURATION_SECONDS, MAX_VIDEO_UPLOAD_SIZE_MB, TARGET_LANGUAGES } from "@/lib/types";

// Reads video duration client-side via a hidden <video> element so we can
// give an immediate, friendly error before even hitting the network - the
// backend re-validates duration/size/format regardless, this is purely UX.
function readVideoDuration(file: File): Promise<number> {
  return new Promise((resolve, reject) => {
    const video = document.createElement("video");
    video.preload = "metadata";
    video.onloadedmetadata = () => {
      URL.revokeObjectURL(video.src);
      resolve(video.duration);
    };
    video.onerror = () => {
      URL.revokeObjectURL(video.src);
      reject(new Error("could not read duration"));
    };
    video.src = URL.createObjectURL(file);
  });
}

export default function VideoUploadCard({
  submitting,
  onSubmit,
}: {
  submitting: boolean;
  onSubmit: (file: File, targetLanguage: string) => void;
}) {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [targetLanguage, setTargetLanguage] = useState<string>(TARGET_LANGUAGES[0].value);
  const [dragOver, setDragOver] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  async function pickFile(f: File) {
    setLocalError(null);

    const maxBytes = MAX_VIDEO_UPLOAD_SIZE_MB * 1024 * 1024;
    if (f.size > maxBytes) {
      const actualMB = (f.size / (1024 * 1024)).toFixed(1);
      setLocalError(
        `Video is ${actualMB} MB, which exceeds the ${MAX_VIDEO_UPLOAD_SIZE_MB} MB limit.`
      );
      return;
    }

    try {
      const duration = await readVideoDuration(f);
      if (duration > MAX_VIDEO_DURATION_SECONDS) {
        setLocalError(`Video can be at most ${MAX_VIDEO_DURATION_SECONDS} seconds long.`);
        return;
      }
    } catch {
      // If metadata can't be read, don't block here; the backend validates anyway.
    }

    setFile(f);
    setPreview(URL.createObjectURL(f));
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragOver(false);
    const dropped = e.dataTransfer.files?.[0];
    if (dropped) pickFile(dropped);
  }

  return (
    <div className="ticket animate-rise p-5">
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={`flex min-h-[220px] cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed p-6 text-center transition-all duration-200 ${
          dragOver
            ? "border-accent bg-accent-soft shadow-glow-accent"
            : "border-line bg-paper-sunken hover:border-accent/50"
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          accept="video/mp4,video/quicktime,video/webm"
          className="hidden"
          onChange={(e) => {
            const picked = e.target.files?.[0];
            if (picked) pickFile(picked);
          }}
        />
        {preview ? (
          <video src={preview} controls className="max-h-52 animate-rise rounded-lg" />
        ) : (
          <>
            <p className="font-display text-base">Drop a video here</p>
            <p className="mt-1 text-sm text-ink-muted">
              or click to choose one from your computer (max. {MAX_VIDEO_DURATION_SECONDS}s,{" "}
              {MAX_VIDEO_UPLOAD_SIZE_MB} MB)
            </p>
          </>
        )}
      </div>

      {localError && <p className="mt-3 text-center text-sm text-error">{localError}</p>}

      <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <label className="flex items-center gap-2 text-sm text-ink-muted">
          Target language
          <select
            value={targetLanguage}
            onChange={(e) => setTargetLanguage(e.target.value)}
            className="rounded-lg border border-line bg-paper-raised px-2.5 py-1.5 text-sm text-ink outline-none transition-colors focus:border-signal"
          >
            {TARGET_LANGUAGES.map((lang) => (
              <option key={lang.code} value={lang.value}>
                {lang.label}
              </option>
            ))}
          </select>
        </label>

        <button
          disabled={!file || submitting}
          onClick={() => file && onSubmit(file, targetLanguage)}
          className="inline-flex items-center gap-2 rounded-lg bg-accent px-5 py-2 text-sm font-medium text-on-accent shadow-glow-accent transition-all duration-200 hover:opacity-90 disabled:opacity-40 disabled:shadow-none"
        >
          {submitting && (
            <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-on-accent/30 border-t-on-accent" />
          )}
          {submitting ? "Translating…" : "Translate"}
        </button>
      </div>
    </div>
  );
}
