import type { Answer } from "@/types";

export default function AnswerCard({answer}:{answer:Answer}){
  if(answer.match_status==="no_match") return <div className="answer-row"><div className="assistant-avatar"><span className="material-symbols-outlined">smart_toy</span></div><article className="answer-card"><div className="answer-body"><div className="answer-section"><div className="answer-label">Editorial decision</div><p className="answer-decision">No approved rule matched this question with sufficient confidence.</p></div><div className="info-box"><span className="material-symbols-outlined">info</span><div><strong>Next action</strong><p>Check the style manual or raise the question with a lead.</p></div></div></div></article></div>;
  if(answer.match_status==="ambiguous") return <div className="answer-row"><div className="assistant-avatar"><span className="material-symbols-outlined">smart_toy</span></div><article className="answer-card"><div className="answer-taxonomy"><div className="tax-left"><span className="tax-pill label-code"><span className="material-symbols-outlined" style={{fontSize:14,color:'var(--primary)'}}>warning</span> MULTIPLE RULES</span></div></div><div className="answer-body"><div className="answer-section"><div className="answer-label">Editorial decision</div><p className="answer-decision">Multiple approved rules may apply.</p></div><p>Please review the candidate rules below or raise the question with a lead.</p>{answer.candidates.map(c=><div className="info-box" key={c.rule_code}><span className="material-symbols-outlined">menu_book</span><div><strong>{c.rule_code} — {c.topic}</strong><p>{c.rule_text}</p></div></div>)}<Escalation reason="The rule engine could not determine one sufficiently clear match."/></div></article></div>;
  return <div className="answer-row">
    <div className="assistant-avatar"><span className="material-symbols-outlined">smart_toy</span></div>
    <article className="answer-card">
      <div className="answer-body">
        <div className="answer-section"><div className="answer-label">Editorial decision</div><p className="answer-decision">{answer.decision}</p></div>
        {answer.examples.length>0 && <div><div className="answer-label" style={{color:'var(--on-surface)'}}>Example</div><div className="info-box" style={{marginTop:6}}><span className="material-symbols-outlined">lightbulb</span><div>{answer.examples.map((e,i)=><div key={i}><strong>{e.input_text}</strong><p>{e.correct_output}</p>{e.explanation&&<p>{e.explanation}</p>}</div>)}</div></div></div>}
      </div>
    </article>
  </div>
}
function Escalation({reason}:{reason:string}){return <div className="escalation-box"><div style={{display:'flex',gap:8,alignItems:'flex-start'}}><span className="material-symbols-outlined">priority_high</span><div><strong>Escalation Protocol Required</strong><p style={{color:'var(--on-surface-variant)',fontSize:13}}>{reason}</p></div></div><a className="escalate-btn" href="/queries">Escalate to Lead Query</a></div>}
