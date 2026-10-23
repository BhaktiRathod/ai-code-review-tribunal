import React, {useMemo,useState} from 'react';
import {ChevronDown, CheckCircle2, AlertTriangle, ShieldAlert, Filter} from 'lucide-react';

const visualStatus = (s) => String(s||'').toLowerCase()==='pass'||String(s||'').toLowerCase()==='static pass'?'Static Pass':String(s||'').toLowerCase()==='fail'?'Fail':'Needs verification';
export function VerificationChecks({checks=[]}){
  const [filter,setFilter]=useState('All');
  const [expanded,setExpanded]=useState({});
  const groups=useMemo(()=>checks.map((c,i)=>({ ...c, status:visualStatus(c.status), id:`${c.check}-${c.file}-${i}` })),[checks]);
  const visible=groups.filter(c=>filter==='All'||c.status===filter);
  return <section className="vchecks" aria-label="Grouped verification checks">
    <header className="vchecks-header"><div><strong>Evidence-led verification</strong><p>Each requirement is shown once, with all contributing agents and disagreements preserved.</p></div><span className="static-pill">Static inspection · Not runtime-tested</span></header>
    <div className="vchecks-filters" aria-label="Filter verification checks"><Filter size={16}/>{['All','Static Pass','Fail','Needs verification'].map(label=><button key={label} type="button" className={filter===label?'filter-active':''} aria-pressed={filter===label} onClick={()=>setFilter(label)}>{label} <span>{label==='All'?groups.length:groups.filter(c=>c.status===label).length}</span></button>)}</div>
    <div className="vchecks-grid">{visible.map(c=><article className={`vcheck ${c.conflict?'vcheck-conflict':''}`} key={c.id}>
      <button type="button" className="vcheck-trigger" aria-expanded={!!expanded[c.id]} onClick={()=>setExpanded(p=>({...p,[c.id]:!p[c.id]}))}>
        <span className={`vcheck-badge ${c.status==='Static Pass'?'static-pass':c.status==='Fail'?'failed':'unverified'}`}>{c.status==='Static Pass'?<CheckCircle2 size={15}/>:c.status==='Fail'?<ShieldAlert size={15}/>:<AlertTriangle size={15}/>} {c.status}</span>
        <span className="vcheck-name"><strong>{c.check}</strong><small>{c.file||'No source file cited'}{c.line?` · Line ${c.line}`:''}</small></span>
        <ChevronDown className={expanded[c.id]?'chevron-open':''} size={19}/>
      </button>
      <div className="vcheck-reviewers"><span>Reviewed by</span>{(c.confirmed_by||[c.agent]).map(a=><span key={a} className="reviewer-chip">{a}</span>)}{c.conflict&&<span className="conflict-chip">Conflicting assessments</span>}</div>
      {expanded[c.id]&&<div className="vcheck-detail"><p><strong>Review evidence</strong> · Source location confirmed does not establish functional correctness.</p>{(c.reviews||[{agent:c.agent,status:c.status,evidence:c.evidence,reference_status:c.reference_status}]).map((r,i)=><div className="vcheck-evidence" key={i}><div><b>{r.agent}</b><span>{r.status}</span></div><p>{r.evidence||'No evidence provided'}</p><small>{r.reference_status||'Source reference not validated'}</small></div>)}</div>}
    </article>)}{visible.length===0&&<p className="vchecks-empty">No checks match this filter.</p>}</div>
  </section>
}
