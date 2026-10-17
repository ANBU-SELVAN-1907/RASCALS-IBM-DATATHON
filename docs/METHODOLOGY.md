# Frozen evaluation protocol

## Data and prediction target

The original simulator produces one aggregate per service per second for four services. These are synthetic request/failure counts, latency summaries, queue, pool, retries, CPU and memory. They are not real hospital transactions. The separate original measured-service experiment in notebook 04 does not train or validate this predictor.

The forecast target is a new service-objective breach in the next 60 event-time seconds. A breach requires p95 latency above 1,000 ms or observed failures/requests above 10% for three consecutive windows. Already-breached windows and windows without a full future horizon are excluded from forecast fitting and point metrics. Incident evaluation processes complete runs, including misses and late outcomes.

Twenty-six features use only current/past observations: eight values, two ratios, six slopes, six means and four service indicators. No scenario, seed, onset, fault metadata, future value or target enters a predictor. Service identity is declared context. A gap above five seconds resets causal windows and notification state.

## Whole-run separation

| Split | Runs | Seed minimum / maximum | Purpose |
|---|---:|---|---|
| train | 240 | 300000 / 300539 | Fit five candidate models |
| calibration | 60 | 310000 / 310509 | Separate sigmoid and novelty reference |
| validation | 120 | 320000 / 320519 | Choose model and repeat gate |
| test | 180 | 500000 / 500529 | Frozen fresh evaluation |
| stress | 12 | 520000 / 520011 | Unseen abrupt-failure checks |

The sampling unit is a run; services in a run are dependent. V1-V4 were inspected during development and remain labeled history. V4 initial-warning filtering improved precision but lost fresh-test early recall, so it was rejected. V5 preserves first warnings and uses its own predeclared fresh final range. Model/protocol hashes were frozen before test generation. Repeating the same seeds later is reproduction, not additional independent validation.

## Models and validation selection

Five candidates: standardized logistic regression at C=0.1 and C=1, and histogram gradient boosting with 7, 15 and 31 leaves. Separate sigmoid calibration fits probability logits on calibration runs. Isolation Forest learns healthy variation and is evaluated/displayed separately.

V5 compares repeat gates from 0 to 0.97 and optional rising-trend bypass. Initial warnings are never filtered. Selection first requires validation precision and early recall at least as high as corrected static thresholds, then maximizes `0.65 * early recall + 0.35 * precision - 2 * max(0, healthy false alarms/hour - 0.5)`. This is our declared engineering objective, not IBM's judging formula. Selected: `logistic_C0.1`, repeat risk gate 0.97, trend bypass False.

## Notification lifecycle and fair comparison

Static thresholds are p95 >800 ms, pool >90%, error fraction >8%, or CPU >90%. They are a documented engineering baseline, not an exhaustive search of all threshold designs. Robust statistics uses median/MAD positive deviations and a validation-selected cutoff. Isolation Forest uses a fixed healthy-reference quantile.

Every comparator uses 15-observation warmup, 3-of-5 persistence, 30-second cooldown and a bounded 60-second episode recheck. V5 additionally allows learned risk to withhold low-risk repeats. Observed breach limits bypass filtering. Independent model paging is disabled; the score supports repeat triage and inspection.

Breaches separated by at most 15 seconds form one incident. Matching remains one alert per incident from 60 seconds before onset through 15 seconds after incident end. Every unmatched notification counts against precision, including extra repeats, non-breaching faults and too-early warnings. No retrospective point adjustment or enlarged horizon is used.

## Results and uncertainty

Early warnings: 130/135 versus 130/135; precision 45.3% versus 43.5%; median early lead 11s versus 11s; misses 1 versus 1; unmatched notifications 162 versus 174.

Both methods have zero healthy-run notifications over 30 service-hours. That denominator differs from all-run notification precision. The report retains paired and unpaired 500-resample whole-run bootstrap intervals, with correlated services kept together. These describe one simulator family, not production or cross-domain efficacy. See DETECTOR-UPGRADE.md for the explicit change and rejected trial.

## Responses and measurement boundaries

The action/no-action preview shares demand, noise and history until an allowlisted simulator intervention. Benefits follow encoded assumptions; deferred optional work is reported with successful transactions. No real remediation executes.

Native tests and isolated authenticated HTTP trials are regenerated for the current source. Queue acknowledgement excludes later inference; engine-batch time excludes queue waiting. Client/server share the VM, generation is off during timing, and short trials do not establish WAN/browser latency or maximum sustained capacity. Local Granite generation is separate and asynchronous. Historical benchmark runs remain identified as history.
