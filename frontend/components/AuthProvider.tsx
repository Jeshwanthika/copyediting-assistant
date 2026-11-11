"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import type { ReactNode } from "react";
import { getMe, login as apiLogin } from "@/lib/api";
import { SESSION_EVENT, clearSession, loadSession, saveSession } from "@/lib/session";
import type { User } from "@/types";

interface AuthState {
  /** The signed-in user, or null. */
  user: User | null;
  /** True until the saved login has been checked with the backend. */
  checking: boolean;
  isLead: boolean;
  signIn: (username: string, password: string) => Promise<User>;
  signOut: () => void;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [checking, setChecking] = useState(true);

  // On first load: confirm the saved token is still valid (and the role unchanged).
  useEffect(() => {
    const saved = loadSession();
    if (!saved) {
      setChecking(false);
      return;
    }
    setUser(saved.user);
    getMe()
      .then((fresh) => {
        setUser(fresh);
        saveSession({ ...saved, user: fresh });
      })
      .catch(() => {
        // A 401 has already cleared the session; anything else (backend down)
        // keeps the saved user so the page can show its own error.
      })
      .finally(() => setChecking(false));
  }, []);

  // Follow sign-in / sign-out from other tabs and from expired tokens.
  useEffect(() => {
    const sync = () => setUser(loadSession()?.user ?? null);
    window.addEventListener(SESSION_EVENT, sync);
    window.addEventListener("storage", sync);
    return () => {
      window.removeEventListener(SESSION_EVENT, sync);
      window.removeEventListener("storage", sync);
    };
  }, []);

  const signIn = useCallback(async (username: string, password: string) => {
    const session = await apiLogin(username, password);
    saveSession(session);
    setUser(session.user);
    return session.user;
  }, []);

  const signOut = useCallback(() => {
    clearSession();
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, checking, isLead: !!user?.is_lead, signIn, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthState {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used inside <AuthProvider>");
  return value;
}

/** Shows its children to leads only; everyone else sees a short explanation. */
export function LeadOnly({ children, what = "This page" }: { children: ReactNode; what?: string }) {
  const { isLead, checking } = useAuth();
  if (checking) return <div className="page-wrap"><p className="muted">Checking access…</p></div>;
  if (!isLead) {
    return (
      <div className="page-wrap">
        <div className="access-denied">
          <span className="material-symbols-outlined">lock</span>
          <h1 className="page-title">Leads only</h1>
          <p className="page-subtitle">
            {what} is only available to leads and admins. If you need a rule changed, raise a query
            with your lead.
          </p>
        </div>
      </div>
    );
  }
  return <>{children}</>;
}
