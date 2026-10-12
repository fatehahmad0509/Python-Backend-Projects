import { ChangeEvent, FormEvent, KeyboardEvent, useRef, useState } from "react";
import { ImageIcon, Send, Sparkles, X, Loader2 } from "lucide-react";

interface ChatInputProps {
  onSend: (message: string, image?: { base64: string; mimeType: string }) => void;
  isSending: boolean;
}

const MAX_IMAGE_MB = 5;

export default function ChatInput({ onSend, isSending }: ChatInputProps) {
  const [text, setText] = useState("");
  const [imagePreview, setImagePreview] = useState<{ base64: string; mimeType: string; name: string } | null>(
    null
  );
  const [imageError, setImageError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;

    if (!file.type.startsWith("image/")) {
      setImageError("Please select an image file.");
      return;
    }
    if (file.size > MAX_IMAGE_MB * 1024 * 1024) {
      setImageError(`Image can be at most ${MAX_IMAGE_MB} MB.`);
      return;
    }

    setImageError(null);
    const reader = new FileReader();
    reader.onload = () => {
      const result = reader.result as string;
      const base64 = result.split(",")[1];
      setImagePreview({ base64, mimeType: file.type, name: file.name });
    };
    reader.readAsDataURL(file);
  };

  const resetTextareaHeight = () => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleSubmit = (e?: FormEvent) => {
    e?.preventDefault();
    const trimmed = text.trim();
    if (!trimmed && !imagePreview) return;
    if (isSending) return;

    onSend(trimmed, imagePreview ? { base64: imagePreview.base64, mimeType: imagePreview.mimeType } : undefined);
    setText("");
    setImagePreview(null);
    resetTextareaHeight();
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <form onSubmit={handleSubmit} className="w-full">
      {imageError && <p className="mb-2 text-xs text-danger">{imageError}</p>}

      {imagePreview && (
        <div className="mb-2 flex items-center gap-3 rounded-xl border border-accent/40 bg-bg-card p-2">
          <img
            src={`data:${imagePreview.mimeType};base64,${imagePreview.base64}`}
            alt="Image preview to be uploaded"
            className="h-12 w-12 rounded-lg object-cover"
          />
          <div className="flex flex-1 items-center gap-1.5 text-xs text-accent-light">
            <Sparkles className="h-3.5 w-3.5" />
            Image Analysis Active
          </div>
          <button
            type="button"
            onClick={() => setImagePreview(null)}
            aria-label="Remove image"
            className="rounded-full p-1 text-text-secondary hover:bg-hover hover:text-text-body"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      <div className="flex items-end gap-2 rounded-2xl border border-border bg-bg-card px-2 py-2 focus-within:border-accent">
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={handleFileChange}
          className="hidden"
          aria-hidden="true"
          tabIndex={-1}
        />
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          aria-label="Upload image"
          className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl text-text-secondary hover:bg-hover hover:text-accent-light"
        >
          <ImageIcon className="h-5 w-5" />
        </button>

        <textarea
          ref={textareaRef}
          value={text}
          onChange={(e) => {
            setText(e.target.value);
            e.target.style.height = "auto";
            e.target.style.height = `${Math.min(e.target.scrollHeight, 160)}px`;
          }}
          onKeyDown={handleKeyDown}
          rows={1}
          placeholder="Write a message to Nova..."
          aria-label="Message input"
          className="max-h-40 flex-1 resize-none bg-transparent py-1.5 text-sm text-text-body placeholder:text-text-secondary focus:outline-none"
        />

        <button
          type="submit"
          disabled={isSending || (!text.trim() && !imagePreview)}
          aria-label="Send"
          className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-user-gradient text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
        >
          {isSending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
        </button>
      </div>
    </form>
  );
}
