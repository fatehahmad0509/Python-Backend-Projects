// Axios API client with JWT token handling and interceptors
import axios, { AxiosInstance } from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API_BASE = `${BACKEND_URL}/api`;

const TOKEN_KEY = "cookielearn_token";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}
export function setToken(t: string | null) {
  if (t) localStorage.setItem(TOKEN_KEY, t);
  else localStorage.removeItem(TOKEN_KEY);
}

export const api: AxiosInstance = axios.create({ baseURL: API_BASE });

// Attach JWT token to every outgoing request
api.interceptors.request.use((config) => {
  const t = getToken();
  if (t) config.headers.Authorization = `Bearer ${t}`;
  return config;
});

// Handle 401 responses by clearing the token (except on auth pages)
api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err?.response?.status === 401) {
      const path = window.location.pathname;
      if (!["/", "/login", "/register"].includes(path)) {
        setToken(null);
      }
    }
    return Promise.reject(err);
  }
);

// Build absolute URL for uploaded assets (avatars, etc.)
export function assetUrl(p?: string | null): string | undefined {
  if (!p) return undefined;
  if (p.startsWith("http")) return p;
  return `${BACKEND_URL}${p}`;
}
