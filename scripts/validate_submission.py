from pathlib import Path
import hashlib
import json
import re
import csv
import math

root=Path(__file__).resolve().parents[1]
source=json.loads((root/'evidence/source-hashes.json').read_text())['sha256']
for name,digest in source.items():
    assert hashlib.sha256((root/name).read_bytes().replace(b'\r\n',b'\n')).hexdigest()==digest,name
deployed_source=json.loads((root/'evidence/deployed-source-hashes.json').read_text())
assert all(source[name]==digest for name,digest in deployed_source.items())
text=(root/'submission/FORM-ANSWERS.md').read_text(encoding='utf-8')
blocks=re.findall(r'```text\n(.*?)\n```',text,re.S)
assert len(blocks)==5
for index,block in enumerate(blocks,1):
    assert len(block)<=1024,(index,len(block))
    print('Form field',index,':',len(block),'/ 1024 characters')
manifest=json.loads((root/'artifacts/manifest.json').read_text())
assert hashlib.sha256((root/'artifacts/models.joblib').read_bytes()).hexdigest()==manifest['sha256']
for filename in ('01_train_and_evaluate','02_test_and_benchmark','03_engineering_audit','04_original_measurements','05_toolkit_readiness'):
    state=json.loads((root/f'notebooks/{filename}.execution.json').read_text())
    assert state['state']=='success',state
    print('Executed notebook:',filename,state['state'])
    notebook=json.loads((root/f'notebooks/{filename}.executed.ipynb').read_text())
    assert not any(o.get('output_type')=='error' for cell in notebook['cells'] for o in cell.get('outputs',[])),filename
measured=json.loads((root/'artifacts/measured/report.json').read_text())
raw=root/'artifacts/measured/original-linuxone-service.csv'
assert hashlib.sha256(raw.read_bytes()).hexdigest()==measured['csv_sha256']
with raw.open(newline='') as stream:
    rows=list(csv.DictReader(stream))
assert len(rows)==measured['rows']==sum(p['observations'] for p in measured['phase_results'].values())
for feature in measured['features']:
    assert all(math.isfinite(float(row[feature])) for row in rows),feature
toolkit=json.loads((root/'artifacts/toolkit/readiness.json').read_text())
assert toolkit['toolkit_container_executed'] is False and toolkit['hardware_acceleration_verified'] is False
assert hashlib.sha256((root/'artifacts/toolkit/random-forest-validation-candidate.onnx').read_bytes()).hexdigest()==toolkit['onnx_sha256']
connectivity=json.loads((root/'evidence/public-connectivity.json').read_text())
assert all(v['status']==200 and v['tls_certificate_verified'] and v['expected_service_received'] for v in connectivity.values())
correctness=json.loads((root/'artifacts/correctness-report.json').read_text())
assert correctness['successful'] and not correctness['errors'] and not correctness['failures'] and not correctness['skipped']
assert correctness['architecture']=='s390x'
http=json.loads((root/'artifacts/http-benchmark.json').read_text())
assert http['architecture']=='s390x' and http['unauthenticated_access_rejected']
for trial in http['trials']:
    assert trial['processed_events']==trial['queued_events'] and not trial['failed_batches'] and trial['audit']['valid']
proof=json.loads((root/'evidence/jupyter-ai-proof.json').read_text())
assert proof['generative_explanation']['mode'].startswith('local Granite')
assert proof['model_manifest']['sha256']==manifest['sha256']
assert proof['generative_explanation']['evidence_ids']==[e['id'] for e in proof['predictive_incident']['evidence']]
deployed=json.loads((root/'evidence/linuxone-verification.json').read_text())
assert deployed['platform_proof']['model']['sha256']==manifest['sha256']
assert deployed['platform_proof']['process_uid']==1000 and deployed['platform_proof']['root_filesystem_readonly']
restart=json.loads((root/'evidence/restart-check.json').read_text())
assert restart['original_prefix_retained'] and not restart['forced_kill_warning']
demo=json.loads((root/'evidence/demo-verification.json').read_text())
assert demo['model_version']==manifest['version']
assert demo['explanation']['evidence_ids']==[e['id'] for e in demo['incident']['evidence']]
report=json.loads((root/'artifacts/report.json').read_text())
assert report['manifest']['sha256']==manifest['sha256']
assert '60 seconds before' in report['method']['matching'] and manifest['forecast_horizon_seconds']==60
team=json.loads((root/'submission/team.json').read_text())
assert team['team_name'] in team['project_title'] and len(team['members'])==4
pdf=root/'submission/RASCALS-ContinuityGuard-Pitch.pdf'
assert pdf.read_bytes().startswith(b'%PDF-') and pdf.stat().st_size<5_000_000
video=json.loads((root/'submission/video-manifest.json').read_text())
assert video['duration_seconds']<180
assert video['container_duration_seconds']<180
assert video['resolution']=='1920x1080'
assert video['model_version']==manifest['version']
assert (root/'submission/RASCALS-ContinuityGuard-Walkthrough.mp4').stat().st_size>10000
extended=json.loads((root/'submission/implementation-video-manifest.json').read_text())
assert extended['duration_seconds']<900 and extended['resolution']=='1920x1080'
assert extended['container_duration_seconds']<900
assert extended['model_version']==manifest['version']
assert (root/'submission/RASCALS-Implementation-Guide.mp4').stat().st_size>10000
for file in root.rglob('*'):
    if not file.is_file() or '.git' in file.parts:
        continue
    assert file.suffix.lower() not in {'.pem','.key'},file
print('Model integrity and publication checks passed.')
