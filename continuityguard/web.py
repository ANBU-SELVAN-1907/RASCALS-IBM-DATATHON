"""Authenticated loopback-only prototype API and continuous event processing."""
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Literal
import asyncio
import json
import os
import platform
import secrets
import time
import uuid
import psutil
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, field_validator
from .runtime import Engine
from .simulation import SERVICES, SCENARIOS, Experiment, simulate, paired_response
from .explain import Explainer

class BodyLimit:
    """Bound actual POST bytes, including requests without Content-Length."""
    def __init__(self, app, limit=1_000_000):
        self.app, self.limit = app, limit

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http' or scope['method'] != 'POST':
            return await self.app(scope,receive,send)
        chunks, size = [], 0
        while True:
            message = await receive()
            if message['type'] == 'http.disconnect':
                return
            chunk = message.get('body',b'')
            size += len(chunk)
            if size > self.limit:
                return await JSONResponse({'detail':'Request too large'},413)(scope,receive,send)
            chunks.append(chunk)
            if not message.get('more_body',False):
                break
        body, delivered = b''.join(chunks), False
        async def bounded_receive():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {'type':'http.request','body':body,'more_body':False}
            return await receive()
        await self.app(scope,bounded_receive,send)

class Telemetry(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False, strict=True)
    event_id: str = Field(min_length=1, max_length=120)
    event_time: str = Field(max_length=60)
    service: Literal['database','urgent-results','appointments','batch-reporting']
    requests: int = Field(ge=1, le=100000)
    failures: int = Field(ge=0, le=100000)
    latency_p95_ms: float = Field(ge=0, le=1000000)
    pool_used: float = Field(ge=0, le=1)
    queue_depth: float = Field(ge=0, le=1000000)
    retry_rate: float = Field(ge=0, le=1)
    cpu_used: float = Field(ge=0, le=1)
    memory_used: float = Field(ge=0, le=1)
    source_mode: Literal['synthetic','external'] = 'external'
    deferred_requests: int = Field(default=0, ge=0, le=100000)

    @field_validator('event_time')
    @classmethod
    def valid_time(cls, value):
        stamp = datetime.fromisoformat(value.replace('Z','+00:00'))
        if stamp.tzinfo is None:
            raise ValueError('A timezone is required')
        return value

class Batch(BaseModel):
    events: list[Telemetry] = Field(min_length=1, max_length=128)

class Login(BaseModel):
    token: str = Field(min_length=20, max_length=200)

class Scenario(BaseModel):
    name: Literal['healthy','healthy_surge','healthy_shift','pool_exhaustion','retry_storm','memory_pressure','abrupt_failure']
    seed: int = Field(default=101, ge=1, le=1000000)
    speed: Literal[1,4] = 4

class IncidentRequest(BaseModel):
    incident_id: str = Field(min_length=1, max_length=30)

