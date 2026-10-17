# Detector upgrade: cg-2026-10-17-v5

## The actual improvement

Early warnings: 130/135 versus 130/135; precision 45.3% versus 43.5%; median early lead 11s versus 11s; misses 1 versus 1; unmatched notifications 162 versus 174.

These are paired results on 180 predeclared fresh synthetic runs. The benefit is fewer unmatched repeat notifications with the same observed early recall, median lead, late count and misses. It is a modest improvement within this simulator, not a claim of universal superiority or production outage prevention.

## What changed

1. A shared `AlertTracker` replaces the permanent latch. Persistent episodes are reviewed after 60 event-time seconds; 3-of-5 persistence and a 30-second cooldown remain. All detector comparisons use this scheduler.
2. The first threshold warning is preserved. Unlike the rejected V4 policy, low model confidence cannot filter that initial signal.
3. Calibrated standardized logistic regression predicts a 60-second breach risk. Only repeat triage uses its selected 0.97 gate. Observed latency/error breach limits bypass that filter. Validation selected `trend_guard=False`.
4. Independent forecast paging is disabled. `forecast_threshold=1.01` is an explicit disabled sentinel, not an attainable probability. Novelty remains separately displayed.

## Why this model

Two standardized logistic candidates and three histogram-boosting sizes were fitted on training runs, then sigmoid-calibrated on different runs. Selection used notification precision and early recall on validation, including a constraint to match or exceed the corrected static baseline on both. A model with higher point-level PR-AUC need not produce the best operational notification policy. The selected model is `logistic_C0.1`; its choice is not a claim that logistic regression is universally best.

## Freeze and fresh evaluation

Actual execution is retained in `notebooks/06_detector_upgrade.executed.ipynb`. The model and protocol hashes were written to `artifacts/freeze.json` before generating 500000-series final runs. Protocol, all validation options, split manifests and original final-test execution records are public. V1-V4 are retained development history, including V4's rejected precision/recall tradeoff.

The baseline also receives the lifecycle correction. Consequently the rise in recall relative to old V3 numbers cannot be attributed to ML; different seeds and a corrected scheduler prevent direct cross-version numerical comparison. Compare V5 against the baseline in the same V5 experiment.

## Uncertainty and ablation

The paired 500-resample whole-run precision-difference interval is 0.63 to 3.15 percentage points. The paired early-recall difference is zero for these sampled runs. Neither fact proves future non-inferiority or generalization beyond this simulator. `report.json/ablations` retains the no-ML-repeat-filter comparison.

The forecast point PR-AUC is 0.8179; this is a different metric from notification precision. The latter counts extra repeats, non-breaching fault warnings and out-of-window warnings as unmatched. Zero healthy-run alerts in 30 service-hours is not proof of a zero operational false-alarm rate.

## Verification

43 native tests cover the bounded refresh, initial-warning preservation, confirmed-limit bypass, offline/live parity, time gaps, malformed events, overload, consumer errors and model integrity. The current HTTP and local Granite proofs are regenerated after model promotion. Container restart persistence and model/source hashes are checked before publication. Historical UI screenshots are labeled; current numerical outputs come from saved reports and authenticated API evidence.
