"""Verify the named LinuxONE prototype; optionally restart it and run a demo.

Run on the authorized LinuxONE host, not the browser client. Private tokens are
read internally and never included in published evidence.
"""
from pathlib import Path
from datetime import datetime,timezone
import argparse
import json
import subprocess
import time
import urllib.request

def main(root,restart=False,demo=False):
    root=Path(root);dest=root/'evidence';dest.mkdir(exist_ok=True)
    def run(*args):return subprocess.run(['sudo','-n','podman',*args],text=True,capture_output=True,check=True)
    token=run('exec','continuityguard','cat','/home/ibm-user/cg-state/.access-token').stdout.strip()
    headers={'Authorization':'Bearer '+token,'X-ContinuityGuard':'operator','Content-Type':'application/json'}
    def api(path,data=None):
        req=urllib.request.Request('http://127.0.0.1:8080/api/'+path,data=json.dumps(data).encode() if data is not None else None,headers=headers)
        return json.load(urllib.request.urlopen(req,timeout=20))
    def save(name,value):(dest/name).write_text(json.dumps(value,indent=2))
    if restart:
        before=api('audit')
        stream=urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8080/api/stream',headers=headers),timeout=20)
        started=time.perf_counter();result=run('restart','--time','30','continuityguard')
        elapsed=time.perf_counter()-started;stream.close()
        for _ in range(100):
            try:after=api('audit');break
            except OSError:time.sleep(.1)
        query="import sqlite3,json;c=sqlite3.connect('/home/ibm-user/cg-state/events.sqlite');print(json.dumps(c.execute('SELECT digest FROM audit ORDER BY id LIMIT 1 OFFSET ?',("+str(before['records']-1)+",)).fetchone()))"
        retained=json.loads(run('exec','continuityguard','python3','-c',query).stdout)[0]
        assert retained==before['head'] and after['valid']
        save('restart-check.json',{'verified_utc':datetime.now(timezone.utc).isoformat(),'before_restart':before,'after_restart':after,'original_prefix_retained':retained==before['head'],'restart_seconds_with_active_sse_client':round(elapsed,3),'forced_kill_warning':'SIGKILL' in result.stderr,'stderr':result.stderr,'scope':'Actual application restart with an open SSE connection. SQLite history persists; feature windows and sessions reset.'})
    state=json.loads(run('inspect','continuityguard').stdout)[0]
    proof=api('platform-proof')
    assert proof['architecture']=='s390x' and proof['process_uid']==1000 and proof['root_filesystem_readonly'] and proof['effective_capabilities_hex']=='0000000000000000'
    save('linuxone-verification.json',{'verified_utc':datetime.now(timezone.utc).isoformat(),'image_id':state['Image'],'container_state':state['State']['Status'],'memory_limit_bytes':state['HostConfig']['Memory'],'cpu_quota':state['HostConfig']['CpuQuota'],'cpu_period':state['HostConfig']['CpuPeriod'],'readonly_rootfs':state['HostConfig']['ReadonlyRootfs'],'security_opt':state['HostConfig']['SecurityOpt'],'platform_proof':proof,'health_response':api('health'),'audit':api('audit')})
    if demo:
        api('scenario',{'name':'pool_exhaustion','seed':101,'speed':4})
        deadline=time.monotonic()+100
        while time.monotonic()<deadline:
            snapshot=api('state')
            if snapshot['incidents']:break
            time.sleep(1)
        else:raise RuntimeError('Demo did not produce an incident')
        incident=snapshot['incidents'][0]
        api('explain',{'incident_id':incident['id']})
        response=api('response-preview',{'incident_id':incident['id']})
        deadline=time.monotonic()+100
        while time.monotonic()<deadline:
            explanation=api('explanation/'+incident['id'])
            if explanation['status']=='complete':break
            time.sleep(1)
        else:raise RuntimeError('Local explanation did not complete')
        assert explanation['mode'].startswith('local Granite')
        assert explanation['evidence_ids']==[e['id'] for e in incident['evidence']]
        save('demo-verification.json',{'verified_utc':datetime.now(timezone.utc).isoformat(),'model_version':proof['model']['version'],'incident':incident,'explanation':explanation,'response_preview':response,'scope':'Actual application actions on controlled synthetic telemetry; no real service modified.'})
    print('Native platform, model and requested checks verified; no credentials exported.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('project');p.add_argument('--restart',action='store_true');p.add_argument('--demo',action='store_true');a=p.parse_args();main(a.project,a.restart,a.demo)
