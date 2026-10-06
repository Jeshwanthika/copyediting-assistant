"use client";

import { useEffect, useState } from "react";
import AnswerCard from "@/components/AnswerCard";
import { createQuestion } from "@/lib/api";
import type { QuestionAnswer } from "@/types";

const suggestions = [
  "Should particle names like 'van' or 'de' count as part of the family name?",
  "Can an author's order be changed after manuscript acceptance?",
  "How should verified ORCID iDs be formatted?",
];

export default function QuestionForm() {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<QuestionAnswer | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => { const q = new URLSearchParams(window.location.search).get("q"); if(q) setText(q); }, []);

  useEffect(() => {
    const reset = () => { setText(""); setResult(null); setError(null); };
    window.addEventListener("ce:new", reset);
    return () => window.removeEventListener("ce:new", reset);
  }, []);

  async function handleAsk() {
    if (!text.trim()) { setError("Please type a question first."); return; }
    setLoading(true); setError(null); setResult(null);
    try {
      const answer = await createQuestion(text.trim());
      setResult(answer);
      try {
        const prev = JSON.parse(localStorage.getItem("ce-conversations") || "[]");
        const item = { id: String(Date.now()), text: text.trim() };
        localStorage.setItem("ce-conversations", JSON.stringify([item, ...prev].slice(0, 20)));
        window.dispatchEvent(new Event("ce:conversations"));
      } catch {}
      try {
        if (answer.answer.escalation_required) {
          const queries = JSON.parse(localStorage.getItem("ce-queries") || "[]");
          if (!queries.some((x: { question: string }) => x.question === text.trim())) {
            queries.unshift({
              id: `EQ-${Date.now().toString().slice(-4)}`,
              question: text.trim(),
              status: "Open",
              priority: "Attention",
              rule: answer.answer.rule_code || "Unmatched",
              time: "Just now",
              reason: answer.answer.escalation_reason || "Lead review required.",
            });
            localStorage.setItem("ce-queries", JSON.stringify(queries.slice(0, 20)));
          }
        }
      } catch {}
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleAsk(); }
  }

  return (
    <div className="assistant-page">
      <header className="assistant-header">
        <h1>AI assistant</h1>
        <p>House style grounded · Editorially cautious</p>
      </header>

      <div className="assistant-body">
        {!result && !error && (
          <div className="empty-state">
            <div className="empty-icon"><span className="material-symbols-outlined">auto_stories</span></div>
            <h2>What are you editing?</h2>
            <p>Ask a style question, paste a sentence, or request an author query. Copydesk will consult the house manual first.</p>
            <div className="empty-suggest-row">
              {suggestions.map((q) => (
                <button key={q} className="empty-suggest-card" type="button" onClick={() => setText(q)}>{q}</button>
              ))}
            </div>
          </div>
        )}

        {error && <p className="error">{error}</p>}

        {result && (
          <section className="inquiry" aria-live="polite" style={{ width: "100%", maxWidth: 820, margin: "0 auto" }}>
            <div className="divider-label label-code">ACTIVE EDITORIAL INQUIRY SESSION</div>
            <div className="user-row">
              <div className="user-bubble-wrap">
                <div className="user-meta label-code">You &nbsp;•&nbsp; Today</div>
                <div className="user-bubble">&ldquo;{result.question_text}&rdquo;</div>
              </div>
              <div className="avatar" style={{ width: 32, height: 32, fontSize: 12, fontWeight: 600 }}>CE</div>
            </div>
            <AnswerCard answer={result.answer} />
          </section>
        )}
      </div>

      <div className="assistant-inputbar">
        <div className="docked-box">
          <textarea
            className="docked-textarea"
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder="Ask about grammar, style, citations, or paste text to review..."
            rows={3}
            aria-label="Editorial question"
          />
          <div className="docked-footer">
            <span className="docked-hint"><span className="material-symbols-outlined">add</span>Shift + Enter for a new line</span>
            <button className="send-btn" type="button" onClick={handleAsk} disabled={loading} aria-label="Send">
              <span className="material-symbols-outlined">{loading ? "hourglass_empty" : "keyboard_return"}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
