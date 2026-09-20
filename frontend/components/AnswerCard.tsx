import { confidenceLabel, sourceLabel } from "@/lib/format";
import type { Answer } from "@/types";

export default function AnswerCard({ answer }: { answer: Answer }) {
  if (answer.match_status === "no_match") return <NoRuleFound />;
  if (answer.match_status === "ambiguous") return <MultipleRules answer={answer} />;
  return <MatchedAnswer answer={answer} />;
}

function NoRuleFound() {
  return (
    <section className="answer answer-none">
      <h3>No matching rule found</h3>
      <p>We could not find a sufficiently relevant rule in the current knowledge base.</p>
      <p>Please check the style manual or raise the question with a lead.</p>
    </section>
  );
}

function MultipleRules({ answer }: { answer: Answer }) {
  return (
    <section className="answer answer-ambiguous">
      <h3>Multiple rules may apply</h3>
      <p>
        We could not tell which rule fits best. Please review the rules below or raise a query
        with a lead.
      </p>
      <ul>
        {answer.candidates.map((rule) => (
          <li key={rule.rule_code}>
            <strong>
              {rule.rule_code} — {rule.topic}
            </strong>
            <br />
            {rule.rule_text}
          </li>
        ))}
      </ul>
      <p className="escalation">Raise a query / check with a lead.</p>
    </section>
  );
}

function MatchedAnswer({ answer }: { answer: Answer }) {
  return (
    <section className="answer">
      {answer.status_notice && <p className="notice">{answer.status_notice}</p>}

      <h3>Decision</h3>
      <p>{answer.decision}</p>

      <h3>Action</h3>
      <p>{answer.action}</p>

      {answer.exception && (
        <>
          <h3>Exception</h3>
          <p>{answer.exception}</p>
        </>
      )}

      <h3>Why</h3>
      <p>{answer.reason}</p>

      <h3>Source</h3>
      <p>
        {answer.source && sourceLabel(answer.source, answer.status)}
        {answer.rule_code && ` (${answer.rule_code}: ${answer.rule_topic})`}
      </p>

      <h3>Confidence</h3>
      <p>{confidenceLabel(answer.confidence)}</p>

      <h3>Escalation</h3>
      {answer.escalation_required ? (
        <>
          <p className="escalation">Raise a query / check with a lead.</p>
          {answer.escalation_reason && <p>{answer.escalation_reason}</p>}
        </>
      ) : (
        <p>No escalation indicated by this rule.</p>
      )}
    </section>
  );
}
