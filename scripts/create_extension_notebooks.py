"""Add native experiments without rewriting the frozen final evaluation."""
from pathlib import Path
import nbformat
root=Path(__file__).resolve().parents[1]
intro="""from pathlib import Path
import os,sys,platform,json
ROOT=Path.cwd()
if not (ROOT/'continuityguard').is_dir():ROOT=ROOT.parent
os.chdir(ROOT);sys.path.insert(0,str(ROOT))
assert platform.machine()=='s390x'
print('Actual kernel:',platform.machine(),platform.python_version())
"""
def save(name,cells):
 n=nbformat.v4.new_notebook(cells=cells,metadata={'kernelspec':{'display_name':'Python 3 (LinuxONE)','language':'python','name':'python3'}});nbformat.write(n,root/'notebooks'/name)
save('04_original_measurements.ipynb',[
 nbformat.v4.new_markdown_cell('# RASCALS / Original measured LinuxONE service data\n\nThis experiment records real request timings, process counters and timestamps. It deliberately separates measured service data from the synthetic hospital-service simulator. A bounded CPU-computation change is annotated; no actual hospital incident is claimed.'),
 nbformat.v4.new_code_cell(intro),
 nbformat.v4.new_code_cell("from continuityguard.measured_workload import main\nobserved=main(ROOT)"),
 nbformat.v4.new_code_cell("import pandas as pd\nfrom IPython.display import display,Image\ndisplay(pd.read_csv(ROOT/'artifacts/measured/original-linuxone-service.csv'))\ndisplay(Image(filename=str(ROOT/'artifacts/measured/observed-service.png')))\nprint('Measured-data provenance:',observed['csv_sha256'])"),
])
save('05_toolkit_readiness.ipynb',[
 nbformat.v4.new_markdown_cell('# RASCALS / IBM AI Toolkit readiness\n\nIBM AI Toolkit documentation is used for deployment controls and an optional Snap ML path. No registry entitlement was available; the supported IBM container and hardware acceleration are **not** claimed as executed. This notebook trains a small Random Forest challenger on simulator training runs and exports ONNX in a supported Snap ML model family. It reports validation-only performance and leaves the deployed v3 model unchanged.'),
 nbformat.v4.new_code_cell(intro),
 nbformat.v4.new_code_cell("""from continuityguard.train import dataset,stack
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import average_precision_score
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType
import onnx,hashlib,time
import numpy as np
out=ROOT/'artifacts/toolkit';out.mkdir(exist_ok=True)
x,y=stack(dataset(1000,10));xv,yv=stack(dataset(20000,4))
started=time.perf_counter()
candidate=RandomForestClassifier(n_estimators=40,max_depth=7,min_samples_leaf=8,n_jobs=1,random_state=17).fit(x,y)
fit_seconds=time.perf_counter()-started
model=convert_sklearn(candidate,initial_types=[('features',FloatTensorType([None,x.shape[1]]))],options={id(candidate):{'zipmap':False}},target_opset=17)
onnx.checker.check_model(model)
path=out/'random-forest-validation-candidate.onnx';path.write_bytes(model.SerializeToString())
report={'architecture':platform.machine(),'toolkit_registry_entitlement':'not configured','toolkit_container_executed':False,'hardware_acceleration_verified':False,'applied_use':'IBM deployment guidance and supported-family ONNX preparation','candidate':'RandomForestClassifier 40 trees, depth 7; validation only; not deployed','training_rows':len(y),'fit_seconds':round(fit_seconds,3),'validation_pr_auc':float(average_precision_score(yv,candidate.predict_proba(xv)[:,1])),'onnx_checker':'passed','onnx_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'source':'https://github.com/IBM/ai-toolkit-for-z-and-linuxone','scope':'Preparation is not Snap ML inference. Deployed HistGradientBoostingClassifier is not advertised as directly supported by Snap ML model import. Entitlement, model-import parity, calibration and policy validation are required before changing serving.'}
(out/'readiness.json').write_text(json.dumps(report,indent=2));display(report)
"""),
])
print('Created original-measurement and Toolkit-readiness notebooks.')
