"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import { useAuth } from "@/components/AuthProvider";
import BrandLogo from "@/components/BrandLogo";
import { BRAND } from "@/lib/brand";

type NavItem = { href: string; icon: string; label: string; leadOnly?: boolean };

const nav: NavItem[] = [
  { href: "/", icon: "chat", label: "AI assistant" },
  { href: "/rules", icon: "auto_stories", label: "Style manual" },
  { href: "/faqs", icon: "help_outline", label: "FAQs" },
  { href: "/review", icon: "library_books", label: "Knowledge base", leadOnly: true },
  { href: "/errors-solutions", icon: "picture_as_pdf", label: "Errors & solutions" },
];

type Conversation = { id: string; text: string };

/** Pages that are shown without the sidebar and without signing in. */
const PUBLIC_PATHS = ["/login"];

export default function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, checking, isLead, signOut } = useAuth();
  const [collapsed, setCollapsed] = useState(false);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const isPublic = PUBLIC_PATHS.includes(pathname);

  useEffect(() => {
    const load = () => {
      try {
        const raw = JSON.parse(localStorage.getItem("ce-conversations") || "[]");
        if (Array.isArray(raw)) setConversations(raw);
      } catch {}
    };
    load();
    window.addEventListener("ce:conversations", load);
    return () => window.removeEventListener("ce:conversations", load);
  }, []);

  // Not signed in: go to the sign-in page, then come back here afterwards.
  useEffect(() => {
    if (!checking && !user && !isPublic) {
      router.replace(`/login?next=${encodeURIComponent(pathname)}`);
    }
  }, [checking, user, isPublic, pathname, router]);

  if (isPublic) return <>{children}</>;

  if (checking || !user) {
    return (
      <div className="splash">
        <div className="brand-mark">{BRAND.mark}</div>
        <span className="muted">{checking ? "Loading…" : "Redirecting to sign in…"}</span>
      </div>
    );
  }

  const items = nav.filter((item) => !item.leadOnly || isLead);
  const isActive = (href: string) => (href === "/" ? pathname === "/" : pathname.startsWith(href));
  const initials = user.display_name
    .split(/\s+/)
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  return (
    <div className={`app-shell ${collapsed ? "is-collapsed" : ""}`}>
      <aside className="sidebar">
        <BrandLogo />

        <nav className="sidebar-nav" aria-label="Primary navigation">
          {items.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`nav-item ${isActive(item.href) ? "active" : ""}`}
              title={item.label}
            >
              <span className="material-symbols-outlined">{item.icon}</span>
              <span className="nav-label">{item.label}</span>
            </Link>
          ))}
        </nav>

        <div className="conversations">
          <div className="conversations-head">
            <span className="conversations-title">Conversations</span>
            <Link
              href="/"
              className="conversations-add"
              aria-label="New conversation"
              onClick={() => window.dispatchEvent(new Event("ce:new"))}
            >
              <span className="material-symbols-outlined">add</span>
            </Link>
          </div>
          <div className="conversations-list">
            {conversations.map((c) => (
              <Link key={c.id} href={`/?q=${encodeURIComponent(c.text)}`} className="conversation-item" title={c.text}>
                {c.text}
              </Link>
            ))}
          </div>
        </div>

        <div className="user-card" title={`${user.display_name} (${user.username})`}>
          <div className="user-avatar">{initials || "U"}</div>
          <div className="user-copy">
            <span className="user-name">{user.display_name}</span>
            <span className={`role-badge ${isLead ? "role-lead" : "role-trainee"}`}>
              {isLead ? "Lead / Admin" : "Trainee"}
            </span>
          </div>
          <button
            className="icon-btn signout-btn"
            type="button"
            onClick={() => {
              signOut();
              router.replace("/login");
            }}
            aria-label="Sign out"
            title="Sign out"
          >
            <span className="material-symbols-outlined">logout</span>
          </button>
        </div>

        <button className="collapse-btn" type="button" onClick={() => setCollapsed((v) => !v)}>
          <span className="material-symbols-outlined">{collapsed ? "chevron_right" : "chevron_left"}</span>
          <span className="nav-label">Collapse sidebar</span>
        </button>
      </aside>

      <div className="content-frame">
        <main className="page-main">{children}</main>
      </div>
    </div>
  );
}
