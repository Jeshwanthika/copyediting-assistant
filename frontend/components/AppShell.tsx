"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import type { ReactNode } from "react";

const nav = [
  ["/", "chat", "AI assistant"],
  ["/rules", "auto_stories", "Style manual"],
  ["/faqs", "help_outline", "FAQs"],
  ["/review", "library_books", "Knowledge base"],
] as const;

type Conversation = { id: string; text: string };

export default function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);
  const [conversations, setConversations] = useState<Conversation[]>([]);

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

  return (
    <div className={`app-shell ${collapsed ? "is-collapsed" : ""}`}>
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">CE</div>
          <div className="brand-copy">
            <span className="brand-title">Copydesk</span>
            <span className="brand-version">Editorial assistant</span>
          </div>
        </div>

        <nav className="sidebar-nav" aria-label="Primary navigation">
          {nav.map(([href, icon, label]) => (
            <Link key={href} href={href} className={`nav-item ${pathname === href ? "active" : ""}`} title={label}>
              <span className="material-symbols-outlined">{icon}</span>
              <span className="nav-label">{label}</span>
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
