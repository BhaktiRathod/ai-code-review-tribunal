import React from 'react';
import {Download, FileText, Globe2, FileCode2, CheckCircle2, Clock3, ShieldAlert} from 'lucide-react';

export function ReportExports({onExport,disabled=false}){
 return <div className="report-exports" aria-label="Download review report">
  <button type="button" className="export export-primary" disabled={disabled} onClick={()=>onExport('pdf')}><FileText size={17}/> Download PDF</button>
  <button type="button" className="export" disabled={disabled} onClick={()=>onExport('html')}><Globe2 size={16}/> HTML</button>
  <button type="button" className="export" disabled={disabled} onClick={()=>onExport('md')}><FileCode2 size={16}/> Markdown</button>
 </div>;
}
export function ReviewSummary({result,counts}){
 const checks=result.checks||[];
 const passed=checks.filter(c=>(c.status||'').toLowerCase()==='pass').length;
 const unverified=checks.filter(c=>(c.status||'').toLowerCase()==='needs verification').length;
 return <div className="summary-grid" aria-label="Review overview">
  <div className="summary-card success"><div className="summary-label"><CheckCircle2 size={17}/> Passed checks</div><strong>{passed}</strong><small>Static verification</small></div>
  <div className="summary-card danger"><div className="summary-label"><ShieldAlert size={17}/> Critical issues</div><strong>{counts.critical}</strong><small>Action recommended</small></div>
  <div className="summary-card warning"><div className="summary-label"><ShieldAlert size={17}/> Warnings</div><strong>{counts.warning}</strong><small>Review recommended</small></div>
  <div className="summary-card neutral"><div className="summary-label"><Clock3 size={17}/> Needs verification</div><strong>{unverified}</strong><small>Not confirmed by execution</small></div>
 </div>;
}
