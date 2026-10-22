"""Presentation-only report exporters. Never execute uploaded project files."""
from __future__ import annotations
from datetime import datetime, timezone
from html import escape
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether

DISCLAIMER = 'Static AI-assisted inspection only. Uploaded code was not executed; findings require independent verification.'

def _s(value):
    return str(value if value is not None else '')

def _facts(data):
    findings = data.get('findings') or []
    checks = data.get('checks') or []
    return {'critical': sum(_s(x.get('severity')).lower() == 'critical' for x in findings),
            'warning': sum(_s(x.get('severity')).lower() == 'warning' for x in findings),
            'passed': sum(_s(x.get('status')).lower() == 'pass' for x in checks),
            'unverified': sum(_s(x.get('status')).lower() == 'needs verification' for x in checks)}

def to_markdown(data):
    facts = _facts(data)
    lines = ['# AI Code Review Tribunal', '', f"**Mode:** {_s(data.get('mode'))}",
             f"**Verdict:** {_s(data.get('verdict'))}", '', _s(data.get('summary')), '',
             '## Review scorecard', '',
             f"- Passed static checks: {facts['passed']}",f"- Critical issues: {facts['critical']}",
             f"- Warnings: {facts['warning']}",f"- Needs verification: {facts['unverified']}", '',
             '## Findings', '']
    findings = data.get('findings') or []
    if not findings: lines.append('No confirmed issues were identified in this static review.')
    for i, f in enumerate(findings, 1):
        lines.extend([f"### {i}. {_s(f.get('title'))}",
            f"- Severity: {_s(f.get('severity'))}", f"- File: {_s(f.get('file') or 'Not cited')}",
            f"- Line: {_s(f.get('line') or 'Not cited')}", f"- Evidence: {_s(f.get('evidence'))}",
            f"- Reference status: {_s(f.get('reference_status') or 'Not validated')}",
            f"- Recommended correction: {_s(f.get('recommendation'))}", ''])
    lines.extend(['## Verification checks', ''])
    for c in data.get('checks') or []:
        lines.extend([f"### {_s(c.get('status'))}: {_s(c.get('check'))}",
            f"- Agent: {_s(c.get('agent'))}", f"- Source: {_s(c.get('file') or 'Not cited')}:{_s(c.get('line') or '-')}",
            f"- Evidence: {_s(c.get('evidence'))}", f"- Reference status: {_s(c.get('reference_status') or 'Not validated')}", ''])
    lines.extend(['## Agent hand-offs',''])
    for e in data.get('events') or []: lines.append(f"- **{_s(e.get('agent'))}**: {_s(e.get('message'))}")
    lines.extend(['', '---', DISCLAIMER])
    return '\n'.join(lines) + '\n'

def to_html(data):
    facts = _facts(data)
    esc = lambda v: escape(_s(v))
    findings = ''.join(f'<article><span class="severity">{esc(f.get("severity"))}</span><h3>{esc(f.get("title"))}</h3><small>{esc(f.get("file"))} {esc(f.get("line"))}</small><p><b>Evidence:</b> {esc(f.get("evidence"))}</p><p><b>Correction:</b> {esc(f.get("recommendation"))}</p><small>Reference: {esc(f.get("reference_status"))}</small></article>' for f in data.get('findings') or []) or '<p>No confirmed issues identified during static review.</p>'
    checks = ''.join(f'<tr><td>{esc(c.get("status"))}</td><td>{esc(c.get("check"))}</td><td>{esc(c.get("file"))}</td><td>{esc(c.get("evidence"))}</td></tr>' for c in data.get('checks') or [])
    handoffs = ''.join(f'<li><b>{esc(e.get("agent"))}</b> — {esc(e.get("message"))}</li>' for e in data.get('events') or [])
    return f'''<!doctype html><html lang="en-GB"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Tribunal review report</title><style>body{{margin:0;background:#f2f5fb;color:#18243a;font:15px/1.55 system-ui,sans-serif}}main{{max-width:950px;margin:36px auto;background:white;padding:46px;border-radius:20px;box-shadow:0 20px 60px #1c31501c}}h1{{font-size:32px;margin:0}}h2{{margin-top:34px;border-bottom:1px solid #e0e6ef;padding-bottom:10px}}.eyebrow{{color:#5873ac;font-weight:700;letter-spacing:.16em;font-size:11px}}.verdict{{background:#eef3fe;padding:20px;border-radius:12px;margin-top:26px}}.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}}.metric{{background:#f5f7fb;border-radius:12px;padding:17px}}.metric strong{{display:block;font-size:26px}}article{{border:1px solid #dfe5ef;padding:17px;border-radius:12px;margin:12px 0}}.severity{{color:#aa3d43;font-weight:700}}table{{border-collapse:collapse;width:100%;font-size:12px}}td,th{{padding:10px;border:1px solid #e0e6ed;text-align:left;vertical-align:top;word-break:break-word}}small,footer{{color:#687990}}@media print{{body{{background:white}}main{{box-shadow:none;margin:0;padding:15px}}}}@media(max-width:700px){{main{{padding:20px;margin:0}}.grid{{grid-template-columns:repeat(2,1fr)}}}}</style><main><div class="eyebrow">AI CODE REVIEW TRIBUNAL · REVIEW REPORT</div><h1>Review verdict</h1><div class="verdict"><b>{esc(data.get('verdict'))}</b><p>{esc(data.get('summary'))}</p><small>Mode: {esc(data.get('mode'))} · Generated {datetime.now(timezone.utc).strftime('%d %b %Y %H:%M UTC')}</small></div><h2>Scorecard</h2><div class="grid"><div class="metric"><strong>{facts['passed']}</strong>Passed</div><div class="metric"><strong>{facts['critical']}</strong>Critical</div><div class="metric"><strong>{facts['warning']}</strong>Warnings</div><div class="metric"><strong>{facts['unverified']}</strong>Unverified</div></div><h2>Findings</h2>{findings}<h2>Verification checks</h2><table><thead><tr><th>Status</th><th>Check</th><th>File</th><th>Evidence</th></tr></thead><tbody>{checks}</tbody></table><h2>Agent hand-offs</h2><ul>{handoffs}</ul><footer>{esc(DISCLAIMER)}</footer></main></html>'''

