"""Send already-aggregated JSONL service windows through an SSH tunnel.

This adapter does not invent operational telemetry or its provenance. Validate
the trained model against the deployment distribution before relying on it.
"""
from pathlib import Path
import argparse
import json
import time
import urllib.request
import urllib.error
import sys
from urllib.parse import urlparse
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from continuityguard.web import Telemetry

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url',default='http://127.0.0.1:8080')
    parser.add_argument('--token-file',required=True,type=Path)
    parser.add_argument('--input',required=True,type=Path)
    parser.add_argument('--reset-session',action='store_true',help='Explicitly stop the demo and reset live feature windows')
    args=parser.parse_args()
    parsed=urlparse(args.url)
    if parsed.scheme!='http' or parsed.hostname not in {'127.0.0.1','localhost','::1'} or parsed.username or parsed.password:
        parser.error('Use a loopback HTTP URL through the authorized SSH tunnel')
    token=args.token_file.read_text().strip()
    def post(path,data):
        request=urllib.request.Request(args.url.rstrip('/')+'/api/'+path,data=json.dumps(data).encode(),headers={'Authorization':'Bearer '+token,'Content-Type':'application/json','X-ContinuityGuard':'operator'})
        for attempt in range(6):
            try:
                with urllib.request.urlopen(request,timeout=15) as response:return json.load(response)
            except urllib.error.HTTPError as exc:
                if exc.code!=429 or attempt==5:raise
                time.sleep(min(4,.125*2**attempt))
    if args.reset_session:post('external-session',{})
    count=0
    with args.input.open() as source:
        batch=[]
        for line in source:
            if len(line)>65536:raise ValueError('An input window exceeds the bounded adapter line size')
            if not line.strip():continue
            event=Telemetry.model_validate_json(line).model_dump()
            event['source_mode']='external'
            batch.append(event)
            if len(batch)==4:
                count+=post('events',{'events':batch})['accepted_into_queue'];batch=[]
        if batch:count+=post('events',{'events':batch})['accepted_into_queue']
    print(json.dumps({'queued_events':count,'scope':'Queue acceptance; inspect /api/state for processed, rejected, duplicate and failed-batch counts.'}))

if __name__=='__main__':main()
