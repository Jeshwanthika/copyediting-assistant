"use client";

import { useCallback, useEffect, useState } from "react";
import RuleEditor from "@/components/RuleEditor";
import StatusBadge from "@/components/StatusBadge";
import { getRuleReviews } from "@/lib/api";
import type { RuleReviewSummary } from "@/types";

export default function ReviewDashboard() {
  const [rules, setRules] = useState<RuleReviewSummary[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [onlyIncomplete, setOnlyIncomplete] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    getRuleReviews()
      .then((data) => {
        setRules(data);
        setError(null);
      })
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Something went wrong."))
      .finally(() => setLoading(false));
  }, []);

  useEffect(load, [load]);

  if (loading) return <p>Loading rules...</p>;
  if (error) return <p className="error">{error}</p>;

  const shown = onlyIncomplete ? rules.filter((r) => !r.complete) : rules;
  const incompleteCount = rules.filter((r) => !r.complete).length;

  return (
    <div className="review-layout">
      <div>
        <p>
          {rules.length - incompleteCount} of {rules.length} rules complete.{" "}
          <label>
            <input
              type="checkbox"
              checked={onlyIncomplete}
              onChange={(e) => setOnlyIncomplete(e.target.checked)}
            />{" "}
            Show incomplete only
          </label>
        </p>
        <table>
          <thead>
            <tr>
              <th>Code</th>
              <th>Topic</th>
              <th>Status</th>
              <th>Complete?</th>
              <th>Missing</th>
            </tr>
          </thead>
          <tbody>
            {shown.map((rule) => (
              <tr
                key={rule.rule_id}
                className={rule.rule_id === selectedId ? "selected" : "clickable"}
                onClick={() => setSelectedId(rule.rule_id)}
              >
                <td>
                  <button className="link" onClick={() => setSelectedId(rule.rule_id)}>
                    {rule.rule_code}
                  </button>
                </td>
                <td>{rule.topic}</td>
                <td>
                  <StatusBadge status={rule.status} />
                </td>
                <td>
                  <span className={rule.complete ? "badge complete" : "badge incomplete"}>
                    {rule.complete ? "Complete" : "Incomplete"}
                  </span>
                </td>
                <td>{rule.missing_fields.join(", ") || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div>
        {selectedId === null ? (
          <p>Select a rule to inspect and edit it.</p>
        ) : (
          <RuleEditor key={selectedId} ruleId={selectedId} onSaved={load} />
        )}
      </div>
    </div>
  );
}
