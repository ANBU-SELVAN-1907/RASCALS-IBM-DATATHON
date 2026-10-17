"""Build the submission PDF from measured artifacts, with editable source code."""
from pathlib import Path
import json
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'submission/RASCALS-ContinuityGuard-Pitch.pdf'
W,H=960,540
INK='#183F34'; GREEN='#187563'; MUTED='#657C70'; PAPER='#F6F8F2'; LINE='#D7E1D4'; GOLD='#AD793B'
c=canvas.Canvas(str(OUT),pagesize=(W,H),pageCompression=1)
c.setTitle('RASCALS | ContinuityGuard | IBM Z Datathon 2026')
c.setAuthor('Team RASCALS')

def rect(x,y,w,h,color):
    c.setFillColor(HexColor(color));c.rect(x,H-y-h,w,h,fill=1,stroke=0)

def text(x,y,content,size=16,color=INK,bold=False):
    c.setFillColor(HexColor(color));c.setFont('Helvetica-Bold' if bold else 'Helvetica',size)
    c.drawString(x,H-y-size,content)

def wrap(x,y,content,width,size=16,color=MUTED,leading=None):
    leading=leading or size*1.45
    words=content.split();lines=[];line=''
    for word in words:
        candidate=(line+' '+word).strip()
        if stringWidth(candidate,'Helvetica',size)>width and line:
            lines.append(line);line=word
        else:line=candidate
    if line:lines.append(line)
    for i,line in enumerate(lines):text(x,y+i*leading,line,size,color)
    return y+len(lines)*leading

def start(number,title,subtitle=None):
    rect(0,0,W,H,PAPER)
    text(48,27,'RASCALS / IBM Z DATATHON 2026',10,GREEN,True)
    text(48,74,title,31,INK,True)
    if subtitle:wrap(48,121,subtitle,860,14)
    rect(48,494,864,1,LINE)
    text(48,509,'CONTINUITYGUARD  |  Synthetic service telemetry. No patient data.',9,MUTED)
    text(881,509,f'{number:02}',9,MUTED)

def end():c.showPage()

start(1,'Useful warning before a service fails', 'ContinuityGuard - real-time system anomaly detection and evidence-backed operator support on IBM LinuxONE')
text(48,201,'DETECT',11,GREEN,True);wrap(48,230,'Forecast a developing service-objective breach from causal rolling telemetry.',238,20,INK)
text(354,201,'UNDERSTAND',11,GREEN,True);wrap(354,230,'Inspect the evidence and the dependent services that matter.',238,20,INK)
text(660,201,'PREVIEW A RESPONSE',11,GREEN,True);wrap(660,230,'Compare an operator action with no action in the same controlled workload.',248,20,INK)
rect(48,401,864,53,INK);text(69,416,'37 s median early warning in the final synthetic test',21,'#F5F8EE',True)
end()

start(2,'Hospital digital-service availability','A shared infrastructure bottleneck can affect several essential software services before the operator has a useful explanation.')
wrap(48,184,'The user: hospital IT operators with limited monitoring capacity.',400,22,INK)
wrap(48,280,'The decision: which dependency to investigate, which services need protection, and which runbook to review.',400,19)
for y,label in [(190,'Urgent-results service'),(265,'Appointments service'),(340,'Optional batch reporting')]:
    rect(555,y,325,48,'#E7EFE3');text(575,y+12,label,17,INK)
    c.setStrokeColor(HexColor(GREEN));c.line(520,H-(y+24),555,H-(y+24))
c.setStrokeColor(HexColor(GREEN));c.line(520,H-214,520,H-364)
text(493,410,'Shared database dependency',16,GREEN,True)
wrap(48,415,'Real-world context: NHS England documented postponed care after the 2024 Synnovis incident. This prototype was not tested on that incident.',400,11)
c.linkURL('https://www.england.nhs.uk/london/2024/06/20/update-on-cyber-incident-clinical-impact-in-south-east-london-thursday-20-june/',(48,H-470,460,H-410),relative=0)
end()

start(3,'A native LinuxONE decision path','Training, evaluation, inference, explanation and the API run on the provided s390x VM. The browser connects through an SSH tunnel.')
labels=[('Telemetry','Validated queue'),('Causal features','Past/current only'),('Forecast + novelty','Separate scores'),('Incident evidence','Runbook + impact')]
for i,(label,detail) in enumerate(labels):
    x=48+i*222
    rect(x,205,201,90,'#E6EEE2');text(x+14,225,label,17,INK,True);text(x+14,256,detail,12,MUTED)
    if i<3:text(x+205,235,'>',15,GREEN,True)
