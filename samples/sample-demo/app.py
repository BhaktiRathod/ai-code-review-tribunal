from fastapi import FastAPI
from prometheus_client import Counter, generate_latest
from starlette.responses import Response
app = FastAPI()
REQUESTS = Counter('http_requests_total','Requests', ['route'])
@app.get('/health')
def health():
    REQUESTS.labels('/health').inc()
    return {'status':'ok'}
@app.get('/metrics')
def metrics():
    return Response(generate_latest(),media_type='text/plain')
