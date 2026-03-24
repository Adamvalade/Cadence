"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { api } from "./api";
import { persistAccessToken } from "./sessionToken";
import type { AuthResponse, UserBrief } from "./types";

interface AuthContextType {
  user: UserBrief | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, username: string, password: string, displayName?: string) => Promise<void>;
  logout: () => Promise<void>;
  refresh: (opts?: { clearOnAuthError?: boolean }) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserBrief | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async (opts?: { clearOnAuthError?: boolean }) => {
    const clearOnAuthError = opts?.clearOnAuthError !== false;
    try {
      const u = await api.get<UserBrief>("/auth/me");
      setUser(u);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "";
      const sessionGone =
        msg === "Not authenticated" ||
        msg === "Invalid token" ||
        msg === "User not found";
      if (clearOnAuthError && sessionGone) {
        setUser(null);
        persistAccessToken(null);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const login = async (email: string, password: string) => {
    const res = await api.post<AuthResponse>("/auth/login", { email, password });
    persistAccessToken(res.access_token);
    setUser(res.user);
    await refresh({ clearOnAuthError: false });
  };

  const register = async (email: string, username: string, password: string, displayName?: string) => {
    const res = await api.post<AuthResponse>("/auth/register", {
      email,
      username,
      password,
      display_name: displayName || username,
    });
    persistAccessToken(res.access_token);
    setUser(res.user);
    await refresh({ clearOnAuthError: false });
  };

  const logout = async () => {
    await api.post("/auth/logout");
    persistAccessToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, refresh }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
