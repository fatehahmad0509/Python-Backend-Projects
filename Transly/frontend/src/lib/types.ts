// Mirrors the FastAPI backend's response schemas. Keep in sync with
// app/schemas/* in the Transly backend repo.

export type Plan = "FREE" | "PLUS" | "DEVELOPER";

// Mirrors the backend's MAX_VIDEO_DURATION_SECONDS / MAX_VIDEO_UPLOAD_SIZE_MB
// defaults, used only for an early, friendly client-side check before
// upload - the backend re-validates both regardless.
export const MAX_VIDEO_DURATION_SECONDS = 60;
export const MAX_VIDEO_UPLOAD_SIZE_MB = 19;

export interface StandardResponse<T> {
  success: boolean;
  message: string;
  data: T | null;
  error?: {
    code: string;
    details: Record<string, unknown> | null;
  };
}

export interface UserProfile {
  id: string;
  full_name: string;
  username: string;
  email: string;
  plan: Plan;
  is_blocked: boolean;
  created_at: string;
  daily_limit: number | null;
  translations_used_today: number;
  translations_remaining_today: number | null;
  video_daily_limit: number | null;
  videos_used_today: number;
  videos_remaining_today: number | null;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export type MediaType = "IMAGE" | "VIDEO";

export interface TranslationItem {
  source_language: string;
  original: string;
  translated: string;
}

export type VideoItemType = "speech" | "on_screen_text";

export interface VideoTranslationItem {
  type: VideoItemType;
  source_language: string;
  original: string;
  translated: string;
}

export interface GeminiErrorDetail {
  code: string;
  message: string;
}

export interface TranslationResult {
  success: boolean;
  detected_languages: string[];
  target_language: string;
  translations: TranslationItem[];
  error: GeminiErrorDetail | null;
}

export interface VideoTranslationResult {
  success: boolean;
  detected_languages: string[];
  target_language: string;
  translations: VideoTranslationItem[];
  error: GeminiErrorDetail | null;
}

export interface TranslationHistoryItem {
  id: string;
  media_type: MediaType;
  detected_languages: string[];
  target_language: string;
  response_json: TranslationResult | VideoTranslationResult;
  created_at: string;
}

export interface PaginationMeta {
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
}

export interface PaginatedTranslationHistory {
  items: TranslationHistoryItem[];
  pagination: PaginationMeta;
}

// A curated set of target languages. The backend accepts any free-text
// string (it's forwarded straight into the Gemini prompt), but a fixed
// list here means every user gets the exact same, known-good string
// instead of relying on the model to interpret arbitrary spelling.
export const TARGET_LANGUAGES = [
  { code: "tr", label: "Türkçe", value: "Turkish" },
  { code: "en", label: "English", value: "English" },
  { code: "az", label: "Azərbaycan dili", value: "Azerbaijani" },
  { code: "de", label: "Deutsch", value: "German" },
  { code: "fr", label: "Français", value: "French" },
  { code: "es", label: "Español", value: "Spanish" },
  { code: "ar", label: "العربية", value: "Arabic" },
  { code: "ru", label: "Русский", value: "Russian" },
  { code: "ja", label: "日本語", value: "Japanese" },
  { code: "zh", label: "中文", value: "Chinese" },
  { code: "it", label: "Italiano", value: "Italian" },
  { code: "pt", label: "Português", value: "Portuguese" },
  { code: "nl", label: "Nederlands", value: "Dutch" },
  { code: "ko", label: "한국어", value: "Korean" },
  { code: "hi", label: "हिन्दी", value: "Hindi" },
  { code: "bn", label: "বাংলা", value: "Bengali" },
  { code: "ur", label: "اردو", value: "Urdu" },
  { code: "fa", label: "فارسی", value: "Persian" },
  { code: "uk", label: "Українська", value: "Ukrainian" },
  { code: "pl", label: "Polski", value: "Polish" },
  { code: "ro", label: "Română", value: "Romanian" },
  { code: "el", label: "Ελληνικά", value: "Greek" },
  { code: "he", label: "עברית", value: "Hebrew" },
  { code: "sv", label: "Svenska", value: "Swedish" },
  { code: "da", label: "Dansk", value: "Danish" },
  { code: "fi", label: "Suomi", value: "Finnish" },
  { code: "no", label: "Norsk", value: "Norwegian" },
  { code: "cs", label: "Čeština", value: "Czech" },
  { code: "id", label: "Bahasa Indonesia", value: "Indonesian" },
  { code: "th", label: "ไทย", value: "Thai" },
  { code: "kk", label: "Қазақша", value: "Kazakh" },
  { code: "uz", label: "Oʻzbek", value: "Uzbek" },
  { code: "tk", label: "Türkmen", value: "Turkmen" },
  { code: "ky", label: "Кыргызча", value: "Kyrgyz" },
  { code: "vi", label: "Tiếng Việt", value: "Vietnamese" },
  { code: "ms", label: "Bahasa Melayu", value: "Malay" },
  { code: "tl", label: "Filipino", value: "Filipino" },
  { code: "sw", label: "Kiswahili", value: "Swahili" },
  { code: "ca", label: "Català", value: "Catalan" },
  { code: "eu", label: "Euskara", value: "Basque" },
  { code: "gl", label: "Galego", value: "Galician" },
  { code: "sr", label: "Српски", value: "Serbian" },
  { code: "hr", label: "Hrvatski", value: "Croatian" },
  { code: "bs", label: "Bosanski", value: "Bosnian" },
  { code: "sk", label: "Slovenčina", value: "Slovak" },
  { code: "sl", label: "Slovenščina", value: "Slovenian" },
  { code: "lt", label: "Lietuvių", value: "Lithuanian" },
  { code: "lv", label: "Latviešu", value: "Latvian" },
  { code: "et", label: "Eesti", value: "Estonian" },
  { code: "bg", label: "Български", value: "Bulgarian" },
  { code: "mk", label: "Македонски", value: "Macedonian" },
  { code: "sq", label: "Shqip", value: "Albanian" },
  { code: "hy", label: "Հայերեն", value: "Armenian" },
  { code: "ka", label: "ქართული", value: "Georgian" },
  { code: "ne", label: "नेपाली", value: "Nepali" },
  { code: "si", label: "සිංහල", value: "Sinhala" },
  { code: "ta", label: "தமிழ்", value: "Tamil" },
  { code: "te", label: "తెలుగు", value: "Telugu" },
  { code: "ml", label: "മലയാളം", value: "Malayalam" },
  { code: "kn", label: "ಕನ್ನಡ", value: "Kannada" },
  { code: "mn", label: "Монгол", value: "Mongolian" },
  { code: "be", label: "Беларуская", value: "Belarusian" },
  { code: "ga", label: "Gaeilge", value: "Irish" },
  { code: "af", label: "Afrikaans", value: "Afrikaans" },
  { code: "tt", label: "Татар", value: "Tatar" }
] as const;
