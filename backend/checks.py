"""Consolidate overlapping specialist checks without concealing disagreements."""
from __future__ import annotations
import re

def _status(value):
    s = str(value or '').strip().casefold()
    return 'Fail' if s in {'fail','failed'} else 'Static Pass' if s in {'pass','static pass'} else 'Needs verification'

def _title(value):
    title = re.sub(r'[^a-z0-9]+', ' ', str(value or '').casefold()).strip()
    # Consolidate frequent linguistic variants for metrics-related checks.
    if 'prometheus' in title and ('counter' in title or 'request count' in title):
        return 'Prometheus counter metrics'
    if ('prometheus' in title or 'request' in title) and ('histogram' in title or 'latency metric' in title):
        return 'Prometheus histogram metrics'
    if 'prometheus' in title and ('scrape' in title or 'target' in title):
        return 'Prometheus scrape configuration'
    return title

def consolidate_checks(checks):
    groups = {}
    for item in checks:
        check = dict(item)
        title = _title(check.get('check'))
        # Do not merge different source files: similarly worded checks can refer to different implementations.
        filename = str(check.get('file') or '').casefold().strip()
        key = (title, filename)
        if key not in groups:
            groups[key] = {'check': title or check.get('check','Unnamed check'), 'file': check.get('file',''),
                'line': check.get('line',0), 'reviews': [], 'confirmed_by': []}
        group = groups[key]
        agent = str(check.get('agent') or 'Unattributed')
        status = _status(check.get('status'))
        # Missing/invalid references cannot be represented as a static pass.
        ref = str(check.get('reference_status') or '')
        if status == 'Static Pass' and (not filename or ref.startswith('unverified')):
            status = 'Needs verification'
        group['reviews'].append({'agent': agent, 'status': status, 'evidence':check.get('evidence',''),
                                 'line':check.get('line',0), 'reference_status':ref})
        if agent not in group['confirmed_by']:
            group['confirmed_by'].append(agent)
    result=[]
    for group in groups.values():
        statuses={r['status'] for r in group['reviews']}
        if len(statuses)>1:
            status='Needs verification'  # Disagreement must not be hidden, even if one agent says Fail.
            conflict=True
        else:
            status=next(iter(statuses))
            conflict=False
        first=group['reviews'][0]
        result.append({**group,'status':status,'conflict':conflict,'agent':', '.join(group['confirmed_by']),
                       'evidence':first['evidence'], 'reference_status':first['reference_status']})
    return result