class Service:
    def __init__(self, root, token_file, state_dir):
        self.root = root
        self.engine = Engine(root/'artifacts', str(state_dir/'events.sqlite'))
        self.explainer = Explainer(os.environ.get('CG_GRANITE_MODEL','/home/ibm-user/granite-4.0-h-350m-base-be.f16.gguf'), self.engine.journal)
        self.sessions = {}
        self.token = token_file.read_text().strip()
        self.queue = asyncio.Queue(maxsize=128)
        self.rejected_batches = 0
        self.generation = 0
        self.running = False
        self.scenario = 'healthy'
        self.speed = 1
        self.second = 0
        self.spec = None
        self.producer = None
        self.consumer = None
        self.base = None
        self.mode = 'external'
        self.transition = asyncio.Lock()
        self.processing_error = None
        self.failed_batches = 0

    async def consume(self):
        while True:
            generation, batch = await self.queue.get()
            try:
                if generation == self.generation:
                    try:
                        await asyncio.to_thread(self.engine.ingest, batch)
                        self.processing_error = None
                    except Exception as exc:
                        self.processing_error = type(exc).__name__
                        self.failed_batches += 1
            finally:
                self.queue.task_done()

    async def stop_producer(self):
        if self.producer:
            self.producer.cancel()
            try:
                await self.producer
            except asyncio.CancelledError:
                pass
        await self.queue.join()

    async def external(self):
        async with self.transition:
            self.mode = 'transition'
            await self.stop_producer()
            self.generation += 1
            self.engine.reset()
            self.mode, self.scenario = 'external','external'
            self.spec, self.base, self.producer = None,None,None
            self.second, self.running = 0,False
            self.engine.journal.append('external_session_started',{'scope':'unvalidated external distribution; no paired simulator actions'})

    async def start(self, params):
        async with self.transition:
            await self._start(params)

    async def _start(self, params):
        self.mode = 'transition'
        await self.stop_producer()
        self.generation += 1
        self.engine.reset()
        self.scenario, self.speed = params.name, params.speed
        self.mode = 'synthetic'
        self.spec = Experiment(params.name, params.seed, strength=1.12)
        self.base = datetime.now(timezone.utc)
        self.second = 0
        self.running = True
        self.engine.journal.append('scenario_started', {'scenario':params.name,'seed':params.seed,'speed':params.speed,'scope':'synthetic sandbox','strength':1.12})
        self.producer = asyncio.create_task(self.produce(self.generation))

    async def produce(self, generation):
        events, _ = simulate(self.spec)
        run_id = uuid.uuid4().hex[:8]
        for t in range(self.spec.seconds):
            if generation != self.generation:
                break
            while not self.running:
                await asyncio.sleep(.2)
            batch = []
            for raw in events[t*len(SERVICES):(t+1)*len(SERVICES)]:
                batch.append({**raw, 'event_id':run_id+':'+raw['event_id'], 'event_time':(self.base+timedelta(seconds=t)).isoformat()})
            await self.queue.put((generation,batch))
            self.second = t
            await asyncio.sleep(1/self.speed)
        self.running = False

    def snapshot(self):
        data = self.engine.snapshot()
        data.update({'team':'RASCALS','source_label':'Controlled synthetic service telemetry' if self.mode=='synthetic' else 'External input; model not validated for this distribution','mode':self.mode,'generation':self.generation,'scenario':self.scenario,'second':self.second,'speed':self.speed,'running':self.running,'finished':self.mode=='synthetic' and self.producer is not None and self.producer.done(),'queue_batches':self.queue.qsize(),'queue_capacity':128,'rejected_batches':self.rejected_batches,'failed_batches':self.failed_batches,'processing_error':self.processing_error,'host': {'architecture':platform.machine(),'logical_cpus':psutil.cpu_count(),'cpu_percent':psutil.cpu_percent(),'memory_percent':psutil.virtual_memory().percent}, 'demo_strength':1.12})
        return data

    def incident(self, value):
        with self.engine.lock:
            match = next((i for i in self.engine.incidents if i['id']==value),None)
        if not match:
            raise HTTPException(404, 'Incident not found')
        return match

