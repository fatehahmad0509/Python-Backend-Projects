"use client";

import { useRef, useState } from "react";
import { TARGET_LANGUAGES } from "@/lib/types";
import CameraCapture from "./CameraCapture";

export default function UploadCard({
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
  const [cameraOpen, setCameraOpen] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  function pickFile(f: File) {
    setFile(f);
    setPreview(URL.createObjectURL(f));
  }

  function handleCapture(f: File) {
    pickFile(f);
    setCameraOpen(false);
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
          accept="image/jpeg,image/png,image/webp"
          className="hidden"
          onChange={(e) => {
            const picked = e.target.files?.[0];
            if (picked) pickFile(picked);
          }}
        />
        {preview ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={preview}
            alt="Selected photo"
            className="max-h-52 animate-rise rounded-lg object-contain"
          />
        ) : (
          <>
            <p className="font-display text-base">Drop a photo here</p>
            <p className="mt-1 text-sm text-ink-muted">or click to choose one from your computer</p>
          </>
        )}
      </div>

      <div className="mt-3 flex justify-center">
        <button
          type="button"
          onClick={() => setCameraOpen(true)}
          className="rounded-lg border border-line bg-paper-raised px-4 py-1.5 text-sm text-ink-muted transition-colors hover:border-accent hover:text-ink"
        >
          Take a photo
        </button>
      </div>

      {cameraOpen && (
        <CameraCapture onCapture={handleCapture} onClose={() => setCameraOpen(false)} />
      )}

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
