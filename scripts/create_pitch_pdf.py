"""Build a measured, team-named pitch from the final LinuxONE outputs."""
from pathlib import Path
import json
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'submission/RASCALS-ContinuityGuard-Pitch.pdf'
read=lambda name:json.loads((ROOT/name).read_text())
R=read('artifacts/report.json');M=R['systems']['ContinuityGuard'];B=R['systems']['Static thresholds']
TEAM=read('submission/team.json');CHECK=read('artifacts/correctness-report.json')
HTTP=read('artifacts/http-benchmark.json')['trials'][-1]
GEN=read('evidence/jupyter-ai-proof.json')['generative_explanation']
DEMO=read('evidence/demo-verification.json')
W,H=960,540
INK='#173E34';GREEN='#197762';MUTED='#60776C';PAPER='#F7F9F3';LINE='#D9E3D8';PALE='#E7EFE2'
c=canvas.Canvas(str(OUT),pagesize=(W,H),pageCompression=1)
c.setTitle(TEAM['project_title']+' | ContinuityGuard');c.setAuthor('; '.join(TEAM['members']))
def rect(x,y,w,h,color):
    c.setFillColor(HexColor(color));c.rect(x,H-y-h,w,h,fill=1,stroke=0)
def text(x,y,s,size=16,color=INK,bold=False):
    s=str(s).replace('–','-').replace('—','-').replace('·',' / ').replace('→','to')
    c.setFillColor(HexColor(color));c.setFont('Helvetica-Bold' if bold else 'Helvetica',size);c.drawString(x,H-y-size,s)
def wrap(x,y,s,width,size=16,color=MUTED,leading=None,bold=False):
    leading=leading or size*1.35;line='';lines=[]
    for word in s.split():
        candidate=(line+' '+word).strip()
        if line and stringWidth(candidate,'Helvetica-Bold' if bold else 'Helvetica',size)>width:lines.append(line);line=word
        else:line=candidate
    if line:lines.append(line)
    for i,line in enumerate(lines):text(x,y+i*leading,line,size,color,bold)
    return y+len(lines)*leading
def start(n,title,subtitle=''):
    rect(0,0,W,H,PAPER);text(36,20,TEAM['project_title'],10,GREEN,True)
    text(36,65,title,30,INK,True)
    if subtitle:wrap(36,109,subtitle,884,13)
    rect(36,498,888,1,LINE);text(36,513,'CONTINUITYGUARD | Synthetic telemetry; no patient data | Public source and measured evidence',8,MUTED)
    text(898,513,f'{n:02}',8,MUTED)
def end():c.showPage()
def link(x,y,label,url,size=10):
    text(x,y,label,size,GREEN);c.linkURL(url,(x,H-y-size-3,x+stringWidth(label,'Helvetica',size),H-y+2),relative=0)
def shot(name,x,y,w,h,crop=None):
    im=Image.open(ROOT/name).convert('RGB')
    if crop:im=im.crop(crop)
    iw,ih=im.size;scale=min(w/iw,h/ih);dw,dh=iw*scale,ih*scale
    c.drawImage(ImageReader(im),x+(w-dw)/2,H-y-dh,width=dw,height=dh)
def card(x,y,w,title,body):
    rect(x,y,w,146,PALE);text(x+15,y+15,title,15,GREEN,True);wrap(x+15,y+45,body,w-30,16,INK)
def pct(v):return f'{100*v:.1f}%'

start(1,'ContinuityGuard','Theme 1: Real-Time AI for Critical Decisions / System Anomaly Detection')
wrap(36,168,'Warn before disruption. Inspect the evidence. Preview the next step.',835,34,INK,bold=True)
text(36,289,'Native LinuxONE AI + accountable operator decisions',19,GREEN,True)
wrap(36,333,'ANBU SELVAN T / SAHANA G / DHARSHINI E / POOJA V',880,17,INK,bold=True)
text(36,369,TEAM['institution'],17,MUTED)
link(36,447,'Public code: github.com/ANBU-SELVAN-1907/RASCALS-IBM-DATATHON','https://github.com/ANBU-SELVAN-1907/RASCALS-IBM-DATATHON',12)
end()

