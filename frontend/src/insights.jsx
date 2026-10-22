import React from 'react';
import {Activity,ShieldCheck,ShieldAlert,Clock3} from 'lucide-react';
const label = s => (s || '').toLowerCase();
export function VisualInsights({result,steps}) {
  if (!result) return null;
  const checks=result.checks||[];
  const pass=checks.filter(c=>label(c.status)==='pass').length;
  const fail=checks.filter(c=>label(c.status)==='fail').length;
  const unverified=checks.length-pass-fail;
  const total=checks.length;
  const data=[{name:'Passed',value:pass,color:'#5ce1b7'},{name:'Failed',value:fail,color:'#ff7895'},{name:'Unverified / other',value:unverified,color:'#ffc977'}];
  const radius=64, circumference=2*Math.PI*radius;
  let offset=0;
  const arcs=data.filter(d=>d.value>0).map(d=>{const length=total?d.value/total*circumference:0;const arc={...d,length,offset};offset+=length;return arc;});
  const agents=[['Requirements','requirements'],['Code','code'],['README','documentation'],['Evaluation','evaluation'],['Chief Judge','judge']];
  const times=agents.map(([name,key])=>({name,time:Number(steps?.[key]?.duration_s)||0,status:steps?.[key]?.status||'pending'}));
  const max=Math.max(...times.map(t=>t.time),1);
  return <section className="insights-section" aria-label="Review insights">
    <div className="insights-heading"><div><span className="panelkicker">ANALYTICS OVERVIEW</span><h3>Review intelligence</h3></div><span className="insights-pill"><Activity size={14}/> Based on this review</span></div>
    <div className="insights-grid">
      <div className="insight-card chart-card"><div className="insight-title">Verification breakdown</div><div className="chart-layout"><div className="donut-wrap"><svg viewBox="0 0 180 180" role="img" aria-label={`${pass} passed, ${fail} failed, ${unverified} unverified checks`}><circle cx="90" cy="90" r={radius} fill="none" stroke="#28334d" strokeWidth="18"/>{arcs.map(d=><circle key={d.name} cx="90" cy="90" r={radius} fill="none" stroke={d.color} strokeWidth="18" strokeDasharray={`${d.length} ${circumference-d.length}`} strokeDashoffset={-d.offset} transform="rotate(-90 90 90)" />)}<text x="90" y="84" textAnchor="middle" fill="#f5f6ff" fontSize="31" fontWeight="800">{total}</text><text x="90" y="108" textAnchor="middle" fill="#9aa8c7" fontSize="11">CHECKS</text></svg></div><div className="chart-legend">{data.map(d=><div className="legend-line" key={d.name}><span className="legend-dot" style={{background:d.color}}/><span>{d.name}</span><b>{d.value}</b></div>)}</div></div><p className="insight-foot">Static inspection only — checks do not establish runtime success.</p></div>
      <div className="insight-card agent-chart-card"><div className="insight-title">Agent execution times</div><div className="duration-bars">{times.map(t=><div className="duration-row" key={t.name}><span>{t.name}</span><div className="duration-track"><div className="duration-fill" style={{width:`${t.time>0?Math.max(3,t.time/max*100):0}%`}}/></div><b>{t.time>0?`${t.time.toFixed(1)}s`:'—'}</b></div>)}</div><p className="insight-foot">Durations recorded by the backend for each review stage.</p></div>
    </div>
  </section>;
}
