"use client";

import { useState } from "react";
import AnswerCard from "@/components/AnswerCard";
import { createQuestion } from "@/lib/api";
import type { QuestionAnswer } from "@/types";

export default function QuestionForm() {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<QuestionAnswer | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleAsk() {
    if (!text.trim()) {
      setError("Please type a question first.");
      setResult(null);
      return;
    }
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      setResult(await createQuestion(text.trim()));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="e.g. Can I change the author order?"
        rows={4}
        aria-label="Your question"
      />
      <button onClick={handleAsk} disabled={loading}>
        {loading ? "Checking..." : "Ask"}
      </button>
      {error && <p className="error">{error}</p>}
      {result && (
        <div aria-live="polite">
          <p className="asked">
            <strong>Your question:</strong> {result.question_text}
          </p>
          <AnswerCard answer={result.answer} />
        </div>
      )}
    </div>
  );
}
