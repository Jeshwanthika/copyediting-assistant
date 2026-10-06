"use client";
import { useEffect, useMemo, useState } from "react";
import { getRules } from "@/lib/api";
import { capitalize } from "@/lib/format";
import type { Rule } from "@/types";

function formatDate(iso: string) {
  try {
    return new Date(iso).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
  } catch {
    return iso;
  }
}

export default function FAQsPage() {
  const [rules, setRules] = useState<Rule[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [q, setQ] = useState("");
  const [category, setCategory] = useState("All");
  const [open, setOpen] = useState<number | null>(null);

  useEffect(() => {
    getRules().then((rs) => {
      setRules(rs);
      setLoaded(true);
      if (rs.length) setOpen(rs[0].id);
    });
  }, []);

  const categories = useMemo(() => ["All", ...Array.from(new Set(rules.map((r) => r.category)))], [rules]);

  const shown = useMemo(
    () =>
      rules.filter(
        (r) =>
          (category === "All" || r.category === category) &&
          `${r.rule_code} ${r.topic} ${r.rule_text} ${r.question_pattern || ""}`.toLowerCase().includes(q.toLowerCase()),
      ),
    [rules, q, category],
  );

  return (
    <div className="page-wrap">
      <div className="label-code page-kicker">KNOWLEDGE BASE · SECTION 04</div>
      <div className="page-header-row">
        <div>
          <h1 className="page-title">Frequently Asked Questions</h1>
          <p className="page-subtitle">
            Quick answers to common trainee questions, standard manuscript handling procedures, and definitive style
            dispute guidance.
          </p>
        </div>
        <div className="page-badges">
          <span className="status-pill status-confirmed">{rules.length} Curated Answers</span>
          <span className="status-pill status-reviewed">
            <span className="material-symbols-outlined" style={{ fontSize: 14 }}>menu_book</span>&nbsp;House Style v2.4
          </span>
          <span className="kbd-pill label-code">⌘K</span>
        </div>
      </div>

      <div className="page-toolbar">
        <div className="search-box">
          <span className="material-symbols-outlined">search</span>
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search FAQs by question, XML element, or keyword (e.g. affiliation, footnote, hyphenation)..."
          />
        </div>
      </div>

      <div className="chips">
        {categories.map((c) => (
          <button key={c} className={`chip ${category === c ? "active" : ""}`} type="button" onClick={() => setCategory(c)}>
            {c === "All" ? `All (${rules.length})` : c}
          </button>
        ))}
      </div>

      <div className="faq-list">
        {!loaded ? (
          <div className="faq-item" style={{ padding: 16 }}>Loading FAQs…</div>
        ) : shown.length === 0 ? (
          <div className="faq-item" style={{ padding: 16 }}>No matching FAQs.</div>
        ) : (
          shown.map((r) => {
            const isOpen = open === r.id;
            return (
              <article className="faq-item" key={r.id}>
                <button className="faq-summary" type="button" onClick={() => setOpen(isOpen ? null : r.id)}>
                  <div style={{ minWidth: 0 }}>
                    <div className="rule-meta">
                      <span className="label-code" style={{ color: "var(--on-surface-variant)" }}>{r.category}</span>
                      {r.escalation ? (
                        <span className="status-pill status-escalation">Escalation Required</span>
                      ) : (
                        <span className={`status-pill status-${r.status}`}>Rule {r.rule_code} ({capitalize(r.status)})</span>
                      )}
                    </div>
                    <div className="title-sm faq-question">{r.question_pattern || r.topic}</div>
                    {!isOpen && <p className="faq-preview">{r.rule_text}</p>}
                  </div>
                  <span className="material-symbols-outlined">{isOpen ? "expand_less" : "expand_more"}</span>
                </button>
                {isOpen && (
                  <div className="faq-answer">
                    <p>{r.rule_text}</p>
                    {r.action && (
                      <div className="rule-action" style={{ marginTop: 12 }}>
                        <span className="material-symbols-outlined">task_alt</span>
                        <div><strong>Immediate action</strong><p>{r.action}</p></div>
                      </div>
                    )}
                    <div className="faq-answer-footer">
                      <div className="faq-answer-actions">
                        <a className="btn-filled" href={`/rules#${r.rule_code}`}>
                          View in Style Manual <span className="material-symbols-outlined" style={{ fontSize: 16 }}>arrow_forward</span>
                        </a>
                        <button className="btn-outline" type="button">Flag Exception</button>
                      </div>
                      <span className="label-code" style={{ color: "var(--on-surface-variant)" }}>
                        Updated {formatDate(r.updated_at)} · v{r.version}
                      </span>
                    </div>
                  </div>
                )}
              </article>
            );
          })
        )}
      </div>
    </div>
  );
}