start(2,'A system failure can interrupt essential care','Our target users are hospital IT operators responsible for shared digital-service infrastructure.')
text(36,172,'1,294+',44,GREEN,True);text(36,228,'outpatient appointments postponed',17,INK,True)
wrap(36,271,'NHS England reported this disruption across two affected trusts for 10-16 June 2024 after the Synnovis cyber incident.',390,16)
link(36,377,'Source: NHS England, 20 June 2024','https://www.england.nhs.uk/london/2024/06/20/update-on-cyber-incident-clinical-impact-in-south-east-london-thursday-20-june/',11)
wrap(36,414,'Context only: our prototype was not tested on that incident and does not claim to detect or prevent ransomware.',390,12)
card(491,172,432,'The operational problem','Pool exhaustion, retry cascades and resource pressure can spread through shared dependencies before operators know where to investigate.')
text(506,343,'The decision we support',20,GREEN,True)
wrap(506,381,'Which dependency needs attention, which software services matter most, and what should an operator inspect next?',392,18,INK)
end()

start(3,'The complete path runs on LinuxONE','The browser is a client through SSH. Telemetry, inference, local generation and the journal stay in the provided VM.')
rect(36,165,888,83,PALE);text(53,176,'JUPYTER CONTAINER / NATIVE s390x',12,GREEN,True)
text(53,204,'Fit candidates > separate calibration > validation policy > fresh final test > hashed model',17,INK)
for i,(a,b) in enumerate([('Ingest','Validated queue'),('Observe','Causal features'),('Score','Forecast + guard'),('Decide','Evidence + runbook')]):
    x=36+224*i;rect(x,282,210,79,INK);text(x+13,295,a,19,'#F7F9F3',True);text(x+13,326,b,12,'#D4E4D5')
for x,title,body in [(36,'ISOLATION FOREST','Separate novelty score; not a probability or independent page trigger.'),(344,'LOCAL GRANITE','Verified evidence wording; complete IDs and labeled fallback.'),(652,'RESPONSE PREVIEW','Same-workload action/no-action branches in the simulator only.')]:
    text(x,394,title,11,GREEN,True);wrap(x,417,body,260,13)
end()

start(4,'A small model, selected for the actual task','Predict a new sustained service-objective breach within 60 event-time seconds using current and past observations.')
for i,(value,label) in enumerate([(60,'Train runs'),(18,'Calibration'),(24,'Validation'),(60,'Fresh test runs')]):
    x=36+i*224;text(x,165,value,43,GREEN,True);text(x,220,label,15,INK)
card(36,275,430,'Calibrated boosted trees','Seven-leaf histogram boosting won the validation objective. Current policy: forecast >= 0.97 OR explicit operational thresholds.')
card(490,275,434,'Evidence of separation','26 causal features; whole runs and disjoint seeds. No scenario, onset, future values or fault labels enter the predictors.')
text(36,449,f"Forecast PR-AUC {R['forecast_test']['pr_auc']:.3f} / prevalence {pct(R['forecast_test']['positive_prevalence'])} / Brier {R['forecast_test']['brier_score']:.5f}",13,INK)
text(36,475,'v3 aligns incident matching to 60 s. Earlier v1/v2 reports are retained as development history.',10,MUTED)
end()

start(5,'A working operator console, not a mockup','Actual deployed s390x application. Scenario telemetry and response effects are synthetic.')
shot('evidence/dashboard.png',36,159,570,300,crop=(230,470,845,815))
text(644,166,'Retained warning evidence',18,GREEN,True)
for i,e in enumerate(DEMO['incident']['evidence']):
    text(644,214+i*58,e['label'],12,MUTED)
    text(644,234+i*58,str(e['value'])+' '+e['unit'],20,INK,True)
wrap(644,407,'Actual selected incident; measurements are evidence, not causal attribution.',275,12)
text(36,469,'Streaming services > persistent warning > measurements > declared dependency and runbook',13,GREEN,True)
end()

