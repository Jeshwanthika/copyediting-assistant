"use client";

import { useEffect, useRef, useState } from "react";
import AnswerCard from "@/components/AnswerCard";
import { useAuth } from "@/components/AuthProvider";
import { createQuestion } from "@/lib/api";
import type { QuestionAnswer } from "@/types";

type SpeechRecognitionLike = {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  onresult: (e: { results: ArrayLike<ArrayLike<{ transcript: string }>> }) => void;
  onerror: (e: { error: string }) => void;
  onend: () => void;
  start: () => void;
  stop: () => void;
  abort: () => void;
};
type SpeechRecognitionCtor = new () => SpeechRecognitionLike;

const suggestions = [
  "Should particle names like 'van' or 'de' count as part of the family name?",
  "Can an author's order be changed after manuscript acceptance?",
  "How should verified ORCID iDs be formatted?",
];

export default function QuestionForm() {
  const { user } = useAuth();
  const firstName = user?.display_name.split(/\s+/)[0] ?? "";
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<QuestionAnswer | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [voice, setVoice] = useState<"idle" | "recording">("idle");
  const [voiceNote, setVoiceNote] = useState<string | null>(null);
  const recognitionRef = useRef<SpeechRecognitionLike | null>(null);
  const baseTextRef = useRef("");

  useEffect(() => { const q = new URLSearchParams(window.location.search).get("q"); if(q) setText(q); }, []);

  useEffect(() => {
    const reset = () => { stopVoice(); setText(""); setResult(null); setError(null); };
    window.addEventListener("ce:new", reset);
    return () => window.removeEventListener("ce:new", reset);
  }, []);

  /** Turn the mic off straight away, ignoring any words still being processed. */
  function stopVoice() {
    const recognition = recognitionRef.current;
    if (!recognition) return;
    recognition.onresult = () => {};
    recognition.onend = () => {};
    recognition.abort();
    recognitionRef.current = null;
    setVoice("idle");
  }

  async function handleAsk() {
    const question = text.trim();
    if (!question) { setError("Please type a question first."); return; }
    if (loading) return;
    stopVoice();
    setText(""); // clear the box as soon as the question is sent
    setLoading(true); setError(null); setResult(null);
    try {
      const answer = await createQuestion(question);
      setResult(answer);
      try {
        const prev = JSON.parse(localStorage.getItem("ce-conversations") || "[]");
        const item = { id: String(Date.now()), text: question };
        localStorage.setItem("ce-conversations", JSON.stringify([item, ...prev].slice(0, 20)));
        window.dispatchEvent(new Event("ce:conversations"));
      } catch {}
      try {
        if (answer.answer.escalation_required) {
          const queries = JSON.parse(localStorage.getItem("ce-queries") || "[]");
          if (!queries.some((x: { question: string }) => x.question === question)) {
            queries.unshift({
              id: `EQ-${Date.now().toString().slice(-4)}`,
              question,
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
      setText(question); // keep the question so it can be sent again
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  function toggleVoice() {
    if (voice === "recording") { recognitionRef.current?.stop(); return; }
    setVoiceNote(null);
    const Ctor = (window as unknown as { SpeechRecognition?: SpeechRecognitionCtor; webkitSpeechRecognition?: SpeechRecognitionCtor });
    const Recognition = Ctor.SpeechRecognition || Ctor.webkitSpeechRecognition;
    if (!Recognition) {
      setVoiceNote("Voice input is not supported in this browser. Please use Chrome or Edge.");
      return;
    }
    const recognition = new Recognition();
    recognition.lang = "en-IN";
    recognition.continuous = true;
    recognition.interimResults = true;
    baseTextRef.current = text.trim();
    recognition.onresult = (e) => {
      let spoken = "";
      for (let i = 0; i < e.results.length; i++) spoken += e.results[i][0].transcript;
      const base = baseTextRef.current;
      setText(base ? `${base} ${spoken.trim()}` : spoken.trim());
    };
    recognition.onerror = (e) => {
      const messages: Record<string, string> = {
        "not-allowed": "Microphone access was blocked. Allow it in the browser address bar and try again.",
        "service-not-allowed": "Microphone access was blocked. Allow it in the browser address bar and try again.",
        "no-speech": "Didn't catch that. Please try again.",
        "audio-capture": "No microphone was found.",
        network: "Voice input needs an internet connection.",
      };
      if (e.error !== "aborted") setVoiceNote(messages[e.error] ?? "Voice input stopped unexpectedly.");
    };
    recognition.onend = () => { setVoice("idle"); recognitionRef.current = null; };
    recognitionRef.current = recognition;
    try {
      recognition.start();
      setVoice("recording");
    } catch {
      setVoiceNote("Could not start the microphone. Please try again.");
    }
  }

  useEffect(() => () => { recognitionRef.current?.abort(); }, []);

  function onKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleAsk(); }
  }

  return (
    <div className="assistant-page">

      <div className="assistant-body">
        {!result && !error && (
          <div className="empty-state">
            <div className="empty-icon"><span className="material-symbols-outlined">auto_stories</span></div>
            {firstName && <div className="eyebrow">Hello, {firstName}</div>}
            <h2>What are you <em>editing</em> today?</h2>
            <p>Ask a style question, paste a sentence, or request an author query. Answers come from the team's stored rules.</p>
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
            <div className="user-row">
              <div className="user-bubble-wrap">
                <div className="user-meta label-code">{firstName || "You"} &nbsp;•&nbsp; Today</div>
                <div className="user-bubble">&ldquo;{result.question_text}&rdquo;</div>
              </div>
              <div className="user-avatar">{(firstName[0] || "U").toUpperCase()}</div>
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
            <span className="docked-hint">
              {voiceNote ? <span className="voice-note">{voiceNote}</span>
                : voice === "recording" ? <span className="voice-note listening">Listening… tap the mic to stop</span>
                : <><span className="material-symbols-outlined">add</span>Shift + Enter for a new line</>}
            </span>
            <div className="docked-actions">
              <button
                className={`mic-btn ${voice === "recording" ? "recording" : ""}`}
                type="button"
                onClick={toggleVoice}
                aria-label={voice === "recording" ? "Stop recording" : "Speak your question"}
                title={voice === "recording" ? "Stop recording" : "Speak your question"}
              >
                <span className="material-symbols-outlined">{voice === "recording" ? "stop" : "mic"}</span>
              </button>
            <button className="send-btn" type="button" onClick={handleAsk} disabled={loading} aria-label="Send">
              <span className="material-symbols-outlined">{loading ? "hourglass_empty" : "keyboard_return"}</span>
            </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
