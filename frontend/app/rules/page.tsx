"use client";
import { useEffect, useMemo, useState } from "react";
import { getRules } from "@/lib/api";
import type { Rule } from "@/types";

function formatDate(iso: string) {
  try {
    return new Date(iso).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
  } catch {
    return iso;
  }
}

export default function RulesPage() {
  const [rules, setRules] = useState<Rule[]>([]);
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("all");
  const [category, setCategory] = useState("All");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getRules().then(setRules).finally(() => setLoading(false));
  }, []);

  const categories = useMemo(() => ["All", ...Array.from(new Set(rules.map((r) => r.category)))], [rules]);

  const shown = useMemo(
    () =>
      rules.filter(
        (r) =>
          (status === "all" || r.status === status) &&
          (category === "All" || r.category === category) &&
          `${r.rule_code} ${r.topic} ${r.rule_text} ${r.category}`.toLowerCase().includes(q.toLowerCase()),
      ),
    [rules, q, status, category],
  );

  return (
    <div className="page-wrap">
      <div className="page-header-row">
        <div>
          <div className="label-code page-kicker">CORPUS REPOSITORY / HOUSE STANDARD OPERATING PROCEDURES</div>
          <h1 className="page-title">Style Manual</h1>
          <p className="page-subtitle">
            Browse approved copy-editing guidance, formal decision trees, XML tagging protocols, and ethical
            manuscript standards across publication imprints.
          </p>
        </div>
        <div className="sync-badge">
          <div>
            <div className="title-sm">{rules.length} Active Rules Synchronized</div>
            <div className="label-code" style={{ color: "var(--on-surface-variant)" }}>v2.4 Editorial Engine · Last validated moments ago</div>
          </div>
          <span className="material-symbols-outlined sync-icon">sync</span>
        </div>
      </div>

      <div className="page-toolbar">
        <div className="search-box">
          <span className="material-symbols-outlined">search</span>
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search by rule ID, keyword, or editorial topic (e.g. author order, affiliation, ORCID, JATS)..."
          />
          <span className="label-code">⌘K</span>
        </div>
        <select className="filter" value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="all">All Statuses</option>
          <option value="confirmed">Confirmed</option>
          <option value="reviewed">Reviewed</option>
          <option value="draft">Draft</option>
          <option value="superseded">Superseded</option>
        </select>
      </div>

      <div className="chips">
        {categories.map((c) => (
          <button key={c} className={`chip ${category === c ? "active" : ""}`} type="button" onClick={() => setCategory(c)}>
            {c === "All" ? "All Guidelines" : c}
          </button>
        ))}
      </div>

      <div className="rules-meta-row">
        <span className="label-code">{shown.length} CORE STANDARDS DISPLAYED · Filtered by relevance</span>
        <span className="label-code">Sort: Version <span className="material-symbols-outlined" style={{ fontSize: 14 }}>arrow_downward</span></span>
      </div>

      <div className="rule-list" style={{ marginTop: 16 }}>
        {loading ? (
          <div className="rule-card">Loading guidelines…</div>
        ) : shown.length === 0 ? (
          <div className="rule-card">No matching guidelines.</div>
        ) : (
          shown.map((r) => <RuleCard key={r.id} rule={r} />)
        )}
      </div>

      {!loading && shown.length > 0 && (
        <div className="rules-pagination">
          <span className="label-code">Showing 1-{shown.length} of {rules.length} guidelines</span>
          <div className="rules-pagination-controls">
            <button className="btn-outline" type="button" disabled>Previous</button>
            <span className="label-code">Page 1 of 1</span>
            <button className="btn-outline" type="button" disabled>Next</button>
          </div>
        </div>
      )}
    </div>
  );
}

function RuleCard({ rule: r }: { rule: Rule }) {
  return (
    <article className="rule-card" id={r.rule_code}>
      <div className="rule-top">
        <div className="rule-meta">
          <span className="rule-code">{r.rule_code}</span>
          <span className={`status-pill status-${r.status}`}>{r.status === "confirmed" ? "✓ " : ""}{r.status}</span>
          <span className="label-code" style={{ color: "var(--on-surface-variant)" }}>{r.category}</span>
        </div>
        <span className="label-code">v{r.version}</span>
      </div>
      <h2>{r.topic}</h2>
      <p>{r.rule_text}</p>
      {r.action && (
        <div className="rule-action">
          <span className="material-symbols-outlined">priority_high</span>
          <div><strong className="label-code">IMMEDIATE ACTION</strong><p>{r.action}</p></div>
        </div>
      )}
      <div className="rule-footer">
        <span>Source: {r.source}{r.source_section ? ` · ${r.source_section}` : ""} · Updated {formatDate(r.updated_at)}</span>
        <span className="rule-footer-actions">
          <button className="btn-outline" type="button"><span className="material-symbols-outlined" style={{ fontSize: 15 }}>content_copy</span>&nbsp;Copy Rule</button>
          <button className="btn-outline" type="button"><span className="material-symbols-outlined" style={{ fontSize: 15 }}>account_tree</span>&nbsp;View Flow</button>
        </span>
      </div>
    </article>
  );
}
