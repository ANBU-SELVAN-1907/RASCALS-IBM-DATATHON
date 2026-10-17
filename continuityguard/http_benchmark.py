"""Real local HTTP/queue/journal integration benchmark with synthetic fixtures.

Uses an isolated temporary app, port and state; never resets the demo server.
Client and server share the LinuxONE VM. No browser/network-WAN claim follows.
"""
from pathlib import Path
import json
import os
import platform
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
import urllib.error
import numpy as np
from .simulation import Experiment,simulate

def main(root,duration=10):
    root=Path(root).resolve()
    assert 1<=duration<=30
    with tempfile.TemporaryDirectory() as temp:
        state=Path(temp)
        with socket.socket() as probe:
            probe.bind(('127.0.0.1',0))
            port=probe.getsockname()[1]
        env=dict(os.environ,CG_PROJECT_ROOT=str(root),CG_STATE_DIR=str(state),CG_TOKEN_FILE=str(state/'token'),CG_PORT=str(port),CG_AUTOSTART='0')
        with (state/'server.log').open('w') as log:
            server=subprocess.Popen([sys.executable,'-m','continuityguard.web'],cwd=root,env=env,stdout=log,stderr=log)
            base=f'http://127.0.0.1:{port}/api/'
            def call(path,data=None,token=None):
                headers={'Content-Type':'application/json','X-ContinuityGuard':'operator'}
                if token:headers['Authorization']='Bearer '+token
                request=urllib.request.Request(base+path,data=json.dumps(data).encode() if data is not None else None,headers=headers)
                with urllib.request.urlopen(request,timeout=15) as response:return json.load(response)
            try:
                for _ in range(100):
                    if server.poll() is not None:raise RuntimeError((state/'server.log').read_text()[-2000:])
                    try:call('health');break
                    except (OSError,urllib.error.URLError):time.sleep(.1)
                else:raise RuntimeError('HTTP benchmark server did not become ready')
                token=(state/'token').read_text().strip()
                unauthorized=False
                try:call('state')
                except urllib.error.HTTPError as exc:unauthorized=exc.code==401
                trials=[]
                for rate in (10,50,100):
                    call('external-session',{},token)
                    events,_=simulate(Experiment('pool_exhaustion',881,seconds=1200,strength=1.12))
                    count=rate*duration
                    ack_ms=[];queued=backpressure=0
                    started=time.perf_counter()
                    for i in range(0,count,4):
                        due=started+i/rate
                        if due>time.perf_counter():time.sleep(due-time.perf_counter())
                        before=time.perf_counter()
                        try:
                            result=call('events',{'events':events[i:i+4]},token)
                            queued+=result['accepted_into_queue']
                            ack_ms.append((time.perf_counter()-before)*1000)
                        except urllib.error.HTTPError as exc:
                            if exc.code!=429:raise
                            backpressure+=min(4,count-i)
                    while time.perf_counter()-started<duration:time.sleep(.005)
                    enqueue_elapsed=time.perf_counter()-started
                    deadline=time.perf_counter()+15
                    snapshot=call('state',token=token)
                    while snapshot['accepted']+snapshot['rejected']<queued and time.perf_counter()<deadline and snapshot['failed_batches']==0:
                        time.sleep(.02);snapshot=call('state',token=token)
                    elapsed=time.perf_counter()-started
                    trial={'offered_events_per_second':rate,'offered_events':count,'queued_events':queued,'http_backpressure_events':backpressure,'processed_events':snapshot['accepted'],'rejected_processing_events':snapshot['rejected'],'duplicates':snapshot['duplicates'],'failed_batches':snapshot['failed_batches'],'enqueue_seconds':round(enqueue_elapsed,3),'through_final_processing_confirmation_seconds':round(elapsed,3),'processed_events_per_second':round(snapshot['accepted']/elapsed,2),'p95_http_queue_ack_ms':round(float(np.percentile(ack_ms,95)),3),'p95_engine_batch_ms':snapshot['latency_p95_ms'],'audit':call('audit',token=token)}
                    assert trial['processed_events']==queued and not trial['failed_batches'] and not trial['rejected_processing_events'],trial
                    trials.append(trial)
                    print(json.dumps(trial),flush=True)
                result={'architecture':platform.machine(),'duration_seconds_per_trial':duration,'batch_size':4,'scope':'Actual authenticated HTTP ingestion, bounded queue, model inference and SQLite journal on LinuxONE; controlled synthetic fixtures submitted in isolated external mode. Client and server share VM; GenAI off.','latency_boundaries':{'http_queue_ack':'Client request through validation and enqueue; excludes later inference.','engine_batch':'Feature extraction through SQLite commit; excludes queue wait.','completion':'First request through final processed-count confirmation, including polling overhead. No event end-to-end p95 or browser latency is claimed.'},'unauthenticated_access_rejected':unauthorized,'trials':trials}
                (root/'artifacts/http-benchmark.json').write_text(json.dumps(result,indent=2))
                return result
            finally:
                server.terminate()
                try:server.wait(timeout=15)
                except subprocess.TimeoutExpired:server.kill();server.wait()
