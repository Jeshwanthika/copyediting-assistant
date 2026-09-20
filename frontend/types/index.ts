export interface Rule {
  id: number;
  rule_code: string;
  category: string;
  topic: string;
  question_pattern: string | null;
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
  exception: string | null;
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
