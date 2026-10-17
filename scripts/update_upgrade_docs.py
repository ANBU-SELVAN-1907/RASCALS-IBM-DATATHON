"""Render the frozen detector's methods and upgrade evidence without changing it."""
from pathlib import Path
import json,re
P=Path(__file__).resolve().parents[1]
read=lambda n:json.loads((P/n).read_text())
r=read('artifacts/report.json');m=r['systems']['ContinuityGuard'];b=r['systems']['Static thresholds'];c=read('artifacts/correctness-report.json')
pct=lambda x:f'{100*x:.1f}%'
def write(n,s):(P/n).write_text(s.rstrip()+'\n',encoding='utf-8')
result=f"Early warnings: {m['early_detections']}/{m['incidents']} versus {b['early_detections']}/{b['incidents']}; precision {pct(m['incident_precision'])} versus {pct(b['incident_precision'])}; median early lead {m['median_early_lead_seconds']:g}s versus {b['median_early_lead_seconds']:g}s; misses {m['missed']} versus {b['missed']}; unmatched notifications {m['unmatched_alerts_all_runs']} versus {b['unmatched_alerts_all_runs']}."
write('docs/DETECTOR-UPGRADE.md',f'''# Detector upgrade: {r['manifest']['version']}

## The actual improvement

{result}

These are paired results on {r['split']['test_runs']} predeclared fresh synthetic runs. The benefit is fewer unmatched repeat notifications with the same observed early recall, median lead, late count and misses. It is a modest improvement within this simulator, not a claim of universal superiority or production outage prevention.

## What changed

1. A shared `AlertTracker` replaces the permanent latch. Persistent episodes are reviewed after 60 event-time seconds; 3-of-5 persistence and a 30-second cooldown remain. All detector comparisons use this scheduler.
2. The first threshold warning is preserved. Unlike the rejected V4 policy, low model confidence cannot filter that initial signal.
3. Calibrated standardized logistic regression predicts a 60-second breach risk. Only repeat triage uses its selected {r['policy']['warning_gate']:g} gate. Observed latency/error breach limits bypass that filter. Validation selected `trend_guard={r['policy']['trend_guard']}`.
4. Independent forecast paging is disabled. `forecast_threshold=1.01` is an explicit disabled sentinel, not an attainable probability. Novelty remains separately displayed.

## Why this model

Two standardized logistic candidates and three histogram-boosting sizes were fitted on training runs, then sigmoid-calibrated on different runs. Selection used notification precision and early recall on validation, including a constraint to match or exceed the corrected static baseline on both. A model with higher point-level PR-AUC need not produce the best operational notification policy. The selected model is `{r['selected_model']}`; its choice is not a claim that logistic regression is universally best.

## Freeze and fresh evaluation

Actual execution is retained in `notebooks/06_detector_upgrade.executed.ipynb`. The model and protocol hashes were written to `artifacts/freeze.json` before generating 500000-series final runs. Protocol, all validation options, split manifests and original final-test execution records are public. V1-V4 are retained development history, including V4's rejected precision/recall tradeoff.

The baseline also receives the lifecycle correction. Consequently the rise in recall relative to old V3 numbers cannot be attributed to ML; different seeds and a corrected scheduler prevent direct cross-version numerical comparison. Compare V5 against the baseline in the same V5 experiment.

## Uncertainty and ablation

The paired 500-resample whole-run precision-difference interval is {100*r['paired_bootstrap']['precision_delta_95'][0]:.2f} to {100*r['paired_bootstrap']['precision_delta_95'][1]:.2f} percentage points. The paired early-recall difference is zero for these sampled runs. Neither fact proves future non-inferiority or generalization beyond this simulator. `report.json/ablations` retains the no-ML-repeat-filter comparison.

The forecast point PR-AUC is {r['forecast_test']['pr_auc']:.4f}; this is a different metric from notification precision. The latter counts extra repeats, non-breaching fault warnings and out-of-window warnings as unmatched. Zero healthy-run alerts in {m['healthy_service_hours']:g} service-hours is not proof of a zero operational false-alarm rate.

## Verification

{c['tests_run']} native tests cover the bounded refresh, initial-warning preservation, confirmed-limit bypass, offline/live parity, time gaps, malformed events, overload, consumer errors and model integrity. The current HTTP and local Granite proofs are regenerated after model promotion. Container restart persistence and model/source hashes are checked before publication. Historical UI screenshots are labeled; current numerical outputs come from saved reports and authenticated API evidence.
''')
splits=read('artifacts/split-manifest.json')
table='| Split | Runs | Seed minimum / maximum | Purpose |\n|---|---:|---|---|\n'
purposes={'train':'Fit five candidate models','calibration':'Separate sigmoid and novelty reference','validation':'Choose model and repeat gate','test':'Frozen fresh evaluation','stress':'Unseen abrupt-failure checks'}
for name,rs in splits.items():table+=f"| {name} | {len(rs)} | {min(x['seed'] for x in rs)} / {max(x['seed'] for x in rs)} | {purposes[name]} |\n"
write('docs/METHODOLOGY.md',f'''# Frozen evaluation protocol

## Data and prediction target

The original simulator produces one aggregate per service per second for four services. These are synthetic request/failure counts, latency summaries, queue, pool, retries, CPU and memory. They are not real hospital transactions. The separate original measured-service experiment in notebook 04 does not train or validate this predictor.

The forecast target is a new service-objective breach in the next 60 event-time seconds. A breach requires p95 latency above 1,000 ms or observed failures/requests above 10% for three consecutive windows. Already-breached windows and windows without a full future horizon are excluded from forecast fitting and point metrics. Incident evaluation processes complete runs, including misses and late outcomes.

Twenty-six features use only current/past observations: eight values, two ratios, six slopes, six means and four service indicators. No scenario, seed, onset, fault metadata, future value or target enters a predictor. Service identity is declared context. A gap above five seconds resets causal windows and notification state.

## Whole-run separation

{table}
The sampling unit is a run; services in a run are dependent. V1-V4 were inspected during development and remain labeled history. V4 initial-warning filtering improved precision but lost fresh-test early recall, so it was rejected. V5 preserves first warnings and uses its own predeclared fresh final range. Model/protocol hashes were frozen before test generation. Repeating the same seeds later is reproduction, not additional independent validation.

## Models and validation selection

Five candidates: standardized logistic regression at C=0.1 and C=1, and histogram gradient boosting with 7, 15 and 31 leaves. Separate sigmoid calibration fits probability logits on calibration runs. Isolation Forest learns healthy variation and is evaluated/displayed separately.

V5 compares repeat gates from 0 to 0.97 and optional rising-trend bypass. Initial warnings are never filtered. Selection first requires validation precision and early recall at least as high as corrected static thresholds, then maximizes `0.65 * early recall + 0.35 * precision - 2 * max(0, healthy false alarms/hour - 0.5)`. This is our declared engineering objective, not IBM's judging formula. Selected: `{r['selected_model']}`, repeat risk gate {r['policy']['warning_gate']:g}, trend bypass {r['policy']['trend_guard']}.

## Notification lifecycle and fair comparison

Static thresholds are p95 >800 ms, pool >90%, error fraction >8%, or CPU >90%. They are a documented engineering baseline, not an exhaustive search of all threshold designs. Robust statistics uses median/MAD positive deviations and a validation-selected cutoff. Isolation Forest uses a fixed healthy-reference quantile.

Every comparator uses 15-observation warmup, 3-of-5 persistence, 30-second cooldown and a bounded 60-second episode recheck. V5 additionally allows learned risk to withhold low-risk repeats. Observed breach limits bypass filtering. Independent model paging is disabled; the score supports repeat triage and inspection.

Breaches separated by at most 15 seconds form one incident. Matching remains one alert per incident from 60 seconds before onset through 15 seconds after incident end. Every unmatched notification counts against precision, including extra repeats, non-breaching faults and too-early warnings. No retrospective point adjustment or enlarged horizon is used.

## Results and uncertainty

{result}

Both methods have zero healthy-run notifications over {m['healthy_service_hours']:g} service-hours. That denominator differs from all-run notification precision. The report retains paired and unpaired 500-resample whole-run bootstrap intervals, with correlated services kept together. These describe one simulator family, not production or cross-domain efficacy. See DETECTOR-UPGRADE.md for the explicit change and rejected trial.

## Responses and measurement boundaries

The action/no-action preview shares demand, noise and history until an allowlisted simulator intervention. Benefits follow encoded assumptions; deferred optional work is reported with successful transactions. No real remediation executes.

Native tests and isolated authenticated HTTP trials are regenerated for the current source. Queue acknowledgement excludes later inference; engine-batch time excludes queue waiting. Client/server share the VM, generation is off during timing, and short trials do not establish WAN/browser latency or maximum sustained capacity. Local Granite generation is separate and asynchronous. Historical benchmark runs remain identified as history.
''')
p=P/'SUMMARY.md';s=p.read_text(encoding='utf-8')
s=s.replace('Frozen v3 model','Frozen V5 model')
s=s.replace('A validation-selected threshold guard and persistence rules produce an incident.','Initial threshold warnings are preserved; a calibrated model filters only low-risk persistent repeats, and observed breach limits bypass filtering.')
s=s.replace('Forecast + threshold guard','Threshold warning + risk-aware repeat triage')
s=re.sub(r'\| Current page policy \|.*?\n', '| Current notification policy | Initial threshold warnings retained; ML risk gate for persistent repeats; observed-limit bypass | Independent model paging disabled; 60-second rechecks prevent permanent suppression |\n',s)
s=re.sub(r'\| Future breach model \|.*?\n', '| Future breach model | StandardScaler + LogisticRegression(C=0.1), separate sigmoid calibration | Chosen among five candidates for notification quality; risk supports repeat triage |\n',s)
s=re.sub(r'The main experiment uses 60 training runs.*?80000-series seeds\.', 'The main experiment uses 240 training, 60 calibration, 120 validation and 180 predeclared fresh final runs. Final seeds are 500000-series, generated after model/protocol freeze. Twelve separate abrupt stress runs use 520000-series seeds. V1-V4 are retained development history.',s)
s=re.sub(r'Final v3 result:.*?all denominators are published\.', 'Final V5 result: '+result+' This is a modest within-simulator precision improvement with unchanged measured early detection. Whole-run paired intervals and all denominators are published; real-world superiority is unproven.',s)
s=s.replace('Thirty-seven regression tests passed natively.',f"{c['tests_run']} regression tests passed natively.")
s=s.replace('The final model is frozen at version three.','The final model is frozen at version five.')
s=s.replace('Run notebook 01 for main training, calibration, selection and evaluation.','Run notebook 06 for fitting, calibration, validation selection and frozen fresh evaluation; notebook 01 reviews the resulting unchanged model.')
s=s.replace('| Training/evaluation rules |','| Current detector upgrade | `docs/DETECTOR-UPGRADE.md`, `notebooks/06_detector_upgrade.executed.ipynb` |\n| Training/evaluation rules |')
write('SUMMARY.md',s)
p=P/'docs/TECHNICAL-DESIGN.md';s=p.read_text(encoding='utf-8')
s=s.replace('Fit three forecasting candidates','Fit five risk candidates').replace('Calibrated boosted tree + threshold guard','Calibrated risk + repeat triage')
s=re.sub(r'Notebook 01 executes fitting.*?These are reproducible experiments, not screenshots of unexecuted code\.', 'Notebook 06 executes current V5 fitting, calibration, validation selection, hash freeze and fresh final evaluation. Notebook 01 reviews the unchanged artifacts; 02 tests and times the engine; 03 verifies the suite, actual HTTP path and native Granite; 04 collects separate original service measurements; 05 retains optional ONNX preparation. Saved outputs and records remain public. Earlier V3/V4 outputs are labeled history.',s)
s=re.sub(r'- \*\*Seven-leaf histogram gradient boosting:\*\*.*?accuracy\.', '- **Calibrated logistic risk:** standardization and LogisticRegression(C=0.1), selected among five candidates by the declared validation notification objective. Separate sigmoid calibration uses different runs. Higher point PR-AUC alone does not decide notification policy; production calibration remains unproven.',s)
s=re.sub(r'- \*\*Threshold guard:\*\*.*?improve\.', '- **Initial warning preservation:** fixed thresholds retain their first 3-of-5 warning. The learned score can filter only persistent repeats; observed breach limits bypass the filter. Shared 60-second rechecks correct permanent suppression. Independent forecast paging is disabled.',s)
s=s.replace('both use 60 event-time seconds in v3. Every detector shares persistence, cooldown and matching rules.','both use 60 event-time seconds. Every detector uses the shared scheduler and matching rules; V5 applies learned triage only to repeats.')
write('docs/TECHNICAL-DESIGN.md',s)
p=P/'docs/DEPLOYMENT.md';s=p.read_text().replace('## Audited v3 update','## Current audited update').replace('cg-2026-10-17-v3','cg-2026-10-17-v5');write('docs/DEPLOYMENT.md',s)
p=P/'docs/RUBRIC-EVIDENCE.md';s=p.read_text().replace('Five executed notebooks','Six executed notebooks').replace('latest v3 results','latest V5 results').replace('v1/v2 reports are development history','V1-V4 reports are development history');write('docs/RUBRIC-EVIDENCE.md',s)
print('Frozen methods, upgrade evidence and detailed explanation updated.')
