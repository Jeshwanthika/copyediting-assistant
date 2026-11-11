import type { Session } from "@/types";

/**
 * The signed-in session (token + user) kept in the browser.
 *
 * This only decides what the UI shows. Every request carries the token and the
 * backend checks the role itself, so editing localStorage does not grant access.
 */
const KEY = "ce-session";
export const SESSION_EVENT = "ce:session";

export function loadSession(): Session | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return null;
    const session = JSON.parse(raw) as Session;
    if (!session.access_token || !session.user) return null;
    if (new Date(session.expires_at).getTime() <= Date.now()) {
      localStorage.removeItem(KEY);
      return null;
    }
    return session;
  } catch {
    return null;
  }
}

export function saveSession(session: Session): void {
  try {
    localStorage.setItem(KEY, JSON.stringify(session));
  } catch {}
  window.dispatchEvent(new Event(SESSION_EVENT));
}

export function clearSession(): void {
  try {
    localStorage.removeItem(KEY);
  } catch {}
  window.dispatchEvent(new Event(SESSION_EVENT));
}

export function getToken(): string | null {
  return loadSession()?.access_token ?? null;
}
