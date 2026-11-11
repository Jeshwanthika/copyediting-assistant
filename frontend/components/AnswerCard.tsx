import type { ReactNode } from "react";
import type { Answer } from "@/types";

/**
 * The assistant's reply, kept to the answer itself:
 *   the decision, what to do (if it adds something), an exception or example
 *   only when the rule has one, and a one-line "check with a lead" when needed.
 */
export default function AnswerCard({ answer }: { answer: Answer }) {
  if (answer.match_status === "no_match") {
    return (
      <Reply>
        <p className="reply-text">No rule covers this yet. Check the style manual or ask a lead.</p>
      </Reply>
    );
  }

  if (answer.match_status === "ambiguous") {
    return (
      <Reply>
        <p className="reply-text">More than one rule may apply — please check with a lead:</p>
        <ul className="reply-list">
          {answer.candidates.map((c) => (
            <li key={c.rule_code}>
              <strong>{c.topic}:</strong> {c.rule_text}
            </li>
          ))}
        </ul>
      </Reply>
    );
  }

  const action = answer.action?.trim();
  const showAction = !!action && action !== answer.decision.trim();
  // Incomplete rules already tell the trainee to ask a lead in the action.
  const escalation =
    answer.escalation_required && answer.rule_complete !== false ? leadNote(answer.escalation_reason) : null;

  return (
    <Reply footer={answer.rule_code ? `${answer.rule_code}${answer.status && answer.status !== "confirmed" ? ` · ${answer.status}` : ""}` : null}>
      <p className="reply-text">{answer.decision}</p>
      {showAction && <p className="reply-action">{action}</p>}
      {answer.exception && (
        <p className="reply-extra">
          <strong>Exception:</strong> {answer.exception}
        </p>
      )}
      {answer.examples.length > 0 && (
        <div className="reply-example">
          <span className="reply-example-label">Example</span>
          {answer.examples.map((e, i) => (
            <p key={i}>
              {e.input_text} → <strong>{e.correct_output}</strong>
            </p>
          ))}
        </div>
      )}
      {escalation && (
        <p className="reply-lead">
          <span className="material-symbols-outlined">priority_high</span>
          Check with a lead{escalation === true ? "." : `: ${escalation}`}
        </p>
      )}
    </Reply>
  );
}

/** "The matched rule requires a query/lead confirmation: If X" -> "If X" */
function leadNote(reason: string | null): string | true {
  if (!reason) return true;
  const i = reason.indexOf(": ");
  return i >= 0 ? reason.slice(i + 2) : true;
}

function Reply({ children, footer }: { children: ReactNode; footer?: string | null }) {
  return (
    <div className="answer-row">
      <div className="assistant-avatar">
        <span className="material-symbols-outlined">smart_toy</span>
      </div>
      <article className="answer-card reply">
        {children}
        {footer && <div className="reply-footer">{footer}</div>}
      </article>
    </div>
  );
}
