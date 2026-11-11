"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { useAuth } from "@/components/AuthProvider";
import BrandLogo from "@/components/BrandLogo";
import { BRAND } from "@/lib/brand";
import type { UserRole } from "@/types";

const ROLE_TEXT: Record<UserRole, { label: string; icon: string; blurb: string }> = {
  lead: {
    label: "Lead / Admin",
    icon: "admin_panel_settings",
    blurb: "Maintain rules, the knowledge base and the errors & solutions library.",
  },
  trainee: {
    label: "Trainee",
    icon: "school",
    blurb: "Ask questions, read the style manual and the errors & solutions guides.",
  },
};

/** Only allow redirects to pages inside this app. */
function safeNext(): string {
  const next = new URLSearchParams(window.location.search).get("next") || "/";
  return next.startsWith("/") && !next.startsWith("//") && next !== "/login" ? next : "/";
}

export default function LoginPage() {
  const router = useRouter();
  const { user, checking, signIn, signOut } = useAuth();
  const [role, setRole] = useState<UserRole>("trainee");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Already signed in: skip this page.
  useEffect(() => {
    if (!checking && user && !busy) router.replace(safeNext());
  }, [checking, user, busy, router]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!username.trim() || !password) {
      setError("Enter your username and password.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const signedIn = await signIn(username.trim(), password);
      if (signedIn.role !== role) {
        signOut();
        setError(
          `This is a ${ROLE_TEXT[signedIn.role].label} account. Choose “${ROLE_TEXT[signedIn.role].label}” above to sign in with it.`,
        );
        return;
      }
      router.replace(safeNext());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sign-in failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="login-page">
      <section className="login-hero" aria-hidden="true">
        <div className="login-hero-inner">
          <BrandLogo className="login-brand" />
          <h1 className="login-headline">
            <span className="thin">Quality copy-editing</span>
            <em>in a few clicks</em>
          </h1>
          <p className="login-lede">
            House rules, worked examples and known error fixes for the journal copy-editing team — in one
            place.
          </p>
        </div>
      </section>

      <section className="login-panel">
        <form className="login-card" onSubmit={handleSubmit} noValidate>
          <div className="eyebrow">Welcome back</div>
          <h2>Sign in to {BRAND.name}</h2>

          <div className="role-switch" role="tablist" aria-label="Account type">
            {(Object.keys(ROLE_TEXT) as UserRole[]).map((r) => (
              <button
                key={r}
                type="button"
                role="tab"
                aria-selected={role === r}
                className={`role-option ${role === r ? "active" : ""}`}
                onClick={() => {
                  setRole(r);
                  setError(null);
                }}
              >
                <span className="material-symbols-outlined">{ROLE_TEXT[r].icon}</span>
                {ROLE_TEXT[r].label}
              </button>
            ))}
          </div>
          <p className="role-blurb">{ROLE_TEXT[role].blurb}</p>

          <label className="field">
            <span>Username</span>
            <input
              type="text"
              autoComplete="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoFocus
            />
          </label>
          <label className="field">
            <span>Password</span>
            <div className="password-wrap">
              <input
                type={showPassword ? "text" : "password"}
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
              <button
                type="button"
                className="icon-btn"
                onClick={() => setShowPassword((v) => !v)}
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                <span className="material-symbols-outlined">{showPassword ? "visibility_off" : "visibility"}</span>
              </button>
            </div>
          </label>

          {error && (
            <p className="error" role="alert">
              {error}
            </p>
          )}

          <button className="btn-filled btn-block" type="submit" disabled={busy}>
            {busy ? "Signing in…" : `Sign in as ${ROLE_TEXT[role].label}`}
            {!busy && <span className="material-symbols-outlined">arrow_forward</span>}
          </button>
          <p className="login-help">Forgotten your password? Ask a lead or admin to reset it.</p>
        </form>
      </section>
    </div>
  );
}
