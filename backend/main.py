from __future__ import annotations
import os
import threading
import uuid
import time
from pathlib import PurePosixPath
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import Response
from reporting import to_pdf, to_html, to_markdown
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from file_reader import read_zip, prepare_context, MAX_UPLOAD
from engine import run_review, run_sample

load_dotenv()
app = FastAPI(title='AI Code Review Tribunal',version='0.6.0')
app.add_middleware(CORSMiddleware,allow_origins=[x.strip() for x in os.getenv('CORS_ORIGINS','http://localhost:5173').split(',')],allow_credentials=False,allow_methods=['GET','POST'],allow_headers=['*'])
POOL=ThreadPoolExecutor(max_workers=2)
JOBS={}
LOCK=threading.Lock()

def trim_jobs():
    if len(JOBS)>100:
        for key in list(JOBS)[:-50]:
            JOBS.pop(key,None)

@app.get('/api/health')
def health():
    return {'status':'ok','live_available':bool(os.getenv('GEMINI_API_KEY','').strip()),'orchestrator':'CrewAI'}

STAGES = [
 ('upload','ZIP uploaded'), ('files','Project files read'), ('readme','README read'),
 ('ctks','CTKS / specification read'), ('requirements','Requirements review'),
 ('code','Code review'), ('documentation','README review'),
 ('evaluation','Evaluation review'), ('judge','Chief Judge verdict'),
 ('recheck','Evidence recheck'), ('report','Report prepared')]

def worker(job_id, files, specification, mode):
    stage_started={}
    def update(key, status='done', detail=''):
        if status == 'running':
            stage_started[key] = time.monotonic()
        elapsed = round(time.monotonic() - stage_started[key], 2) if key in stage_started and status in ('done','failed') else None
        with LOCK:
            job=JOBS.get(job_id)
            if job is not None:
                job['steps'][key]={'status':status,'detail':detail,'duration_s':elapsed}
                job['last_event']={'step':key,'status':status,'detail':detail}
    try:
        update('files',detail=f'{len(files)} readable project files')
        readmes=[name for name in files if PurePosixPath(name).name.casefold() in {'readme.md','readme.txt','readme.rst'}]
        update('readme', 'done' if readmes else 'skipped', ('Found: '+', '.join(readmes[:3])) if readmes else 'No README found in readable ZIP files')
        update('ctks','done' if specification.strip() else 'skipped', 'Requirements received' if specification.strip() else 'No CTKS supplied; alignment cannot be confirmed')
        if mode=='sample':
            for key in ('requirements','code','documentation','evaluation'):
                update(key,'running','Running predefined sample checks')
            result=run_sample(files)
            for key in ('requirements','code','documentation','evaluation','judge','recheck'):
                update(key,'done' if key!='recheck' else 'skipped','Sample simulation, not live Gemini analysis')
        else:
            def progress(role, status, detail):
                mapping={'Requirements':'requirements','Code':'code','README':'documentation','Evaluation':'evaluation','Chief Judge':'judge','Evidence Recheck':'recheck'}
                update(mapping.get(role,role),status,detail)
            result=run_review(prepare_context(files,specification), files, progress)
        result['files_reviewed']=list(files)
        result['file_inventory']={'readme':readmes,'source':[n for n in files if PurePosixPath(n).suffix.lower() in ('.py','.java','.js','.jsx','.ts','.tsx')], 'config':[n for n in files if PurePosixPath(n).suffix.lower() in ('.yaml','.yml','.json','.toml','.properties')]}
        result['stage_details']=dict(JOBS[job_id]['steps'])
        update('report',detail='Final report ready for export')
        with LOCK:
            JOBS[job_id]['status']='complete'
            JOBS[job_id]['result']=result
    except Exception as exc:
        with LOCK:
            JOBS[job_id]['status']='failed'
            JOBS[job_id]['error']=str(exc)[:350]
            for key,step in JOBS[job_id]['steps'].items():
                if step['status']=='running': step['status']='failed';step['detail']='Review interrupted'

@app.post('/api/reviews')
async def start_review(project: UploadFile = File(...), specification: str = Form(''), mode: str = Form('sample')):
    if mode not in {'sample','live'}:
        raise HTTPException(400,'Unknown mode')
    if mode=='live' and not os.getenv('GEMINI_API_KEY','').strip():
        raise HTTPException(400,'Live review requires GEMINI_API_KEY on the backend.')
    if not (project.filename or '').lower().endswith('.zip'):
        raise HTTPException(400,'Upload a .zip project archive.')
    raw=await project.read(MAX_UPLOAD+1)
    try:
        files=read_zip(raw)
    except ValueError as e:
        raise HTTPException(400,str(e)) from e
    job_id=str(uuid.uuid4())
    with LOCK:
        trim_jobs()
        JOBS[job_id]={'status':'running','created_at':datetime.now(timezone.utc).isoformat(), 'steps':{key:{'status':('done' if key=='upload' else 'pending'),'detail':('ZIP accepted by backend' if key=='upload' else '')} for key,_ in STAGES},'last_event':{'step':'upload','status':'done','detail':'ZIP accepted by backend'}}
    POOL.submit(worker,job_id,files,specification[:16000],mode)
    return {'review_id':job_id,'status':'running','files':list(files),'message':f'ZIP received successfully by FastAPI. {len(files)} readable project files identified.'}

@app.get('/api/reviews/{review_id}')
def get_review(review_id:str):
    with LOCK:
        item=JOBS.get(review_id)
        if not item:
            raise HTTPException(404,'Review not found or expired.')
        return item


@app.get('/api/reviews/{review_id}/export/{format}')
def export_review(review_id: str, format: str):
    """Export an already completed server-side review; never trust client-supplied findings."""
    if format not in {'pdf', 'html', 'md'}:
        raise HTTPException(400, 'Format must be pdf, html or md')
    with LOCK:
        review = JOBS.get(review_id)
        if not review or review.get('status') != 'complete':
            raise HTTPException(404, 'Completed review not found or expired')
        data = review['result']
    generator = {'pdf': to_pdf, 'html': to_html, 'md': to_markdown}[format]
    content = generator(data)
    mimetype = {'pdf': 'application/pdf', 'html': 'text/html; charset=utf-8', 'md': 'text/markdown; charset=utf-8'}[format]
    return Response(content=content, media_type=mimetype, headers={
        'Content-Disposition': f'attachment; filename="tribunal-review.{format}"',
        'X-Content-Type-Options': 'nosniff',
        'Cache-Control': 'no-store',
    })
