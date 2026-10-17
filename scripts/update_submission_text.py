"""Keep submission claims synchronized with the frozen current artifacts."""
from pathlib import Path
import json

P=Path(__file__).resolve().parents[1]
read=lambda f:json.loads((P/f).read_text())
r=read('artifacts/report.json');m=r['systems']['ContinuityGuard'];b=r['systems']['Static thresholds']
check=read('artifacts/correctness-report.json');h=read('artifacts/http-benchmark.json')['trials'][-1]
team=read('submission/team.json');manifest=r['manifest']
pct=lambda v:f'{100*v:.1f}%'
def write(name,value):(P/name).write_text(value,encoding='utf-8')
table='| Detector | Early recall | Precision | Median early lead | Late | Missed |\n|---|---:|---:|---:|---:|---:|\n'
for name,s in r['systems'].items():table+=f"| {name} | {pct(s['early_warning_recall'])} | {pct(s['incident_precision'])} | {s['median_early_lead_seconds']:g} s | {s['late_detections']} | {s['missed']} |\n"
result=f"On {r['split']['test_runs']} predeclared fresh synthetic runs, ContinuityGuard warned early for {m['early_detections']}/{m['incidents']} service incidents versus {b['early_detections']}/{b['incidents']} for static thresholds. Precision was {pct(m['incident_precision'])} versus {pct(b['incident_precision'])}; median early lead was {m['median_early_lead_seconds']:g}s versus {b['median_early_lead_seconds']:g}s; misses were {m['missed']} versus {b['missed']}. Unmatched notifications were {m['unmatched_alerts_all_runs']} versus {b['unmatched_alerts_all_runs']}. This is a modest measured precision gain within one simulator family, not universal superiority."
write('docs/RESULTS.md',f'''# Current results: {manifest['version']}

{result}

{table}
The V5 final evaluation uses predeclared 500000-series seeds, generated only after the model/protocol freeze. V1-V4 are retained development history. All detectors share the scheduler: 3-of-5 persistence, 30-second cooldown and a 60-second persistent-episode recheck. V5 retains initial threshold warnings and uses learned risk only to filter repeats; observed breach limits bypass the filter. Matching stays at 60 seconds before onset through 15 seconds after incident end. Services within a run are correlated. Paired whole-run bootstrap intervals are retained in report.json/paired_bootstrap.

There were {m['unmatched_alerts_all_runs']} unmatched model-policy alerts overall. No alerts occurred in {m['healthy_service_hours']:g} healthy service-hours, which does not prove a zero real false-alarm rate. The abrupt-failure stress set detected {r['unseen_abrupt_failures']['detected']}/{r['unseen_abrupt_failures']['incidents']} incidents and warned before none.

Forecast PR-AUC: {r['forecast_test']['pr_auc']:.4f}, positive prevalence {pct(r['forecast_test']['positive_prevalence'])}, Brier {r['forecast_test']['brier_score']:.5f}. Reliability bins are retained; production calibration is unverified. Run-bootstrap intervals resample whole runs, not individual correlated services: see `report.json/run_bootstrap` (500 replicates). These intervals describe uncertainty within the simulator family only.

{check['tests_run']} tests passed on {check['architecture']}, with {check['failures']} failures, {check['errors']} errors and {check['skipped']} skipped. The actual authenticated local HTTP trial processed {h['processed_events']}/{h['offered_events']} offered events at 100 events/s over 10 seconds. Queue-ack p95 was {h['p95_http_queue_ack_ms']:g} ms; engine-batch p95 was {h['p95_engine_batch_ms']:g} ms. Queue acknowledgement excludes subsequent inference; engine timing excludes queue waiting. Completion throughput includes confirmation polling. Client and server share the VM, fixtures are synthetic, generation is off, and no WAN/browser or sustained peak-capacity claim follows.

The earlier direct-engine measurements are retained, including the slower concurrent-workload repeat. Use the named report and exact boundary instead of quoting the fastest number as a platform guarantee.
''')
write('README.md',f'''# {team['project_title']}

## ContinuityGuard

**Theme:** Real-Time AI for Critical Decisions / System Anomaly Detection.

**Team:** {'; '.join(team['members'])}. **Institution:** {team['institution']}.

Detect developing system faults from incoming telemetry, inspect an evidence-linked alert, and preview an operator response. Actual model training, testing, inference and constrained Granite generation run natively on IBM LinuxONE Community Cloud. The hospital-service scenario explains the beneficiaries; it is not clinical decision-making.

**Scope:** an operational research prototype with controlled synthetic telemetry. It is not production hospital validation and has not prevented a measured real outage. There is no guarantee of full marks, universal detection or superiority over every baseline.

## Review the submission

- [Pitch PDF](submission/RASCALS-ContinuityGuard-Pitch.pdf), [narrated evidence walkthrough](submission/RASCALS-ContinuityGuard-Walkthrough.mp4), [form answers](submission/FORM-ANSWERS.md).
- [Rubric evidence map](docs/RUBRIC-EVIDENCE.md), [technical design](docs/TECHNICAL-DESIGN.md), [current results](docs/RESULTS.md), [judging questions](docs/JUDGE-QUESTIONS.md).
- [Native execution proof](evidence/jupyter-ai-proof.json), [container verification](evidence/linuxone-verification.json), [restart check](evidence/restart-check.json), [HTTP measurement](artifacts/http-benchmark.json).
- [Source/resource credits](docs/ATTRIBUTIONS.md), [mandatory lab evidence](docs/LABS.md), [remaining submission actions](submission/FINAL-CHECKLIST.md).

## Current measured result

{result}

{table}
![Frozen V5 precision and recall comparison](artifacts/benchmark.png)

The current model is **{r['selected_model']}**, with standardization, separate sigmoid calibration and a **{r['policy']['mode']}** policy. Initial threshold warnings are retained. Learned risk >= **{r['policy']['warning_gate']}** or observed latency/error breach permits a persistent repeat notification. Independent forecast paging is disabled; the learned score is used for repeat triage. Isolation Forest is a separate novelty signal; novelty is not an outage probability or an independent paging trigger. The 60-second forecast and early matching window agree.

{check['tests_run']} native tests passed. Actual local authenticated HTTP ingestion processed {h['processed_events']}/{h['offered_events']} events at 100 offered events/s in a 10-second trial. Read [measurement boundaries and uncertainty](docs/RESULTS.md) before quoting latency. Model hash and environment are in [manifest](artifacts/manifest.json).

![Historical V3 operator-console screenshot](evidence/dashboard.png)

Historical V3 interface view; current V5 numerical results are above and in the frozen report/API evidence. The screenshot is retained as history, not represented as a new V5 capture.

## Reproduce through LinuxONE Jupyter

Open `shared/continuityguard/notebooks` in the supplied native s390x environment:

1. `01_train_and_evaluate.ipynb`: review the unchanged frozen model and results; original V3 training is archived.
2. `02_test_and_benchmark.ipynb`: correctness and direct-engine timing.
3. `03_engineering_audit.ipynb`: final suite, actual isolated HTTP integration and local predictive/generative proof.
4. `04_original_measurements.ipynb`: original measured service timings and a separate novelty fit.
5. `05_toolkit_readiness.ipynb`: separate Random Forest and checked ONNX export; no entitled Toolkit execution claim.
6. `06_detector_upgrade.ipynb`: actual V5 fitting, validation selection, model/protocol freeze and first fresh evaluation.

Each source notebook has a retained executed copy and success record. Rerunning frozen final seeds is reproduction, not a new independent test. V1-V4 development reports remain in artifacts, including the rejected V4 precision/recall tradeoff. See [methodology](docs/METHODOLOGY.md), [data card](docs/DATA-CARD.md) and [model card](docs/MODEL-CARD.md).

```bash
python scripts/execute_notebook.py notebooks/06_detector_upgrade.ipynb
python scripts/execute_notebook.py notebooks/01_train_and_evaluate.ipynb
python scripts/execute_notebook.py notebooks/02_test_and_benchmark.ipynb
python scripts/execute_notebook.py notebooks/03_engineering_audit.ipynb
python scripts/validate_submission.py
```

## Open Jupyter and the dashboard

Assigned VM: **https://148.100.99.173:38888/lab** for Jupyter and **https://148.100.99.173:8443** for the dashboard. Verify the short-lived certificate fingerprint in [public access](docs/PUBLIC-ACCESS.md) manually, then enter the appropriate private token. Both run on IBM LinuxONE. SSH is also supported:

```powershell
ssh -i "C:\\path\\to\\your-key.pem" -N -o ExitOnForwardFailure=yes -L 127.0.0.1:8080:127.0.0.1:8080 -L 127.0.0.1:38888:127.0.0.1:38889 linux1@YOUR_VM_IP
```

Open `http://127.0.0.1:8080` for the app, or `http://127.0.0.1:38888/lab` for Jupyter. Their tokens are different. On the VM, retrieve the app token with `sudo podman exec continuityguard cat /home/ibm-user/cg-state/.access-token`. Never publish a private key, token, state database or authenticated URL.

Choose database connection pressure and 4x replay. Inspect an incident, request an explanation and preview the sandbox response. The initial warning follows operational thresholds; ML governs repeat triage. A low displayed risk does not suppress the first threshold warning. In Evaluation evidence, inspect the live platform controls and verify the audit journal.

External input is a separate session: stop/reset the sandbox using `POST /api/external-session` (or the External stream button), then send validated windows to `POST /api/events`. Client-supplied synthetic provenance is overwritten. Response previews are disabled for external input. [Adapter and schema](docs/EXTERNAL-INPUT.md) explain the limits; forecasts require validation on real deployment data.

## Deploy and inspect

```bash
python3 scripts/deploy_linuxone.py /absolute/project/path
# Deliberate update, preserving state and a stopped rollback container:
python3 scripts/deploy_linuxone.py /absolute/project/path --replace
python3 scripts/verify_linuxone.py /absolute/project/path --restart --demo
```

The host is RHEL 9.8, with Podman. The app is UID 1000, read-only root, capped CPU/memory/PIDs, capabilities dropped and no-new-privileges. Its backend binds loopback; SSH or an authenticated TLS proxy provides access. Host networking is an explicit tradeoff. [Deployment](docs/DEPLOYMENT.md) records the pinned-image compatibility path and restart behavior. Do not run a development server on occupied port 8080; use `CG_PORT=8081` for an independent instance.

## Repository organization

`continuityguard/` contains the simulator, features, models, runtime, API and interface. `notebooks/` holds native experiments and executed evidence. `tests/` exercises failure boundaries. `artifacts/` retains trained models and measured reports. `evidence/` contains redacted actual execution/deployment proof. `docs/` explains methods and limits. `submission/` holds team metadata, PDF/video and form materials. `scripts/` provides reproducible execution, deployment and packaging.

## Originality and assistance

The contribution is this specific integration of warning evidence, service priorities, constrained local generation and paired response preview. Established algorithms are credited; no world-first claim is made. Codex assisted architecture, coding, verification and preparation. The team must understand, review and disclose that assistance under organizer guidance. LinuxONE/s390x execution does not prove z/OS integration or AI accelerator use.
''')
write('docs/MODEL-CARD.md',f'''# Model card: {manifest['version']}

**Purpose:** operational support for a new service-objective breach within 60 event-time seconds, in the controlled simulator. Not a clinical system or validated real hospital risk score.

**Chosen model:** {r['selected_model']}; StandardScaler followed by LogisticRegression(C=0.1, max_iter=500, random_state=17), selected among five candidates on the declared validation objective. Sigmoid calibration fits separate runs. Isolation Forest has 100 trees and max_samples=256. The selected policy is `{r['policy']}`. Initial static warnings are preserved. The learned gate filters only persistent repeats; observed breach limits bypass it. The 1.01 forecast threshold is an explicit disabled sentinel: there is no independent forecast page. Novelty stays separately visible.

**Features:** 26 causal values: eight measurements; two normalized ratios; six 15-observation slopes; six means; four service indicators. Warmup is 15 observations. A gap exceeding five event-time seconds resets the affected service's feature and persistence windows. Out-of-order/nonfinite data is rejected without advancing valid state.

**Environment:** native s390x Jupyter, Python 3.12.15. Exact package versions, SHA-256 and fitting timestamp are in the manifest. Train/calibration/validation/final test use 240/60/120/180 separate runs. Final seeds are 500000-series, generated after freeze; V1-V4 inspected results are development history.

**Measured result:** {result} See `RESULTS.md` for complete denominators, precision, misses, all-run unmatched alerts and whole-run bootstrap intervals. Reliability bins and remaining calibration limits are retained. Do not claim statistically established model superiority or interpret scores as production outage probabilities.

**Failure handling:** missing receipts show stale status; a gap rewarms; model failure or nonfinite output uses explicit degraded static fallback. Consumer exceptions are counted and health becomes degraded. Sudden unseen incidents had no early warnings. External distributions require authorization, validation and calibration.

**Explanation:** Granite 4.0 H 350M base via the supplied llama.cpp runtime generates one of two verified wordings under a JSON grammar. Every evidence ID in the summary is required. This is constrained wording, not unrestricted causal reasoning. A labeled deterministic fallback covers invalid/unavailable generation. No real action executes.

**Security:** trusted joblib artifacts only. The hash detects mismatch, not replacement of both manifest and artifact. Native image provenance and external audit anchoring are future hardening work. Measurements shown in an incident are evidence, not SHAP attribution or proven root cause. Declared service priorities are software policy, not learned clinical risk.
''')
blocks=[
"Hospital digital services share infrastructure. Developing pool exhaustion, retry cascades or resource pressure can delay access to results and disrupt dependent services before an operator has a useful warning. ContinuityGuard addresses system availability: identify abnormal activity as telemetry arrives, warn of an approaching service-objective breach, show affected software services and provide evidence-linked investigation steps. Hospital IT operators are the target users. The prototype uses controlled synthetic service telemetry; it does not use patient data or make clinical decisions.",
f"A validated bounded queue feeds causal rolling features on LinuxONE. A calibrated logistic model scores near-term breach risk. Initial threshold warnings are retained; ML filters low-risk repeats, while observed breach limits bypass filtering. Isolation Forest separately scores novelty. Persistent risk creates incidents with measurements, declared dependencies and runbooks. Local Granite generates schema-constrained wording with complete evidence IDs and a labeled fallback. A paired simulator previews allowlisted action versus no action under identical demand. Jupyter separates whole-run training, calibration, validation and fresh final testing. The frozen V5 test warned before {m['early_detections']}/{m['incidents']} incidents, with median early lead {m['median_early_lead_seconds']:g}s versus {b['median_early_lead_seconds']:g}s for thresholds; precision was {pct(m['incident_precision'])} versus {pct(b['incident_precision'])}. These are synthetic results, not proof of consistent superiority.",
f"Training, testing, scoring, novelty, local Granite, API processing and SQLite journaling execute natively on our LinuxONE Community Cloud s390x VM. Six saved Jupyter notebooks retain outputs, model hashes and failure tests. Podman runs the app as UID 1000 with a read-only root, CPU/memory/PID limits, dropped capabilities, no-new-privileges and authenticated TLS/SSH access. {check['tests_run']} native tests passed. A real local HTTP/queue/journal trial processed {h['processed_events']}/{h['offered_events']} synthetic window events at 100 offered events/s over 10 seconds. Platform screenshots and verification outputs are public. The two relevant provided sample labs executed before project work; exact organizer prerequisite mapping still needs confirmation. We do not claim z/OS integration, AI hardware acceleration or production-scale performance.",
"Hospital IT operators benefit from one reviewable path from warning to evidence, software-service priority, investigation and response preview. The aim is earlier attention to developing faults and clearer operational tradeoffs, supporting the availability of essential digital services. The preview reports modeled successful urgent-results transactions and deferred optional work together, with no real remediation. The implementation is reusable for authorized service telemetry after domain validation and calibration. Current value is a working, tested LinuxONE prototype and reproducible evaluation, not a measured patient outcome or proven real-world outage reduction. The latest results include misses, false alerts, baseline comparison and uncertainty rather than claiming perfect detection.",
"https://github.com/linuxone-community-cloud/jupyter-lab-ml\nhttps://scikit-learn.org/\nhttps://numpy.org/\nhttps://github.com/IBM/ai-toolkit-for-z-and-linuxone\nhttps://onnx.ai/\nhttps://github.com/onnx/sklearn-onnx\nhttps://scipy.org/\nhttps://joblib.readthedocs.io/\nhttps://fastapi.tiangolo.com/\nhttps://www.starlette.io/\nhttps://www.uvicorn.org/\nhttps://docs.pydantic.dev/\nhttps://jupyter.org/\nhttps://pandas.pydata.org/\nhttps://matplotlib.org/\nhttps://psutil.readthedocs.io/\nhttps://www.sqlite.org/\nhttps://podman.io/\nhttps://github.com/abetlen/llama-cpp-python\nhttps://github.com/ggml-org/llama.cpp\nhttps://huggingface.co/ibm-granite/granite-4.0-h-350m-base\nhttps://github.com/python-pillow/Pillow\nhttps://github.com/pypdfium2-team/pypdfium2\nhttps://github.com/imageio/imageio-ffmpeg\nhttps://ffmpeg.org/\nFull credits: https://github.com/ANBU-SELVAN-1907/RASCALS-IBM-DATATHON/blob/main/docs/ATTRIBUTIONS.md"
]
titles=['Problem','Solution overview','IBM Z / LinuxONE use','Value and beneficiaries','Open-source resources']
assert all(len(b)<=1024 for b in blocks),[len(b) for b in blocks]
write('submission/FORM-ANSWERS.md','# '+team['project_title']+'\n\nSolution: ContinuityGuard. Team: '+ '; '.join(team['members'])+'. Institution: '+team['institution']+'.\n\n'+''.join('## '+title+'\n\n```text\n'+block+'\n```\n\n' for title,block in zip(titles,blocks))+'Copy each block into its corresponding portal field. Upload the reviewed PDF and a <=3-minute accessible YouTube/Vimeo video. Public repository: https://github.com/ANBU-SELVAN-1907/RASCALS-IBM-DATATHON\n\nManual portal submission and prerequisite mapping confirmation remain team actions.\n')
print('Synchronized current results and form lengths:',[len(b) for b in blocks])
questions=[
('What problem does this solve?','Developing system faults can disrupt dependent essential software services. We support IT operators with streaming risk, retained measurements, runbooks and a response preview; no clinical decisions.'),
('What is the exact title and team?',team['project_title']+' / '+team['solution_name']+'. '+ '; '.join(team['members'])+'. '+team['institution']+'.'),
('What actually runs on LinuxONE?','The native Jupyter training/test kernels, simulator, causal features, forecast, novelty estimator, API, SQLite journal and local Granite. The browser is a client through TLS or SSH. Show the live platform proof, model hash and executed notebooks.'),
('Why LinuxONE rather than a logo in the slides?','Prediction and local generation execute on s390x beside the prototype telemetry/journal, without exporting telemetry to a remote model API. Containers and verified resource/security controls are applied to this actual runtime. No comparative speed superiority is claimed.'),
('Is this IBM Machine Learning for z/OS?','No. This is open-source AI on LinuxONE Community Cloud Linux. We do not claim z/OS integration, z/OS transactions, Telum/Spyre acceleration or certification.'),
('What does Jupyter prove?','Six native notebooks retain fitting, calibration, selection, evaluation, tests, actual HTTP integration and local generation. Their executed copies, success records and architecture/model outputs are in the repository.'),
('Have both mandatory labs been completed?','The Churn multi-model and Loan predictive/generative sample notebooks executed before original project work. Their timestamps and source commit are recorded. The organizer must confirm the exact mapping to its assigned prerequisites; execution alone is not a course-completion certificate.'),
('What is learned?',f"{r['selected_model']} forecasts a new sustained breach within 60 event-time seconds. Isolation Forest learns healthy variation for a separate novelty score. Sigmoid calibration uses separate runs; production calibration is unproven."),
('Why this model?','Five candidates and alert-policy variants compete on a declared validation objective. Scaled logistic regression supplies a compact, calibratable score; other candidates include three boosted-tree sizes. We do not call them universally best.'),
('What triggers an alert?','Initial static warnings use 3-of-5 persistence after warmup. A 60-second episode recheck prevents permanent suppression. ML confirms whether a persistent repeat merits notification; observed breach limits bypass the learned filter. Independent forecast paging is disabled. Novelty remains separate.'),
('How much better is it?',result+' Report confidence intervals; do not claim a statistically established general advantage.'),
('Why retain AI if thresholds are competitive?','The model supplies a learned, calibratable score and novelty context, while the integration makes decisions inspectable. Current experiments do not justify replacing thresholds. More diverse authorized data and operational validation are needed to establish incremental ML value.'),
('What is new?','This original implementation connects causal warning features, software dependency priorities, evidence receipts, constrained local wording and a same-workload response preview. Algorithms are established; no world-first claim or prior-team code reuse.'),
('How is leakage controlled?','Whole runs and disjoint train/calibration/validation/test seeds; past/current features only; no fault metadata; separate calibration. V1-V4 inspected reports are development history. V5 freezes its protocol and model before new final runs.'),
('Why did the headline change?','V3 aligned the horizon. V4 filtering improved precision but lost early recall and was rejected. V5 preserves first threshold warnings and filters repeats. It freezes selection before new final evaluation; prior results remain published.'),
('Why zero healthy false alerts but low precision?',f"The zero applies only to {m['healthy_service_hours']:g} healthy service-hours. Overall precision also counts repeat, unmatched and non-breaching fault-run alerts. There were {m['unmatched_alerts_all_runs']} unmatched V5 notifications overall."),
('Can sudden faults be predicted?','The unseen abrupt stress test detected every tested service incident but warned before none. No precursor means no promised early warning.'),
('Does the diagnosis prove root cause?','No. A declared dependency map and heuristic measured-signal rules propose a suspected source. Service criticality is declared software policy, not learned clinical risk or causal proof.'),
('Does the preview prove outage prevention?','No. Paired branches share exogenous demand/noise and history until an allowlisted simulator action. Benefits follow intervention assumptions. No real host or service is modified.'),
('What does Granite add?','Local constrained wording tied to verified measurements and a runbook. Every evidence ID cited in the text is required. It has no shell tools and cannot execute remediation. Invalid/unavailable generation gets a labeled deterministic fallback.'),
('What happens when inference or storage fails?','Inference exceptions/nonfinite outputs enter explicit degraded static fallback. Consumer exceptions increment failed batches, preserve queue progress and make health degraded. No prediction percentage is invented. Reconcile upstream events after storage failure; this is not exactly-once delivery.'),
('What happens on missing or reordered data?','Receipt age shows stale status. A >5-second event gap resets per-service warmup and persistence. Old/out-of-order/nonfinite events are rejected without poisoning future state. Windows are bounded.'),
('Can external callers spoof a simulator result?','External input requires a separate session, cannot mix with the sandbox and has its provenance overwritten by the server. Paired previews are disabled for external incidents. Real deployment still requires authorized data and domain calibration.'),
('Is the journal tamper-proof?','No. It checks hash links and retains history across restart; externally retain a trusted head to detect whole-history replacement. Signed provenance and external anchoring would be production work.'),
('What do the latency numbers include?',f"The actual local HTTP test processed {h['processed_events']}/{h['offered_events']} synthetic fixture events at 100 offered events/s over 10 seconds. Queue-ack p95 {h['p95_http_queue_ack_ms']:g} ms excludes later processing; engine-batch p95 {h['p95_engine_batch_ms']:g} ms excludes queue wait. Client/server share the VM; no WAN/browser or maximum sustained-capacity claim."),
('What security controls were verified?','UID 1000, read-only root, CPU/memory/PID caps, dropped capabilities, no-new-privileges, loopback/SSH, schema/actual body limits, authentication and origin checks. Host networking and single-token access remain explicit prototype limits.'),
('How do you know the implementation works?',f"{check['tests_run']} native tests pass; inspect the actual test names/output. Additional HTTP, real Granite, container, restart and browser checks retain measured evidence. Passing tests does not prove absence of every bug."),
('What remains before adoption/submission?','Production adoption needs authorized real telemetry, domain evaluation/calibration, reviewed response steps, identity/operations hardening and reliability trials. Event submission still needs prerequisite mapping confirmation, reviewed YouTube/Vimeo hosting and manual portal entry.'),
('Was AI assistance used?','Yes. Codex assisted architecture, coding, orchestration, tests and submission preparation. The team must understand and disclose its work under organizer guidance. Do not claim unaided development or invent member contributions.'),
]
write('docs/JUDGE-QUESTIONS.md','# Defend the implementation in your own words\n\n'+''.join(f"{i}. **{q}** {a}\n\n" for i,(q,a) in enumerate(questions,1)))
# Keep the current short/extended walkthrough scripts synchronized.
import runpy
runpy.run_path(str(P / 'scripts/write_walkthrough_scenes.py'))
