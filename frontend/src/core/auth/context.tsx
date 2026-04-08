"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";

import { getMe, login, logout, register } from "./api";
import type { Session } from "./types";

const TOKEN_KEY = "deerflow_auth_token";
const SESSION_KEY = "deerflow_session";

interface AuthContextValue {
  session: Session | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  doLogin: (email: string, password: string) => Promise<void>;
  doRegister: (email: string, password: string) => Promise<void>;
  doLogout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem(TOKEN_KEY);
    if (token) {
      getMe(token)
        .then((s) => {
          if (s) {
            setSession(s);
            localStorage.setItem(SESSION_KEY, JSON.stringify(s));
          } else {
            localStorage.removeItem(TOKEN_KEY);
            localStorage.removeItem(SESSION_KEY);
          }
        })
        .catch(() => {
          localStorage.removeItem(TOKEN_KEY);
          localStorage.removeItem(SESSION_KEY);
        })
        .finally(() => setIsLoading(false));
    } else {
      setIsLoading(false);
    }
  }, []);

  const doLogin = useCallback(async (email: string, password: string) => {
    const result = await login({ email, password });
    localStorage.setItem(TOKEN_KEY, result.access_token);
    localStorage.setItem(SESSION_KEY, JSON.stringify(result));
    setSession(result);
  }, []);

  const doRegister = useCallback(async (email: string, password: string) => {
    const result = await register({ email, password });
    localStorage.setItem(TOKEN_KEY, result.access_token);
    localStorage.setItem(SESSION_KEY, JSON.stringify(result));
    setSession(result);
  }, []);

  const doLogout = useCallback(async () => {
    await logout();
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(SESSION_KEY);
    setSession(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        session,
        isLoading,
        isAuthenticated: !!session,
        doLogin,
        doRegister,
        doLogout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}