def create_app(root=None, token_file=None, auto_start=True):
    root = Path(root or os.environ.get('CG_PROJECT_ROOT',Path(__file__).resolve().parents[1])).resolve()
    state_dir=Path(os.environ.get('CG_STATE_DIR',root/'state'))
    state_dir.mkdir(parents=True,exist_ok=True)
    token_file = Path(token_file or os.environ.get('CG_TOKEN_FILE',state_dir/'.access-token'))
    if not token_file.exists():
        token_file.write_text(secrets.token_urlsafe(32))
        token_file.chmod(0o600)

    @asynccontextmanager
    async def lifespan(app):
        service = Service(root,token_file,state_dir)
        app.state.service = service
        service.consumer = asyncio.create_task(service.consume())
        if auto_start:
            await service.start(Scenario(name='healthy',speed=1))
        yield
        if service.producer:
            service.producer.cancel()
            try:
                await service.producer
            except asyncio.CancelledError:
                pass
        await service.queue.join()
        service.consumer.cancel()
        try:
            await service.consumer
        except asyncio.CancelledError:
            pass
        await asyncio.to_thread(service.explainer.close)
        service.engine.close()

    app = FastAPI(title='ContinuityGuard · RASCALS',lifespan=lifespan,docs_url=None,redoc_url=None)
    app.add_middleware(BodyLimit)

    @app.middleware('http')
    async def security(request, call_next):
        if request.method=='POST':
            length = request.headers.get('content-length','0')
            if not length.isdigit() or int(length)>1000000:
                return JSONResponse({'detail':'Request too large'},status_code=413)
            origin = request.headers.get('origin')
            if origin and origin not in {'http://'+request.headers.get('host',''),'https://'+request.headers.get('host','')}:
                return JSONResponse({'detail':'Origin rejected'},status_code=403)
            if request.headers.get('x-continuityguard')!='operator':
                return JSONResponse({'detail':'Operator header required'},status_code=403)
        if request.url.path.startswith('/api/') and request.url.path not in {'/api/login','/api/health'}:
            service = request.app.state.service
            value = request.cookies.get('cg_session') or request.headers.get('authorization','').removeprefix('Bearer ')
            authorized = secrets.compare_digest(value.encode('utf-8'),service.token.encode('utf-8')) if value else False
            authorized = authorized or (value in service.sessions and service.sessions[value] > time.time())
            if not authorized:
                return JSONResponse({'detail':'Login required'},status_code=401)
        response = await call_next(request)
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['Referrer-Policy']='no-referrer'
        response.headers['Cache-Control']='no-store'
        response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'"
        return response

    @app.get('/')
    async def index():
        return FileResponse(Path(__file__).parent/'static'/'index.html')

    @app.get('/api/health')
    async def health(request:Request):
        service=request.app.state.service
        return JSONResponse({'status':'degraded' if service.processing_error else 'ready','architecture':platform.machine(),'model_version':service.engine.bundle.manifest['version']},status_code=503 if service.processing_error else 200)

    @app.post('/api/login')
    async def login(params:Login,request:Request):
        service=request.app.state.service
        if not secrets.compare_digest(params.token.encode('utf-8'),service.token.encode('utf-8')):
            raise HTTPException(401,'Invalid access token')
        service.sessions={k:v for k,v in service.sessions.items() if v>time.time()}
        if len(service.sessions)>=20:
            service.sessions.pop(next(iter(service.sessions)))
        session=secrets.token_urlsafe(32)
        service.sessions[session]=time.time()+28800
        response=JSONResponse({'authenticated':True})
        response.set_cookie('cg_session',session,httponly=True,samesite='strict',max_age=28800)
        return response

    @app.get('/api/state')
    async def state(request:Request):
        return await asyncio.to_thread(request.app.state.service.snapshot)

    @app.get('/api/stream')
    async def stream(request:Request):
        async def events():
            # Periodic reconnect also bounds session authorization lifetime.
            for _ in range(30):
                if await request.is_disconnected():
                    break
                snapshot=await asyncio.to_thread(request.app.state.service.snapshot)
                yield 'data: '+json.dumps(snapshot,allow_nan=False)+'\n\n'
                await asyncio.sleep(1)
        return StreamingResponse(events(),media_type='text/event-stream')

    @app.post('/api/events',status_code=202)
    async def ingest(params:Batch,request:Request):
        service=request.app.state.service
        if service.mode!='external':
            raise HTTPException(409,'Start an external session before ingesting external telemetry')
        batch=[e.model_dump() for e in params.events]
        for event in batch:
            event['source_mode']='external'
            event['deferred_requests']=0
        if any(e['failures']>e['requests'] for e in batch):
            raise HTTPException(422,'Failures cannot exceed requests')
        try:
            service.queue.put_nowait((service.generation,batch))
        except asyncio.QueueFull:
            service.rejected_batches+=1
            raise HTTPException(429,'Bounded ingestion queue is full; retry with backoff')
        return {'accepted_into_queue':len(batch),'queue_batches':service.queue.qsize()}

    @app.post('/api/external-session')
    async def external(request:Request):
        await request.app.state.service.external()
        return {'mode':'external','scope':'Isolated external stream. Forecasts require validation on the deployment distribution.'}

    @app.post('/api/scenario')
    async def scenario(params:Scenario,request:Request):
        await request.app.state.service.start(params)
        return {'started':params.model_dump(),'scope':'synthetic sandbox only'}

    @app.post('/api/pause')
    async def pause(request:Request):
        service=request.app.state.service
        if service.mode!='synthetic' or not service.producer or service.producer.done():
            raise HTTPException(409,'No active replay; start a new scenario')
        service.running=not service.running
        return {'running':service.running}

    @app.post('/api/explain')
    async def explain(params:IncidentRequest,request:Request):
        service=request.app.state.service
        return service.explainer.request(service.incident(params.incident_id))

    @app.get('/api/explanation/{incident_id}')
    async def explanation(incident_id:str,request:Request):
        return request.app.state.service.explainer.status(incident_id)

    @app.post('/api/response-preview')
    async def preview(params:IncidentRequest,request:Request):
        service=request.app.state.service
        incident=service.incident(params.incident_id)
        if not service.spec or incident['source_mode']!='synthetic':
            raise HTTPException(409,'Paired preview requires the controlled simulator')
        action=incident['runbook']['action']
        if action=='none':
            return {'scope':'Operator investigation; no automatic action recommended.'}
        stamp=datetime.fromisoformat(incident['event_time'])
        second=max(0,int((stamp-service.base).total_seconds()))
        result=await asyncio.to_thread(paired_response,service.spec,second,action)
        service.engine.journal.append('paired_response_preview',{'incident_id':incident['id'],**result})
        return result

    @app.get('/api/report')
    async def report():
        return json.loads((root/'artifacts'/'report.json').read_text())

    @app.get('/api/platform-proof')
    async def platform_proof(request:Request):
        service=request.app.state.service
        def read(path):
            try:return Path(path).read_text().strip()
            except OSError:return 'unavailable'
        status={line.split(':',1)[0]:line.split(':',1)[1].strip() for line in read('/proc/self/status').splitlines() if ':' in line}
        return {'project_title':'RASCALS_IBM Z Datathon 2026 Project','architecture':platform.machine(),'python':platform.python_version(),'process_uid':os.getuid() if hasattr(os,'getuid') else None,'cgroup_memory_max':read('/sys/fs/cgroup/memory.max'),'cgroup_cpu_max':read('/sys/fs/cgroup/cpu.max'),'effective_capabilities_hex':status.get('CapEff'),'no_new_privileges':status.get('NoNewPrivs'),'root_filesystem_readonly':bool(os.statvfs('/').f_flag & os.ST_RDONLY) if hasattr(os,'statvfs') else None,'model':service.engine.bundle.manifest,'novelty_estimator':type(service.engine.bundle.state['novelty']).__name__,'granite_model_available':service.explainer.path.is_file(),'platform_scope':'Observed process and container properties; no z/OS or hardware accelerator claim.'}

    @app.get('/api/audit')
    async def audit(request:Request):
        return request.app.state.service.engine.journal.verify()

    app.mount('/static',StaticFiles(directory=Path(__file__).parent/'static'),name='static')
    return app

if __name__=='__main__':
    import uvicorn
    uvicorn.run(create_app(auto_start=os.environ.get('CG_AUTOSTART','1')=='1'),host='127.0.0.1',port=int(os.environ.get('CG_PORT','8080')),log_level='warning',timeout_graceful_shutdown=3)
