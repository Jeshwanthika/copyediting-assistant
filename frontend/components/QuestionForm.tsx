"use client";

import { useState } from "react";
import { createQuestion } from "@/lib/api";

export default function QuestionForm() {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleAsk() {
    if (!text.trim()) {
      setError("Please type a question first.");
      setMessage(null);
      return;
    }
    setLoading(true);
    setError(null);
    setMessage(null);
    try {
      await createQuestion(text.trim());
      setMessage("Question received. AI decision support will be added in the next stage.");
      setText("");
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
        placeholder="e.g. How should I tag an author name with three given names?"
        rows={5}
        aria-label="Your question"
      />
      <button onClick={handleAsk} disabled={loading}>
        {loading ? "Sending..." : "Ask"}
      </button>
      {message && <p className="success">{message}</p>}
      {error && <p className="error">{error}</p>}
    </div>
  );
}
