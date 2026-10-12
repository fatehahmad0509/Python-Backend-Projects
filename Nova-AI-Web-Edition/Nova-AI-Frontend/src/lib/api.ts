import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";
import type { ApiErrorShape, HTTPValidationError } from "../types/api";

// Base URL of the deployed Nova AI backend. Override with VITE_API_BASE_URL if needed.
export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "";

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { "Content-Type": "application/json" },
});

// --- Token storage helpers (kept outside Zustand to avoid circular imports) ---
const ACCESS_KEY = "nova_access_token";
const REFRESH_KEY = "nova_refresh_token";

export const tokenStorage = {
  getAccess: () => localStorage.getItem(ACCESS_KEY),
  getRefresh: () => localStorage.getItem(REFRESH_KEY),
  set: (access: string, refresh: string) => {
    localStorage.setItem(ACCESS_KEY, access);
    localStorage.setItem(REFRESH_KEY, refresh);
  },
  setAccess: (access: string) => localStorage.setItem(ACCESS_KEY, access),
  clear: () => {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
  },
};

// Attach access token to every request
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = tokenStorage.getAccess();
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Callback the app can register to react to forced logout (e.g. redirect to /login)
let onSessionExpired: (() => void) | null = null;
export const registerSessionExpiredHandler = (cb: () => void) => {
  onSessionExpired = cb;
};

// Callback the app can register to show the "account suspended" screen.
// Triggered on ANY 403 response — we deliberately never clear tokens or force
// a logout here, since a blocked user should stay signed in and just see the
// suspension screen instead (they can log out manually from that screen).
let onAccountSuspended: (() => void) | null = null;
export const registerAccountSuspendedHandler = (cb: () => void) => {
  onAccountSuspended = cb;
};

const AUTH_ENDPOINTS = ["/auth/login", "/auth/register", "/auth/refresh", "/auth/logout"];
const isAuthEndpoint = (url?: string) => Boolean(url && AUTH_ENDPOINTS.some((p) => url.includes(p)));

let refreshPromise: Promise<{ token: string | null; suspended: boolean }> | null = null;

async function refreshAccessToken(): Promise<{ token: string | null; suspended: boolean }> {
  const refresh_token = tokenStorage.getRefresh();
  if (!refresh_token) return { token: null, suspended: false };
  try {
    const { data } = await axios.post(`${API_BASE_URL}/auth/refresh`, {
      refresh_token,
    });
    tokenStorage.setAccess(data.access_token);
    return { token: data.access_token as string, suspended: false };
  } catch (err) {
    // Account got blocked while the access token was expiring — surface the
    // suspension screen instead of silently logging the user out.
    if (axios.isAxiosError(err) && err.response?.status === 403) {
      return { token: null, suspended: true };
    }
    return { token: null, suspended: false };
  }
}

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as (InternalAxiosRequestConfig & { _retry?: boolean }) | undefined;
    const status = error.response?.status;

    // Blocked / suspended account — never force logout, show the dedicated
    // suspension screen instead and leave the session as-is.
    if (status === 403) {
      onAccountSuspended?.();
      return Promise.reject(normalizeError(error));
    }

    // Only attempt a silent token refresh for calls to protected endpoints.
    // A 401 from /auth/login or /auth/register just means bad credentials —
    // it is NOT an expired session and must not trigger the refresh/logout flow.
    if (status === 401 && !isAuthEndpoint(original?.url) && original && !original._retry) {
      original._retry = true;
      if (!refreshPromise) {
        refreshPromise = refreshAccessToken().finally(() => {
          refreshPromise = null;
        });
      }
      const result = await refreshPromise;
      if (result.token) {
        original.headers = original.headers ?? {};
        original.headers.Authorization = `Bearer ${result.token}`;
        return api(original);
      }
      if (result.suspended) {
        onAccountSuspended?.();
      } else {
        tokenStorage.clear();
        onSessionExpired?.();
      }
    }

    return Promise.reject(normalizeError(error));
  }
);

// Normalizes any axios error into a friendly message + field errors for forms.
export function normalizeError(error: unknown): ApiErrorShape {
  if (axios.isAxiosError(error)) {
    const status = error.response?.status;
    const url = error.config?.url;

    if (!error.response) {
      return { status, message: "Network connection failed. Please check your internet connection." };
    }

    if (status === 422) {
      const detail = (error.response.data as HTTPValidationError)?.detail;
      const fieldErrors: Record<string, string> = {};
      detail?.forEach((d) => {
        const field = String(d.loc[d.loc.length - 1]);
        fieldErrors[field] = d.msg;
      });
      return {
        status,
        message: "There is an error in the information you entered. Please check the fields.",
        fieldErrors,
      };
    }

    // Wrong e-mail/password — cover both 401 and 400, since backends vary in
    // which status they use for "invalid credentials".
    if ((status === 401 || status === 400) && url?.includes("/auth/login")) {
      return { status, message: "Invalid email address or password." };
    }

    if (status === 403) {
      return { status, message: "Your account has been suspended." };
    }

    if (status === 401) {
      return { status, message: "Your session has expired. Please log in again." };
    }

    if (status === 429) {
      // The /chat endpoint returns 429 specifically when the user has used up
      // their daily token quota — surface that as a dedicated message instead
      // of the generic "too many requests" one.
      if (url?.includes("/chat") && !url.includes("/chat/conversations")) {
        return {
          status,
          message: "Daily Usage Limit Reached! Please Try Again Tomorrow.",
        };
      }
      return { status, message: "Too many requests sent. Please wait a moment and try again." };
    }

    if (status && status >= 500) {
      return { status, message: "A server error occurred. Please try again later." };
    }

    const data = error.response.data as { message?: string; detail?: string } | undefined;
    return {
      status,
      message: data?.message || data?.detail || "An unexpected error occurred.",
    };
  }

  return { message: "An unexpected error occurred." };
}
