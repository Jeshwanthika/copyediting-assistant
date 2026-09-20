"use client";

import { useEffect, useState } from "react";
import { getRules } from "@/lib/api";
import type { Rule } from "@/types";

export default function RuleList() {
  const [rules, setRules] = useState<Rule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getRules()
      .then(setRules)
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Something went wrong."))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p>Loading rules...</p>;
  if (error) return <p className="error">{error}</p>;
  if (rules.length === 0) return <p>No rules found. Run the seed script (see README).</p>;

  return (
    <table>
      <thead>
        <tr>
          <th>Code</th>
          <th>Topic</th>
          <th>Rule</th>
          <th>Escalation</th>
          <th>Source</th>
          <th>Status</th>
          <th>Version</th>
        </tr>
      </thead>
      <tbody>
        {rules.map((rule) => (
          <tr key={rule.id}>
            <td>{rule.rule_code}</td>
            <td>{rule.topic}</td>
            <td>{rule.rule_text}</td>
            <td>{rule.escalation ?? "None stated"}</td>
            <td>{rule.source}</td>
            <td>
              <span className={`badge ${rule.status}`}>{rule.status}</span>
            </td>
            <td>{rule.version}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
