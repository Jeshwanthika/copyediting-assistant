import { clearSession, getToken } from "@/lib/session";
import type {
  DocumentItem,
  DocumentUpdate,
  ExampleInput,
  ExampleItem,
  QuestionAnswer,
  Rule,
  RuleReviewDetail,
  RuleReviewSummary,
  RuleUpdate,
  Session,
  User,
} from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/** fetch() with the login token attached. A 401 means the login is no longer valid. */
async function send(path: string, init: RequestInit = {}): Promise<Response> {
  const headers = new Headers(init.headers);
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, { ...init, headers });
  } catch {
    throw new Error(`Cannot reach the backend at ${API_BASE}. Is it running?`);
  }
  if (response.status === 401 && token && !path.startsWith("/auth/login")) {
    clearSession(); // the app shell sends the user back to the sign-in page
  }
  if (!response.ok) {
    throw new Error(await errorMessage(response));
  }
  return response;
}

/** Turn a failed response or network error into a readable Error. */
async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await send(path, init);
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

// ---------------------------------------------------------------- login

export function login(username: string, password: string): Promise<Session> {
  return request<Session>("/auth/login", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify({ username, password }),
  });
}

export function getMe(): Promise<User> {
  return request<User>("/auth/me");
}

export function changePassword(currentPassword: string, newPassword: string): Promise<void> {
  return request<void>("/auth/change-password", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
  });
}

// ---------------------------------------------------------------- rules

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

// ---------------------------------------------------------------- errors & solutions

export function getDocuments(): Promise<DocumentItem[]> {
  return request<DocumentItem[]>("/documents");
}

/** The PDF as a Blob. Fetched with the token, because an <iframe src> cannot send one. */
export async function getDocumentFile(documentId: number): Promise<Blob> {
  const response = await send(`/documents/${documentId}/file`);
  const blob = await response.blob();
  // Make sure the browser treats it as a PDF even if the type was lost.
  return blob.type === "application/pdf" ? blob : new Blob([blob], { type: "application/pdf" });
}

export function uploadDocument(file: File, title: string, description: string): Promise<DocumentItem> {
  const form = new FormData();
  form.append("file", file);
  form.append("title", title);
  form.append("description", description);
  // No Content-Type header: the browser sets the multipart boundary itself.
  return request<DocumentItem>("/documents", { method: "POST", body: form });
}

export function updateDocument(documentId: number, update: DocumentUpdate): Promise<DocumentItem> {
  return request<DocumentItem>(`/documents/${documentId}`, {
    method: "PATCH",
    headers: JSON_HEADERS,
    body: JSON.stringify(update),
  });
}

export function replaceDocumentFile(documentId: number, file: File): Promise<DocumentItem> {
  const form = new FormData();
  form.append("file", file);
  return request<DocumentItem>(`/documents/${documentId}/file`, { method: "PUT", body: form });
}

export function deleteDocument(documentId: number): Promise<void> {
  return request<void>(`/documents/${documentId}`, { method: "DELETE" });
}
