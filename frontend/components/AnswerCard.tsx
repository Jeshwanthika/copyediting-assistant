import type { Answer } from "@/types";

export default function AnswerCard({answer}:{answer:Answer}){
  if(answer.match_status==="no_match") return <div className="answer-row"><div className="assistant-avatar"><span className="material-symbols-outlined">smart_toy</span></div><article className="answer-card"><div className="answer-body"><div className="answer-section"><div className="answer-label">Editorial decision</div><p className="answer-decision">No approved rule matched this question with sufficient confidence.</p></div><div className="info-box"><span className="material-symbols-outlined">info</span><div><strong>Next action</strong><p>Check the style manual or raise the question with a lead.</p></div></div></div></article></div>;
  if(answer.match_status==="ambiguous") return <div className="answer-row"><div className="assistant-avatar"><span className="material-symbols-outlined">smart_toy</span></div><article className="answer-card"><div className="answer-taxonomy"><div className="tax-left"><span className="tax-pill label-code"><span className="material-symbols-outlined" style={{fontSize:14,color:'var(--primary)'}}>warning</span> MULTIPLE RULES</span></div></div><div className="answer-body"><div className="answer-section"><div className="answer-label">Editorial decision</div><p className="answer-decision">Multiple approved rules may apply.</p></div><p>Please review the candidate rules below or raise the question with a lead.</p>{answer.candidates.map(c=><div className="info-box" key={c.rule_code}><span className="material-symbols-outlined">menu_book</span><div><strong>{c.rule_code} — {c.topic}</strong><p>{c.rule_text}</p></div></div>)}<Escalation reason="The rule engine could not determine one sufficiently clear match."/></div></article></div>;
  const confirmed=answer.status==="confirmed";
  const incomplete=answer.rule_complete===false;
  return <div className="answer-row">
    <div className="assistant-avatar"><span className="material-symbols-outlined">smart_toy</span></div>
    <article className="answer-card">
      <div className="answer-taxonomy"><div className="tax-left">
        <span className="tax-pill label-code"><span className="material-symbols-outlined" style={{fontSize:14,color:'var(--primary)'}}>verified</span> Matched Rule: {answer.rule_code}</span>
        <span className={`tax-pill label-code ${confirmed?'confirmed-pill':''}`}>{confirmed?"Confirmed Policy":(answer.status||"Draft")}</span>
      </div><div className="match label-code"><span className="match-dot" /> {Math.round(answer.confidence*100)}% Semantic Match</div></div>
      <div className="answer-body">
        {answer.status_notice && <div className={`info-box ${confirmed?'':''}`}><span className="material-symbols-outlined">verified</span><div><strong>{answer.status_notice}</strong></div></div>}
        {incomplete && <div className="info-box"><span className="material-symbols-outlined">warning</span><div><strong>{answer.incomplete_notice || "Guidance found, but this rule is incomplete."}</strong><p>Missing: {answer.missing_fields.join(", ") || "additional rule details"}.</p></div></div>}
        <div className="answer-section"><div className="answer-label">Editorial decision</div><p className="answer-decision">{answer.decision}</p></div>
        <div><div className="answer-label" style={{color:'var(--on-surface)'}}>Immediate operational action</div><div className="info-box" style={{marginTop:6}}><span className="material-symbols-outlined">task_alt</span><p>{answer.action}</p></div></div>
        {answer.exception && <div><div className="answer-label" style={{color:'var(--on-surface)'}}>Exception</div><p style={{marginTop:6}}>{answer.exception}</p></div>}
        <div><div className="answer-label" style={{color:'var(--on-surface)'}}>Scholarly &amp; ethical rationale</div><p style={{marginTop:6,color:'var(--on-surface-variant)'}}>{answer.reason}</p></div>
        {answer.examples.length>0 && <div><div className="answer-label" style={{color:'var(--on-surface)'}}>Example</div><div className="info-box" style={{marginTop:6}}><span className="material-symbols-outlined">lightbulb</span><div>{answer.examples.map((e,i)=><div key={i}><strong>{e.input_text}</strong><p>{e.correct_output}</p>{e.explanation&&<p>{e.explanation}</p>}</div>)}</div></div></div>}
        {answer.escalation_required && <Escalation reason={answer.escalation_reason || "This question should be checked with a lead."}/>} 
      </div>
      <div className="answer-footer"><div className="label-code">{answer.rule_code} · {answer.source || "Current knowledge base"}</div><div className="footer-actions"><button className="footer-link" type="button"><span className="material-symbols-outlined" style={{fontSize:15}}>thumb_up</span>Helpful</button><button className="footer-link" type="button"><span className="material-symbols-outlined" style={{fontSize:15}}>flag</span>Discrepancy</button><button className="footer-link" type="button"><span className="material-symbols-outlined" style={{fontSize:15}}>content_copy</span>Copy Guidance</button></div></div>
    </article>
  </div>
}
function Escalation({reason}:{reason:string}){return <div className="escalation-box"><div style={{display:'flex',gap:8,alignItems:'flex-start'}}><span className="material-symbols-outlined">priority_high</span><div><strong>Escalation Protocol Required</strong><p style={{color:'var(--on-surface-variant)',fontSize:13}}>{reason}</p></div></div><a className="escalate-btn" href="/queries">Escalate to Lead Query</a></div>}
