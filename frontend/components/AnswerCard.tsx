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

const FIELD_LABELS: Record<string, string> = {
  rule_text: "rule text",
  action: "action",
  source: "source",
  status: "status",
};

function MatchedAnswer({ answer }: { answer: Answer }) {
  const incomplete = answer.rule_complete === false;
  const confirmed = answer.status === "confirmed";

  return (
    <section className={`answer ${incomplete ? "answer-incomplete" : ""}`}>
      {answer.status_notice && (
        <p className={confirmed ? "notice notice-confirmed" : "notice"}>{answer.status_notice}</p>
      )}

      {incomplete && (
        <>
          <h3 className="incomplete-heading">{answer.incomplete_notice}</h3>
          <p>
            The rule text is shown below as recorded, but the missing information (
            {answer.missing_fields.map((f) => FIELD_LABELS[f] ?? f).join(", ")}) has not been
            provided yet.
          </p>
        </>
      )}

      {answer.condition && (
        <>
          <h3>Applies when</h3>
          <p>{answer.condition}</p>
        </>
      )}

      <h3>{incomplete ? "Rule text (as recorded)" : "Decision"}</h3>
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

      <h3>Example</h3>
      {answer.examples.length === 0 ? (
        <p>No example has been added yet.</p>
      ) : (
        <ul className="examples">
          {answer.examples.map((example, index) => (
            <li key={index}>
              <p>
                <strong>Question:</strong> {example.input_text}
              </p>
              <p>
                <strong>Correct handling:</strong> {example.correct_output}
              </p>
              {example.explanation && (
                <p>
                  <strong>Explanation:</strong> {example.explanation}
                </p>
              )}
            </li>
          ))}
        </ul>
      )}

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
