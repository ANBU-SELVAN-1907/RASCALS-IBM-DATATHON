"""Build and start the submitted image on the authorized RHEL LinuxONE host.

Run from a host checkout containing artifacts produced by the Jupyter notebook.
No inbound firewall port is opened. Preserve the state volume on redeployment.
"""
from pathlib import Path
import argparse
import json
from datetime import datetime,timezone
import socket
import subprocess
import time
import urllib.request

def run(*args, check=True):
    result=subprocess.run(['sudo','-n','podman',*args],text=True,capture_output=True)
    if check and result.returncode:
        raise RuntimeError(result.stderr[-4000:])
    return result

def main(project, replace=False):
    project=Path(project).resolve()
    if not (project/'artifacts/manifest.json').exists():
        raise SystemExit('Run and export the training notebook before deployment.')
    exists=run('container','exists','continuityguard',check=False).returncode==0
    if exists and not replace:
        raise SystemExit('Container exists. Use --replace for a deliberate redeployment; its state volume is preserved.')
    with socket.socket() as probe:
        if probe.connect_ex(('127.0.0.1',8080)) == 0 and not (exists and replace):
            raise SystemExit('Port 8080 is occupied. Inspect the existing process before deploying; use a separate port for development.')
    build=['build','--format','docker','-t','localhost/continuityguard:2026','-f',str(project/'Containerfile'),str(project)]
    result=run(*build,check=False)
    if result.returncode and 'unsupported MIME type for compression' in result.stderr:
        # Supplied image has mixed OCI-manifest/Docker-layer media metadata.
        # Flatten an untouched throwaway container from the pinned source; no
        # running lab volume, credentials, notebook state or code is included.
        source='registry.linuxone.cloud.marist.edu/l1cc/jupyterlab-image-s390x@sha256:d2da8a7b0c88c3b468e29014b2ada9ef8274f98c976ec456904c5e2bae5aa54c'
        normalized='localhost/ibm-lab-flat:2026'
        if run('image','exists',normalized,check=False).returncode!=0:
            archive=project.parent/'ibm-lab-rootfs.tar'
            container=run('create','--entrypoint','/bin/true',source).stdout.strip()
            try:
                run('export','-o',str(archive),container)
                config=json.loads(run('image','inspect',source).stdout)[0]['Config']
                changes=['--change','USER 1000','--change','WORKDIR /home/ibm-user']
                for env in config.get('Env',[]):
                    changes += ['--change','ENV '+env]
                run('import',*changes,str(archive),normalized)
            finally:
                run('rm',container,check=False)
        result=run(*build[:-1],'--build-arg','BASE_IMAGE='+normalized,build[-1],check=False)
    if result.returncode:
        raise RuntimeError(result.stderr[-4000:])
    print(result.stdout[-2500:],flush=True)
    if exists:
        backup='continuityguard-previous-'+datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
        run('stop','--time','30','continuityguard')
        run('rename','continuityguard',backup)
        print('Retained stopped rollback container:',backup,flush=True)
    with socket.socket() as probe:
        if probe.connect_ex(('127.0.0.1',8080)) == 0:
            raise SystemExit('Port remains occupied after stopping the previous app. Inspect it before continuing.')
    if run('volume','exists','continuityguard-state',check=False).returncode!=0:
        run('volume','create','continuityguard-state')
    container=run('run','-d','--name','continuityguard','--network','host','--restart','unless-stopped','--stop-timeout','30','--memory','2g','--cpus','1.5','--pids-limit','256','--cap-drop','ALL','--security-opt','no-new-privileges','--read-only','--tmpfs','/tmp:rw,nosuid,nodev,size=128m','-v','continuityguard-state:/home/ibm-user/cg-state:Z','localhost/continuityguard:2026').stdout.strip()
    for _ in range(30):
        try:
            with urllib.request.urlopen('http://127.0.0.1:8080/api/health',timeout=2) as response:
                health=json.load(response)
            state=json.loads(run('inspect',container).stdout)[0]['State']
            if not state['Running'] or state.get('Restarting'):
                raise RuntimeError('Submitted container is not running steadily')
            if health['model_version'] != json.loads((project/'artifacts/manifest.json').read_text())['version']:
                raise RuntimeError('Health endpoint is serving a different model version')
            print(json.dumps({'container_id':container,'health':health,'access':'SSH tunnel to VM loopback port 8080','image':'localhost/continuityguard:2026'},indent=2))
            return
        except Exception:
            time.sleep(1)
    raise RuntimeError('Health check did not become ready; inspect container logs.')

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('project',nargs='?',default='.')
    parser.add_argument('--replace',action='store_true')
    args=parser.parse_args()
    main(args.project,args.replace)
