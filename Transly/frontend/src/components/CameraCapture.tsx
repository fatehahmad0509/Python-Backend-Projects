"use client";

import { useEffect, useRef, useState } from "react";

export default function CameraCapture({
  onCapture,
  onClose,
}: {
  onCapture: (file: File) => void;
  onClose: () => void;
}) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function startCamera() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: "environment" },
          audio: false,
        });

        if (cancelled) {
          stream.getTracks().forEach((track) => track.stop());
          return;
        }

        streamRef.current = stream;
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
        setReady(true);
      } catch {
        if (!cancelled) {
          setError(
            "Could not access the camera. Make sure you've granted camera permission in your browser settings."
          );
        }
      }
    }

    startCamera();

    return () => {
      cancelled = true;
      streamRef.current?.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    };
  }, []);

  function handleClose() {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    onClose();
  }

  function handleCapture() {
    const video = videoRef.current;
    if (!video || !video.videoWidth || !video.videoHeight) return;

    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    canvas.toBlob(
      (blob) => {
        if (!blob) {
          setError("Could not create the photo. Please try again.");
          return;
        }
        const file = new File([blob], `camera-${Date.now()}.jpg`, { type: "image/jpeg" });
        streamRef.current?.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
        onCapture(file);
      },
      "image/jpeg",
      0.92
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-paper-sunken/80 p-4 backdrop-blur-sm">
      <div className="ticket w-full max-w-lg animate-rise p-5">
        <div className="flex items-center justify-between">
          <h2 className="font-display text-lg font-medium">Take a photo</h2>
          <button
            onClick={handleClose}
            className="text-sm text-ink-muted hover:text-ink"
            aria-label="Close"
          >
            Close
          </button>
        </div>

        <div className="mt-4 overflow-hidden rounded-xl bg-paper-sunken">
          {error ? (
            <div className="flex min-h-[280px] items-center justify-center p-6 text-center">
              <p className="text-sm text-error-soft">{error}</p>
            </div>
          ) : (
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className="max-h-[60vh] w-full object-contain"
            />
          )}
        </div>

        <div className="mt-4 flex justify-end gap-3">
          <button
            onClick={handleClose}
            className="rounded-lg px-4 py-2 text-sm text-ink-muted hover:text-ink"
          >
            Cancel
          </button>
          <button
            onClick={handleCapture}
            disabled={!ready || !!error}
            className="rounded-lg bg-accent px-5 py-2 text-sm font-medium text-on-accent shadow-glow-accent transition-opacity hover:opacity-90 disabled:opacity-40 disabled:shadow-none"
          >
            Capture
          </button>
        </div>
      </div>
    </div>
  );
}
