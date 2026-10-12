"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import * as api from "./api";
import { ApiError } from "./api";
import type { UserProfile } from "./types";

const ACCESS_TOKEN_KEY = "transly_access_token";
const REFRESH_TOKEN_KEY = "transly_refresh_token";

type AuthStatus = "loading" | "authenticated" | "unauthenticated";

interface AuthContextValue {
  status: AuthStatus;
  user: UserProfile | null;
  login: (email: string, password: string) => Promise<void>;
  register: (payload: {
    full_name: string;
    username: string;
    email: string;
    password: string;
  }) => Promise<void>;
  logout: () => void;
  refreshProfile: () => Promise<void>;
  /**
   * Runs `fn` with a valid access token. If the token has expired (401),
   * transparently refreshes it once via the refresh token and retries -
   * callers never have to think about token expiry themselves.
   */
  withAuth: <T,>(fn: (accessToken: string) => Promise<T>) => Promise<T>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<AuthStatus>("loading");
  const [user, setUser] = useState<UserProfile | null>(null);

  // Nothing in this provider renders based on the token values themselves
  // (only `status`/`user` drive UI), so they live in refs rather than
  // state. This matters because withAuth can be called twice in quick
  // succession within the same async flow (e.g. translateImage then
  // refreshProfile in translate/page.tsx). If the first call refreshes the
  // tokens, the second call must see the NEW tokens immediately - with
  // React state it would still be reading the value captured when this
  // render started, since state updates don't apply until a re-render.
  // Refs give every call a live, synchronously-updated view of the
  // current tokens, so a mid-flow refresh doesn't get undone by a second
  // call using the old, now-rotated-out refresh token.
  const accessTokenRef = useRef<string | null>(null);
  const refreshTokenRef = useRef<string | null>(null);

  const setAccessToken = useCallback((token: string | null) => {
    accessTokenRef.current = token;
  }, []);

  const setRefreshToken = useCallback((token: string | null) => {
    refreshTokenRef.current = token;
  }, []);

  const persistTokens = useCallback(
    (access: string, refresh: string) => {
      setAccessToken(access);
      setRefreshToken(refresh);
      localStorage.setItem(ACCESS_TOKEN_KEY, access);
      localStorage.setItem(REFRESH_TOKEN_KEY, refresh);
    },
    [setAccessToken, setRefreshToken]
  );

  const clearSession = useCallback(() => {
    setAccessToken(null);
    setRefreshToken(null);
    setUser(null);
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    setStatus("unauthenticated");
  }, [setAccessToken, setRefreshToken]);

  // Rehydrate the session from localStorage on first load.
  useEffect(() => {
    const storedAccess = localStorage.getItem(ACCESS_TOKEN_KEY);
    const storedRefresh = localStorage.getItem(REFRESH_TOKEN_KEY);

    if (!storedAccess || !storedRefresh) {
      setStatus("unauthenticated");
      return;
    }

    setAccessToken(storedAccess);
    setRefreshToken(storedRefresh);

    api
      .getMe(storedAccess)
      .then((profile) => {
        setUser(profile);
        setStatus("authenticated");
      })
      .catch(async () => {
        // Access token expired - try the refresh token before giving up.
        try {
          const tokens = await api.refreshTokens(storedRefresh);
          persistTokens(tokens.access_token, tokens.refresh_token);
          const profile = await api.getMe(tokens.access_token);
          setUser(profile);
          setStatus("authenticated");
        } catch {
          clearSession();
        }
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const withAuth = useCallback(
    async <T,>(fn: (accessToken: string) => Promise<T>): Promise<T> => {
      const currentAccessToken = accessTokenRef.current;
      if (!currentAccessToken) throw new ApiError("Not signed in", "UNAUTHORIZED", 401, null);

      try {
        return await fn(currentAccessToken);
      } catch (err) {
        const is401 = err instanceof ApiError && err.status === 401;
        const currentRefreshToken = refreshTokenRef.current;
        if (!is401 || !currentRefreshToken) throw err;

        // Access token expired mid-session: refresh once and retry.
        // Reading from the refs (not the outer accessToken/refreshToken
        // state) means that if withAuth is called again later in the same
        // handler - e.g. refreshProfile() right after translateImage() -
        // it picks up the tokens this call just persisted, instead of the
        // stale ones captured when this render started.
        const tokens = await api.refreshTokens(currentRefreshToken);
        persistTokens(tokens.access_token, tokens.refresh_token);
        return await fn(tokens.access_token);
      }
    },
    [persistTokens]
  );

  const login = useCallback(
    async (email: string, password: string) => {
      const tokens = await api.login({ email, password });
      persistTokens(tokens.access_token, tokens.refresh_token);
      const profile = await api.getMe(tokens.access_token);
      setUser(profile);
      setStatus("authenticated");
    },
    [persistTokens]
  );

  const register = useCallback(
    async (payload: { full_name: string; username: string; email: string; password: string }) => {
      await api.register(payload);
      // Registration doesn't return tokens by design - log in right after
      // so the person doesn't have to fill in the login form again.
      await login(payload.email, payload.password);
    },
    [login]
  );

  const refreshProfile = useCallback(async () => {
    const profile = await withAuth((token) => api.getMe(token));
    setUser(profile);
  }, [withAuth]);

  const logout = useCallback(() => {
    clearSession();
  }, [clearSession]);

  const value = useMemo(
    () => ({ status, user, login, register, logout, refreshProfile, withAuth }),
    [status, user, login, register, logout, refreshProfile, withAuth]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