start(6,'Measure usefulness without hiding the misses','Fresh v3 test: 60 synthetic runs; correlated service incidents within a run. No production hospital validation.')
xs=[36,281,428,568,731,834]
for x,label in zip(xs,['Detector','Early recall','Precision','Median lead*','Late','Missed']):text(x,163,label,12,MUTED,True)
for index,(name,m) in enumerate(R['systems'].items()):
    y=198+index*43
    if name=='ContinuityGuard':rect(29,y-6,895,37,PALE)
    vals=[name,pct(m['early_warning_recall']),pct(m['incident_precision']),str(m['median_early_lead_seconds'])+' s',m['late_detections'],m['missed']]
    for x,value in zip(xs,vals):text(x,y,value,15,INK,name=='ContinuityGuard')
wrap(36,382,f"Both methods warned before {M['early_detections']}/{M['incidents']} incidents. Median lead: {M['median_early_lead_seconds']:g} s vs {B['median_early_lead_seconds']:g} s; model precision was slightly lower. This does not establish consistent ML superiority.",882,14,INK)
ci=R['run_bootstrap']['systems']['ContinuityGuard']
text(36,445,f"Run-bootstrap 95% interval for early recall: {pct(ci['early_recall_percentile_95'][0])}-{pct(ci['early_recall_percentile_95'][1])}. 500 resamples; simulator-conditional.",11,MUTED)
text(36,472,'*Among early detections only. Zero healthy-run alerts in 10 service-hours is not proof of zero real false alarms.',10,MUTED)
end()

start(7,'The response is inspectable and bounded','Evidence, service priorities, approved investigation steps and a reproducible response preview form one decision workflow.')
shot('evidence/dashboard.png',36,155,382,324,crop=(870,1010,1235,1430))
text(460,166,'Predictive + generative, locally verified',20,GREEN,True)
wrap(460,212,f"Granite generated schema-validated wording on s390x in {GEN['elapsed_seconds']:g} seconds in the Jupyter proof. Every evidence ID cited in the summary is retained.",450,17,INK)
wrap(460,320,'The preview compares allowlisted actions under identical future demand/noise. It reports benefits with deferred optional work. It executes no real remediation.',450,16)
text(460,440,'Suspected source is a hypothesis, not causal proof.',12,MUTED)
end()

start(8,'Platform use that judges can verify','Native AI execution, actual ingestion and container controls are exposed as evidence.')
text(36,163,CHECK['tests_run'],48,GREEN,True);text(36,220,'native tests passed',18,INK,True)
wrap(36,269,'Checks cover leakage, online/offline parity, time gaps, invalid inputs, provenance, overload, consumer failure, model corruption and grounded fallback.',400,15)
text(36,379,f"{HTTP['processed_events']}/{HTTP['offered_events']} events processed",22,GREEN,True)
wrap(36,416,f"Real local HTTP path: 100 offered events/s for 10 s. Queue-ack p95 {HTTP['p95_http_queue_ack_ms']:g} ms; queue wait and inference are distinct boundaries.",405,13)
card(490,163,434,'Application containment','UID 1000 / read-only root / capabilities dropped / no-new-privileges / 2 GiB memory / 1.5 CPU quota / SSH loopback access')
shot('evidence/evaluation.png',490,322,434,126,crop=(250,995,850,1170))
wrap(505,458,'Actual live proof excerpt. Full screenshot and model hash are in evidence/. No accelerator claim.',400,10)
end()

start(9,'An accountable path from warning to action','Original integration and measured implementation, with limits that operators and judges can inspect.')
card(36,163,280,'Community value','Earlier investigation of shared service failures; preserve attention for essential software services.')
card(340,163,280,'Engineering evidence','Native notebooks, actual API ingestion, model hashes, failure tests and local explanations.')
card(644,163,280,'Next validation','Authorized real telemetry, operator feedback, domain calibration and reviewed runbooks before operational use.')
link(36,353,'github.com/ANBU-SELVAN-1907/RASCALS-IBM-DATATHON','https://github.com/ANBU-SELVAN-1907/RASCALS-IBM-DATATHON',15)
wrap(36,396,'Both sample labs executed before project work; confirm organizer mapping to the required categories. Review/upload the <=3 minute video and submit the portal manually.',880,14,INK)
wrap(36,461,'AI assistance is disclosed. Open-source resources and a criterion-by-criterion evidence map are in the repository. No score or award is guaranteed.',880,11)
end()
c.save()
assert OUT.stat().st_size<5_000_000
print(OUT,OUT.stat().st_size,'bytes / 9 pages')
