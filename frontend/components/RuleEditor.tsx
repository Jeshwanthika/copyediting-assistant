"use client";

import { useCallback, useEffect, useState } from "react";
import ExampleManager from "@/components/ExampleManager";
import StatusBadge from "@/components/StatusBadge";
import { getRuleReview, updateRule } from "@/lib/api";
import type { RuleReviewDetail, RuleStatus, RuleUpdate } from "@/types";

type FormState = {
  rule_text: string;
  condition: string;
  action: string;
  exception: string;
  escalation: string;
  source: string;
  source_section: string;
  status: RuleStatus;
  version: string;
};

const TEXT_FIELDS: { key: keyof FormState; label: string; multiline: boolean }[] = [
  { key: "rule_text", label: "Rule text", multiline: true },
  { key: "condition", label: "Condition (when it applies)", multiline: true },
  { key: "action", label: "Action", multiline: true },
  { key: "exception", label: "Exception", multiline: true },
  { key: "escalation", label: "Escalation", multiline: true },
  { key: "source", label: "Source", multiline: false },
  { key: "source_section", label: "Source section", multiline: false },
];

function toForm(detail: RuleReviewDetail): FormState {
  const r = detail.rule;
  return {
    rule_text: r.rule_text,
    condition: r.condition ?? "",
    action: r.action ?? "",
    exception: r.exception ?? "",
    escalation: r.escalation ?? "",
    source: r.source,
    source_section: r.source_section ?? "",
    status: r.status as RuleStatus,
    version: String(r.version),
  };
}

export default function RuleEditor({ ruleId, onSaved }: { ruleId: number; onSaved: () => void }) {
  const [detail, setDetail] = useState<RuleReviewDetail | null>(null);
  const [form, setForm] = useState<FormState | null>(null);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const apply = useCallback((data: RuleReviewDetail) => {
    setDetail(data);
    setForm(toForm(data));
  }, []);

  useEffect(() => {
    getRuleReview(ruleId)
      .then(apply)
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Something went wrong."));
  }, [ruleId, apply]);

  if (error && !detail) return <p className="error">{error}</p>;
  if (!detail || !form) return <p>Loading rule...</p>;

  const { rule, completeness } = detail;
  const statusOptions = [rule.status as RuleStatus, ...detail.allowed_status_transitions];

  function changedFields(): RuleUpdate {
    const original = toForm(detail!);
    const update: Record<string, string | number> = {};
    for (const key of Object.keys(form!) as (keyof FormState)[]) {
      if (form![key] !== original[key]) {
        update[key] = key === "version" ? Number(form![key]) : form![key];
      }
    }
    return update as RuleUpdate;
  }

  async function handleSave() {
    const update = changedFields();
    if (Object.keys(update).length === 0) {
      setMessage("Nothing to save.");
      return;
    }
    setSaving(true);
    setError(null);
    setMessage(null);
    try {
      const saved = await updateRule(ruleId, update);
      apply(saved);
      const demoted = !update.status && saved.rule.status !== rule.status;
      setMessage(
        demoted
          ? `Saved. The rule content changed, so its status was set back to ${saved.rule.status.toUpperCase()}. A lead must review it again.`
          : "Saved.",
      );
      onSaved();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="editor">
      <h2>
        {rule.rule_code} — {rule.topic}
      </h2>

      <p className={`status-banner banner-${rule.status}`}>
        <StatusBadge status={rule.status} /> {detail.status_notice}
      </p>

      <p>
        <span className={completeness.complete ? "badge complete" : "badge incomplete"}>
          {completeness.complete ? "Complete" : "Incomplete"}
        </span>{" "}
        {!completeness.complete && <>Missing: {completeness.missing_fields.join(", ")}. </>}
        Exception: {completeness.has_exception ? "yes" : "none"} · Escalation:{" "}
        {completeness.has_escalation ? "yes" : "none"} · Examples: {completeness.example_count}
      </p>

      {TEXT_FIELDS.map(({ key, label, multiline }) => (
        <label key={key} className="field">
          <span>{label}</span>
          {multiline ? (
            <textarea
              rows={3}
              value={form[key]}
              onChange={(e) => setForm({ ...form, [key]: e.target.value })}
            />
          ) : (
            <input
              type="text"
              value={form[key]}
              onChange={(e) => setForm({ ...form, [key]: e.target.value })}
            />
          )}
        </label>
      ))}

      <div className="field-row">
        <label className="field">
          <span>Status</span>
          <select
            value={form.status}
            onChange={(e) => setForm({ ...form, status: e.target.value as RuleStatus })}
          >
            {statusOptions.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          <span>Version</span>
          <input
            type="number"
            min={1}
            value={form.version}
            onChange={(e) => setForm({ ...form, version: e.target.value })}
          />
        </label>
      </div>

      <p className="hint">
        Editing the content of a reviewed or confirmed rule sends it back to draft. Only a lead
        should change the status.
      </p>
      <button onClick={handleSave} disabled={saving}>
        {saving ? "Saving..." : "Save changes"}
      </button>
      {message && <p className="success">{message}</p>}
      {error && <p className="error">{error}</p>}

      <ExampleManager
        ruleId={ruleId}
        examples={detail.examples}
        onChanged={async () => {
          apply(await getRuleReview(ruleId));
          onSaved();
        }}
      />
    </div>
  );
}
