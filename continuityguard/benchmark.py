"""Paced direct-engine benchmark, with an explicit non-HTTP measurement boundary."""
from pathlib import Path
import json
import os
import platform
import tempfile
import time
import numpy as np
import psutil
from .runtime import Engine
from .simulation import Experiment, simulate

def main(artifacts):
    artifacts=Path(artifacts)
    events,_=simulate(Experiment('pool_exhaustion',771, strength=1.12))
    trials=[]
    process=psutil.Process()
    for rate in (10,50,100):
        with tempfile.TemporaryDirectory() as folder:
            engine=Engine(artifacts,str(Path(folder)/'benchmark.sqlite'))
            count=rate*8
            timings=[]
            cpu_before=process.cpu_times()
            started=time.perf_counter()
            for i in range(0,count,4):
                due=started+i/rate
                if due>time.perf_counter():
                    time.sleep(due-time.perf_counter())
                before=time.perf_counter()
                engine.ingest(events[i:i+4])
                timings.append((time.perf_counter()-before)*1000)
            remaining=started+8-time.perf_counter()
            if remaining>0:
                time.sleep(remaining)
            elapsed=time.perf_counter()-started
            cpu_after=process.cpu_times()
            state=engine.snapshot()
            trials.append({'offered_events_per_second':rate,'accepted_events':state['accepted'],'rejected_events':state['rejected'],'duplicates':state['duplicates'],'measurement_seconds':round(elapsed,3),'achieved_events_per_second':round(state['accepted']/elapsed,2),'batch_size':4,'p50_batch_processing_ms':float(np.percentile(timings,50)),'p95_batch_processing_ms':float(np.percentile(timings,95)),'p99_batch_processing_ms':float(np.percentile(timings,99)),'process_cpu_seconds':round(cpu_after.user+cpu_after.system-cpu_before.user-cpu_before.system,3),'process_rss_bytes':process.memory_info().rss})
            engine.close()
            print(json.dumps(trials[-1]),flush=True)
    result={'architecture':platform.machine(),'logical_cpus':os.cpu_count(),'duration_per_trial_seconds':8,'scope':'Paced in-process engine with SQLite commits on the assigned LinuxONE VM. Source telemetry is synthetic service-window events; this is not an HTTP or source-to-browser load test. GenAI is off.','boundary':'Feature extraction, ML scoring, alert policy and journal commit; measured for batches of 4 events.','queue_scope':'Direct engine: ingestion queue is bypassed in this benchmark. Queue backpressure is checked separately by correctness tests.','trials':trials}
    (artifacts/'runtime-benchmark.json').write_text(json.dumps(result,indent=2))
    return result
