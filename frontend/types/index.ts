export type RuleStatus = "draft" | "reviewed" | "confirmed" | "superseded";

export interface Rule {
  id: number;
  rule_code: string;
  category: string;
  topic: string;
  question_pattern: string | null;
  condition: string | null;
  rule_text: string;
  action: string | null;
  exception: string | null;
  escalation: string | null;
  source: string;
  source_section: string | null;
  status: string;
  version: number;
  created_at: string;
  updated_at: string;
}

export interface Question {
  id: number;
  question_text: string;
  category: string | null;
  matched_rule_id: number | null;
  created_at: string;
}

export interface MatchedRule {
  rule_id: number;
  rule_code: string;
  topic: string;
  version: number;
}

export interface CandidateRule {
  rule_code: string;
  topic: string;
  rule_text: string;
}

export interface AnswerExample {
  input_text: string;
  correct_output: string;
  explanation: string | null;
}

export interface Answer {
  matched: boolean;
  match_status: "matched" | "no_match" | "ambiguous";
  decision: string;
  action: string;
  reason: string;
  rule_code: string | null;
  rule_topic: string | null;
  source: string | null;
  status: string | null;
  status_notice: string | null;
  rule_complete: boolean | null;
  missing_fields: string[];
  incomplete_notice: string | null;
  condition: string | null;
  exception: string | null;
  examples: AnswerExample[];
  confidence: number;
  matched_terms: string[];
  escalation_required: boolean;
  escalation_reason: string | null;
  candidates: CandidateRule[];
}

export interface QuestionAnswer extends Question {
  question_id: number;
  matched_rule: MatchedRule | null;
  answer: Answer;
}

export interface RuleCompleteness {
  rule_code: string;
  complete: boolean;
  missing_fields: string[];
  has_condition: boolean;
  has_exception: boolean;
  has_escalation: boolean;
  has_source_section: boolean;
  has_example: boolean;
  example_count: number;
}

export interface RuleReviewSummary {
  rule_id: number;
  rule_code: string;
  topic: string;
  category: string;
  status: RuleStatus;
  version: number;
  complete: boolean;
  missing_fields: string[];
  has_exception: boolean;
  has_escalation: boolean;
  has_example: boolean;
}

export interface ExampleItem {
  id: number;
  rule_id: number;
  input_text: string;
  correct_output: string;
  explanation: string | null;
  created_at: string;
}

export interface RuleReviewDetail {
  rule: Rule;
  completeness: RuleCompleteness;
  examples: ExampleItem[];
  allowed_status_transitions: RuleStatus[];
  status_notice: string;
}

/** The only fields the backend lets a lead change. */
export interface RuleUpdate {
  condition?: string;
  rule_text?: string;
  action?: string;
  exception?: string;
  escalation?: string;
  source?: string;
  source_section?: string;
  status?: RuleStatus;
  version?: number;
}

export interface ExampleInput {
  input_text: string;
  correct_output: string;
  explanation?: string;
}
