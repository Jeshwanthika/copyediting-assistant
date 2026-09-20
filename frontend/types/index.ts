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
