import type {
  ExampleInput,
  ExampleItem,
  QuestionAnswer,
  Rule,
  RuleReviewDetail,
  RuleReviewSummary,
  RuleUpdate,
} from "@/types";

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
    throw new Error(await errorMessage(response));
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

/** Use the backend's explanation when it gave one (e.g. "An incomplete rule cannot be confirmed"). */
async function errorMessage(response: Response): Promise<string> {
  try {
    const body = await response.json();
    if (typeof body.detail === "string") return body.detail;
    if (Array.isArray(body.detail)) {
      return body.detail
        .map((d: { loc?: (string | number)[]; msg: string }) =>
          `${(d.loc ?? []).slice(1).join(".")}: ${d.msg}`.replace(/^: /, ""),
        )
        .join("; ");
    }
  } catch {
    // not JSON - fall through
  }
  return `Backend returned an error (HTTP ${response.status}).`;
}

const JSON_HEADERS = { "Content-Type": "application/json" };

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

export function getRuleReviews(): Promise<RuleReviewSummary[]> {
  return request<RuleReviewSummary[]>("/rules/review");
}

export function getRuleReview(ruleId: number): Promise<RuleReviewDetail> {
  return request<RuleReviewDetail>(`/rules/${ruleId}/review`);
}

export function updateRule(ruleId: number, update: RuleUpdate): Promise<RuleReviewDetail> {
  return request<RuleReviewDetail>(`/rules/${ruleId}`, {
    method: "PATCH",
    headers: JSON_HEADERS,
    body: JSON.stringify(update),
  });
}

export function addExample(ruleId: number, example: ExampleInput): Promise<ExampleItem> {
  return request<ExampleItem>(`/rules/${ruleId}/examples`, {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify(example),
  });
}

export function deleteExample(ruleId: number, exampleId: number): Promise<void> {
  return request<void>(`/rules/${ruleId}/examples/${exampleId}`, { method: "DELETE" });
}