text(48,337,'Predictive AI',17,GREEN,True);wrap(48,366,'Calibrated seven-leaf boosted-tree forecast; Isolation Forest for novelty; thresholds as a measured baseline and failure fallback.',390,16)
text(515,337,'Predictive + generative AI',17,GREEN,True);wrap(515,366,'Local Granite selects evidence-grounded wording under a strict schema. No tool access or autonomous remediation.',390,16)
text(48,462,'RHEL 9.8 / 3 virtual CPUs / 7.3 GiB RAM / Podman / Jupyter / scikit-learn',11,MUTED)
end()

start(4,'Learn, calibrate, select, then test','The same causal feature code is used in Jupyter and online inference. Entire runs stay in one split.')
for i,(number,label) in enumerate([(60,'Training runs'),(18,'Calibration runs'),(24,'Validation runs'),(60,'Final test runs')]):
    x=48+i*220;text(x,190,str(number),49,GREEN,True);text(x,253,label,16,INK)
wrap(48,320,'26 inputs describe current signals, rolling means/slopes, load-normalized values and service identity. Fault labels, seeds, onset time and future values never enter the predictors.',850,18)
wrap(48,405,'Three forecast candidates and alert policies were compared on validation. The earlier inspected development report is retained. Final v2 testing uses fresh seeds; simulator families still overlap.',850,14)
end()

start(5,'Earlier warning, with a precision tradeoff','Final test: 60 synthetic runs, 47 service incidents, 10 healthy service-hours. Service incidents in one run are correlated.')
columns=[48,270,427,580,736]
for x,label in zip(columns,['Detector','Early recall','Precision','Median lead*','Missed']):text(x,190,label,13,MUTED,True)
data=[('Static thresholds','89.4%','68.3%','9 s','4 / 47'),('Robust statistics','63.8%','20.3%','36.5 s','17 / 47'),('Isolation Forest','85.1%','26.7%','46 s','7 / 47'),('ContinuityGuard','91.5%','61.4%','37 s','4 / 47')]
for i,row in enumerate(data):
    y=226+i*45
    if i==3:rect(42,y-6,864,39,'#E2EEDC')
    for x,value in zip(columns,row):text(x,y,value,16,INK,i==3)
wrap(48,422,'*Among early detections. Both final model and threshold baseline had zero alerts in tested healthy runs; the model had 27 unmatched alerts across all runs, versus 20 for thresholds.',850,12)
text(48,467,'Unseen abrupt stress: 24 / 24 incidents detected, zero warned in advance. No precursor means no promised early warning.',11,MUTED)
end()

start(6,'A decision an operator can inspect','The contribution connects warning evidence, declared software-service importance, and a repeatable response preview.')
text(48,185,'01 / Evidence',18,GREEN,True);wrap(48,218,'Measured pool, queue, retry and latency values accompany the alert. The dependency diagnosis is a hypothesis.',250,17)
text(354,185,'02 / Response preview',18,GREEN,True);wrap(354,218,'The same future demand/noise is replayed with and without an allowlisted simulator action.',250,17)
text(660,185,'03 / Explain safely',18,GREEN,True);wrap(660,218,'Local generation uses valid evidence IDs and runbook wording; validation failure is explicit.',250,17)
rect(48,365,864,86,'#E6EEE2');text(66,379,'Example held-out paired experiment: seed 50300',15,INK,True)
text(66,409,'+294 modeled urgent-results successes / 100 s to 0 s breach duration / 1,418 batch requests deferred',14,GREEN)
text(48,466,'Simulator-conditional effects, not proof of a real hospital intervention. No host or real service is modified.',11,MUTED)
end()

start(7,'Reproducible evidence and clear limits','A prototype designed to be reviewed, rerun and challenged.')
text(48,185,'Runtime evidence',19,GREEN,True);wrap(48,222,'At 100 synthetic window events/s: 9.03–53.60 ms p95 across two runs processing per four-event engine batch; about 186 MB process RSS. Short eight-second test, with generation off.',395,18)
wrap(48,354,'This excludes HTTP, queue waiting and browser rendering. It does not establish maximum capacity or production resilience.',395,14)
text(520,185,'Review package',19,GREEN,True);wrap(520,222,'Executed Jupyter notebooks, trained model hash, split manifest, tests, measured reports and readable source.',390,18)
wrap(520,333,'Next: authorized real telemetry, operator feedback, stronger authentication and broader failure testing. No z/OS integration, hardware accelerator use or clinical benefit is claimed.',390,14)
text(48,445,'Repository: github.com/ANBU-SELVAN-1907/RASCALS-IBM-DATATHON',14,INK,True)
c.linkURL('https://github.com/ANBU-SELVAN-1907/RASCALS-IBM-DATATHON',(48,H-467,900,H-437),relative=0)
text(48,470,'AI-assisted implementation; team review and organizer guidance apply. Open-source resources are attributed in the repository.',10,MUTED)
end()
c.save()
assert OUT.stat().st_size<5_000_000
print(OUT,OUT.stat().st_size,'bytes')