def to_pdf(data):
    buf=BytesIO()
    doc=SimpleDocTemplate(buf,pagesize=A4,rightMargin=17*mm,leftMargin=17*mm,topMargin=19*mm,bottomMargin=19*mm, title='AI Code Review Tribunal')
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='TribunalTitle',parent=styles['Title'],fontName='Helvetica-Bold',fontSize=22,leading=27,textColor=colors.HexColor('#1d3559'),spaceAfter=14,alignment=TA_LEFT))
    styles.add(ParagraphStyle(name='TribunalBody',parent=styles['BodyText'],fontSize=9,leading=14,spaceAfter=7,wordWrap='CJK'))
    styles.add(ParagraphStyle(name='TribunalSmall',parent=styles['BodyText'],fontSize=8,leading=12,textColor=colors.HexColor('#56657c'),spaceAfter=5,wordWrap='CJK'))
    styles.add(ParagraphStyle(name='TribunalSection',parent=styles['Heading2'],fontSize=13,leading=17,textColor=colors.HexColor('#284b7f'),spaceBefore=15,spaceAfter=9))
    P=lambda x,style='TribunalBody':Paragraph(escape(_s(x)).replace('\n','<br/>'),styles[style])
    parts=[P('AI CODE REVIEW TRIBUNAL','TribunalSmall'),P('Code Review Report','TribunalTitle'),P('Verdict: '+_s(data.get('verdict'))),P(data.get('summary')), P('Mode: '+_s(data.get('mode')),'TribunalSmall')]
    facts=_facts(data)
    cells=[[P(label,'TribunalSmall') for label in ('Passed checks','Critical','Warnings','Unverified')],[P(str(facts[key])) for key in ('passed','critical','warning','unverified')]]
    table=Table(cells,colWidths=[43*mm]*4, hAlign='LEFT')
    table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#f0f4fc')),('BOX',(0,0),(-1,-1),.4,colors.HexColor('#dae2f0')),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),10)]))
    parts += [Spacer(1,8),table,P('Findings','TribunalSection')]
    if not data.get('findings'):parts.append(P('No confirmed issues were identified during static review.'))
    for i,f in enumerate(data.get('findings') or [],1):
        block=[P(f"{i}. {_s(f.get('title'))} — {_s(f.get('severity'))}"),P('File: '+_s(f.get('file') or 'Not cited')+' | Line: '+_s(f.get('line') or 'Not cited'),'TribunalSmall'),P('Evidence: '+_s(f.get('evidence'))),P('Suggested action: '+_s(f.get('recommendation'))),P('Reference check: '+_s(f.get('reference_status') or 'Not validated'),'TribunalSmall')]
        parts.append(KeepTogether(block))
    parts.append(P('Verification checks','TribunalSection'))
    for c in data.get('checks') or []:
        parts.extend([P(f"{_s(c.get('status'))} — {_s(c.get('check'))}"),P('Source: '+_s(c.get('file') or 'Not cited')+' | Agent: '+_s(c.get('agent')),'TribunalSmall'),P('Evidence: '+_s(c.get('evidence')),'TribunalSmall')])
    parts.append(P('Agent hand-offs','TribunalSection'))
    for e in data.get('events') or []: parts.append(P(_s(e.get('agent'))+': '+_s(e.get('message')),'TribunalSmall'))
    parts.extend([Spacer(1,12),P(DISCLAIMER,'TribunalSmall')])
    def footer(canvas,doc):
        canvas.saveState();canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#66768b'));canvas.drawString(17*mm,12*mm,'AI Code Review Tribunal · Static review');canvas.drawRightString(193*mm,12*mm,f'Page {doc.page}');canvas.restoreState()
    doc.build(parts,onFirstPage=footer,onLaterPages=footer)
    return buf.getvalue()
