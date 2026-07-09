import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { api, setOnAuthExpired } from "@/lib/api";

type Role = "author" | "editor" | "admin";
interface User { id: string; email: string; full_name: string; role: Role; is_active: boolean; }
interface AuthState {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthState | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setOnAuthExpired(() => setUser(null));
    return () => setOnAuthExpired(null);
  }, []);

  useEffect(() => {
    const token = localStorage.getItem("ab_access_token");
    if (!token) { setLoading(false); return; }
    api.get("/auth/me")
      .then(setUser)
      .catch(() => localStorage.removeItem("ab_access_token"))
      .finally(() => setLoading(false));
  }, []);

  async function login(email: string, password: string) {
    const res = await api.login(email, password);
    localStorage.setItem("ab_access_token", res.access_token);
    localStorage.setItem("ab_refresh_token", res.refresh_token);
    setUser(res.user);
  }

  function logout() {
    localStorage.removeItem("ab_access_token");
    localStorage.removeItem("ab_refresh_token");
    setUser(null);
  }

  async function refreshUser() {
    const res = await api.get("/auth/me");
    setUser(res);
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components -- Provider + its hook are one cohesive unit, kept together deliberately
export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
