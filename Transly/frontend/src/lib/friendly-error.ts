import { ApiError } from "./api";
import type { GeminiErrorDetail } from "./types";

const MESSAGES: Record<string, string> = {
  DAILY_LIMIT_EXCEEDED: "You've used up today's translation quota. You can try again tomorrow.",
  INVALID_IMAGE: "This file could not be read. Please try a different photo.",
  IMAGE_TOO_LARGE: "The photo is too large. Please choose a smaller file.",
  UNSUPPORTED_IMAGE_FORMAT: "This file format isn't supported. Use JPEG, PNG, or WEBP.",
  TEXT_NOT_READABLE: "No readable text was found in the image. Try a clearer photo.",
  INVALID_VIDEO: "This video could not be read. Please try a different video.",
  VIDEO_TOO_LARGE: "The video is too large. Please choose a smaller file.",
  VIDEO_TOO_LONG: "The video can't be longer than 60 seconds. Please choose a shorter video.",
  UNSUPPORTED_VIDEO_FORMAT: "This video format isn't supported. Use MP4, MOV, or WEBM.",
  NOTHING_DETECTED_IN_VIDEO:
    "No speech or readable text was found in the video. Please try a different video.",
  GEMINI_SERVICE_ERROR: "The translation service is unreachable right now. Please try again shortly.",
  RATE_LIMIT_EXCEEDED: "You're sending requests too fast. Please try again shortly.",
  INVALID_CREDENTIALS: "Incorrect email or password.",
  EMAIL_ALREADY_EXISTS: "This email is already registered.",
  USERNAME_ALREADY_EXISTS: "This username is already taken.",
  USER_BLOCKED: "This account has been blocked. Please contact support.",
};

export function friendlyError(err: unknown): string {
  if (err instanceof ApiError) {
    return MESSAGES[err.code] ?? err.message ?? "Something unexpected went wrong. Please try again.";
  }
  if (err instanceof TypeError) {
    // fetch() throws a TypeError for things like being offline, DNS/CORS issues, etc.
    return "Could not connect to the server. Check your internet connection and try again.";
  }
  if (err instanceof Error && err.message) {
    return err.message;
  }
  return "Something unexpected went wrong. Please try again.";
}

// The backend can return HTTP 200 (the request itself succeeded) while the
// translation attempt failed at the Gemini level - e.g. the photo had no
// readable text, or the video had no speech/on-screen text. This maps that
// inner failure to the same plain-language messages instead of leaving the
// user with no explanation.
export function friendlyGeminiError(
  err: GeminiErrorDetail | null,
  mediaKind: "image" | "video" = "image"
): string {
  if (!err) {
    return mediaKind === "video"
      ? "Translation failed. Please try a different video."
      : "Translation failed. Please try a different photo.";
  }
  return MESSAGES[err.code] ?? err.message;
}
