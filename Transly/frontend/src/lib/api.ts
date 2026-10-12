import type {
  PaginatedTranslationHistory,
  StandardResponse,
  TokenPair,
  TranslationResult,
  UserProfile,
  VideoTranslationResult,
} from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

if (!API_URL && typeof window !== "undefined") {
  // Fails loudly in the browser console rather than silently hitting
  // a relative "/undefined/..." URL.
  console.error(
    "NEXT_PUBLIC_API_URL is not set. Copy .env.local.example to .env.local and set it."
  );
}

export class ApiError extends Error {
  code: string;
  status: number;
  details: Record<string, unknown> | null;

  constructor(message: string, code: string, status: number, details: Record<string, unknown> | null) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
    this.details = details;
  }
}

async function parseResponse<T>(res: Response): Promise<T> {
  let body: StandardResponse<T> | null = null;
  try {
    body = await res.json();
  } catch {
    // Non-JSON body (e.g. a gateway error page) - fall through below.
  }

  if (!res.ok || !body || body.success === false) {
    const code = body?.error?.code ?? "UNKNOWN_ERROR";
    const message = body?.message ?? `Request failed with status ${res.status}`;
    throw new ApiError(message, code, res.status, body?.error?.details ?? null);
  }

  return body.data as T;
}

function authHeaders(accessToken?: string): HeadersInit {
  return accessToken ? { Authorization: `Bearer ${accessToken}` } : {};
}

// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------

export async function register(payload: {
  full_name: string;
  username: string;
  email: string;
  password: string;
}): Promise<UserProfile> {
  const res = await fetch(`${API_URL}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return parseResponse<UserProfile>(res);
}

export async function login(payload: { email: string; password: string }): Promise<TokenPair> {
  const res = await fetch(`${API_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return parseResponse<TokenPair>(res);
}

export async function refreshTokens(refresh_token: string): Promise<TokenPair> {
  const res = await fetch(`${API_URL}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token }),
  });
  return parseResponse<TokenPair>(res);
}

// ---------------------------------------------------------------------------
// Users
// ---------------------------------------------------------------------------

export async function getMe(accessToken: string): Promise<UserProfile> {
  const res = await fetch(`${API_URL}/users/me`, {
    headers: { ...authHeaders(accessToken), "Cache-Control": "no-cache" },
    cache: "no-store",
  });
  return parseResponse<UserProfile>(res);
}

// ---------------------------------------------------------------------------
// Translations
// ---------------------------------------------------------------------------

export async function translateImage(
  accessToken: string,
  image: File,
  targetLanguage: string
): Promise<TranslationResult> {
  const formData = new FormData();
  formData.append("image", image);

  const url = new URL(`${API_URL}/translate/image`);
  url.searchParams.set("target_language", targetLanguage);

  const res = await fetch(url.toString(), {
    method: "POST",
    headers: authHeaders(accessToken),
    body: formData,
  });
  return parseResponse<TranslationResult>(res);
}

export async function translateVideo(
  accessToken: string,
  video: File,
  targetLanguage: string
): Promise<VideoTranslationResult> {
  const formData = new FormData();
  formData.append("video", video);

  const url = new URL(`${API_URL}/translate/video`);
  url.searchParams.set("target_language", targetLanguage);

  const res = await fetch(url.toString(), {
    method: "POST",
    headers: authHeaders(accessToken),
    body: formData,
  });
  return parseResponse<VideoTranslationResult>(res);
}

export async function getHistory(
  accessToken: string,
  page: number,
  pageSize: number
): Promise<PaginatedTranslationHistory> {
  const url = new URL(`${API_URL}/translations/history`);
  url.searchParams.set("page", String(page));
  url.searchParams.set("page_size", String(pageSize));

  const res = await fetch(url.toString(), {
    headers: { ...authHeaders(accessToken), "Cache-Control": "no-cache" },
    cache: "no-store",
  });
  return parseResponse<PaginatedTranslationHistory>(res);
}

export async function deleteHistory(accessToken: string): Promise<void> {
  const res = await fetch(`${API_URL}/translations/history`, {
    method: "DELETE",
    headers: authHeaders(accessToken),
  });
  await parseResponse<null>(res);
}
