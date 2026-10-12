import { createContext, useContext, useEffect, useState, ReactNode, useCallback } from "react";
import { api, getToken, setToken } from "@/lib/api";
import type { User } from "@/types";

type AuthCtx = {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (payload: { email: string; username: string; password: string; full_name?: string; native_language_code?: string }) => Promise<void>;
  logout: () => void;
  refresh: () => Promise<void>;
  setUser: (u: User) => void;
};

const AuthContext = createContext<AuthCtx>({} as AuthCtx);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    if (!getToken()) { setLoading(false); return; }
    try {
      const { data } = await api.get<User>("/auth/me");
      setUser(data);
    } catch (err: any) {
      if (err?.response?.status === 401) {
        setToken(null);
        setUser(null);
      }
      // network/CORS/timeout gibi hatalarda token'a dokunma, oturumu koru
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  const login = async (email: string, password: string) => {
    const { data } = await api.post("/auth/login", { email, password });
    setToken(data.access_token);
    setUser(data.user);
  };

  const register: AuthCtx["register"] = async (payload) => {
    const { data } = await api.post("/auth/register", payload);
    setToken(data.access_token);
    setUser(data.user);
  };

  const logout = () => {
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, refresh, setUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
