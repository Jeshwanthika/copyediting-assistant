import type { QuestionAnswer, Rule } from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/** Turn a failed response or network error into a readable Error. */
async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, init);
  } catch {
    throw new Error(`Cannot reach the backend at ${API_BASE}. Is it running?`);
  }
  if (!response.ok) {
    throw new Error(`Backend returned an error (HTTP ${response.status}).`);
  }
  return response.json() as Promise<T>;
}

export function getRules(): Promise<Rule[]> {
  return request<Rule[]>("/rules");
}

export function createQuestion(questionText: string): Promise<QuestionAnswer> {
  return request<QuestionAnswer>("/questions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question_text: questionText }),
  });
}
