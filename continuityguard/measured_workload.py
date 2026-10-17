"""Original measured localhost service experiment, separate from simulator data.

All timings/counters are observed. A bounded SHA-256 workload changes real
request computation; no latency values or health outcomes are invented.
"""
from pathlib import Path
from datetime import datetime,timezone
from http.server import HTTPServer,BaseHTTPRequestHandler
import csv
import hashlib
import json
import multiprocessing as mp
import platform
import tempfile
import time
import urllib.request
import numpy as np
import psutil
from sklearn.ensemble import IsolationForest
import joblib

def serve(port_queue,pressure):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path!='/probe':self.send_error(404);return
            value=b'continuityguard-bounded-real-compute'
            for _ in range(180000 if pressure.value else 250):
                value=hashlib.sha256(value).digest()
            self.send_response(200);self.send_header('Content-Type','application/octet-stream');self.send_header('Content-Length',str(len(value)));self.end_headers();self.wfile.write(value)
        def log_message(self,*args):pass
    server=HTTPServer(('127.0.0.1',0),Handler)
    port_queue.put(server.server_port)
    server.serve_forever()

def main(root):
    root=Path(root);out=root/'artifacts/measured';out.mkdir(parents=True,exist_ok=True)
    ctx=mp.get_context('spawn');ports=ctx.Queue();pressure=ctx.Value('b',False)
    process=ctx.Process(target=serve,args=(ports,pressure),daemon=True);process.start()
    port=ports.get(timeout=20);observed=psutil.Process(process.pid);observed.cpu_percent()
    rows=[]
    try:
        for phase,count in [('baseline_fit',30),('baseline_check',10),('controlled_compute_pressure',12),('recovery',12)]:
            pressure.value=phase=='controlled_compute_pressure'
            for index in range(count):
                start=time.perf_counter();latencies=[];failures=0
                for _ in range(4):
                    before=time.perf_counter()
                    try:
                        with urllib.request.urlopen(f'http://127.0.0.1:{port}/probe',timeout=5) as response:
                            assert response.status==200 and len(response.read())==32
                    except Exception:failures+=1
                    latencies.append((time.perf_counter()-before)*1000)
                elapsed=time.perf_counter()-start
                row={'observed_utc':datetime.now(timezone.utc).isoformat(),'phase_annotation':phase,'requests':4,'failures':failures,'request_latency_p95_ms':round(float(np.percentile(latencies,95)),6),'process_cpu_percent':observed.cpu_percent(),'process_rss_bytes':observed.memory_info().rss,'vm_memory_percent':psutil.virtual_memory().percent,'observation_seconds':round(elapsed,6)}
                rows.append(row)
                if elapsed<.5:time.sleep(.5-elapsed)
            print('Measured phase',phase,flush=True)
    finally:
        process.terminate();process.join(timeout=10)
        if process.is_alive():process.kill();process.join()
    features=['request_latency_p95_ms','process_cpu_percent']
    x=np.asarray([[r[k] for k in features] for r in rows])
    fit=np.array([r['phase_annotation']=='baseline_fit' for r in rows])
    model=IsolationForest(n_estimators=100,max_samples=30,contamination='auto',random_state=17,n_jobs=1).fit(x[fit])
    # Cutoff fixed from baseline fit only; pressure/recovery labels never enter fit.
    cutoff=float(np.quantile(-model.score_samples(x[fit]),.95))
    scores=-model.score_samples(x)
    for row,score in zip(rows,scores):row['novelty_score']=float(score);row['above_baseline_cutoff']=bool(score>cutoff)
    path=out/'original-linuxone-service.csv'
    with path.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=rows[0].keys());writer.writeheader();writer.writerows(rows)
    joblib.dump({'estimator':model,'features':features,'baseline_cutoff':cutoff},out/'observed-novelty.joblib',compress=3)
    phases={phase:{'observations':sum(r['phase_annotation']==phase for r in rows),'median_request_p95_ms':float(np.median([r['request_latency_p95_ms'] for r in rows if r['phase_annotation']==phase])),'above_baseline_cutoff':sum(r['above_baseline_cutoff'] for r in rows if r['phase_annotation']==phase),'failed_requests':sum(r['failures'] for r in rows if r['phase_annotation']==phase)} for phase in dict.fromkeys(r['phase_annotation'] for r in rows)}
    result={'architecture':platform.machine(),'collected_utc':datetime.now(timezone.utc).isoformat(),'data_kind':'Original measured service timings and process counters on the assigned LinuxONE VM','csv_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'rows':len(rows),'features':features,'model':'IsolationForest, 100 trees, 30 baseline observations; 95th-percentile fit-only cutoff','phase_results':phases,'scope':'Bounded localhost hash-computation microservice. Pressure annotation identifies actual increased computation, not a production failure or hospital outage. No synthetic pool/retry values are added. This separate novelty experiment does not validate or replace the simulator-trained 60-second breach model.','limitations':['Single short experiment on one VM','Only four actual requests per measurement window; p95 is descriptive','Baseline fit is small and noise/resource contention may affect scores','No real disruption, incident recall, causal prevention or cross-domain claim']}
    (out/'report.json').write_text(json.dumps(result,indent=2))
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(2,1,figsize=(12,5.5),sharex=True)
    ax[0].plot([r['request_latency_p95_ms'] for r in rows],color='#167567');ax[0].set(ylabel='Measured request p95 (ms)',title='Original LinuxONE service measurements / bounded computation experiment')
    ax[1].plot(scores,color='#315b83');ax[1].axhline(cutoff,color='#b17532',linestyle='--',label='Fit-baseline cutoff');ax[1].set(xlabel='Observation index (approximately 0.5 s windows)',ylabel='Novelty score');ax[1].legend()
    for a in ax:a.axvspan(40,51,color='#e8b969',alpha=.25);a.grid(alpha=.15)
    fig.tight_layout();fig.savefig(out/'observed-service.png',dpi=220);plt.close(fig)
    print(json.dumps(result,indent=2));return result
