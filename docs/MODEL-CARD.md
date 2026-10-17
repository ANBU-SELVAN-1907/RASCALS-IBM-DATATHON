# Model card: cg-2026-10-17-v3

**Purpose:** operational support for a new service-objective breach within 60 event-time seconds, in the controlled simulator. Not a clinical system or validated real hospital risk score.

**Chosen model:** boosted_trees_7_leaves; HistGradientBoostingClassifier with maximum 7 leaves, 120 iterations, learning rate .06 and L2=1. Sigmoid calibration fits separate runs. Isolation Forest has 100 trees and max_samples=256. The selected policy is `{'mode': 'guarded_forecast', 'forecast_threshold': 0.97, 'novelty_threshold': 0.6049514944657695, 'novelty_quantile': 0.995}`. In guarded_forecast mode, forecast >=0.97 OR static thresholds feeds shared persistence; novelty stays separately visible.

**Features:** 26 causal values: eight measurements; two normalized ratios; six 15-observation slopes; six means; four service indicators. Warmup is 15 observations. A gap exceeding five event-time seconds resets the affected service's feature and persistence windows. Out-of-order/nonfinite data is rejected without advancing valid state.

**Environment:** native s390x Jupyter, Python 3.12.15. Exact package versions, SHA-256 and fitting timestamp are in the manifest. Train/calibration/validation/final test use 60/18/24/60 separate runs. Final seeds are 70000-series; v1/v2 inspected results are development history.

**Measured result:** On 60 fresh synthetic runs, both ContinuityGuard and static thresholds warned before 31/43 service incidents. Median early lead was 13 seconds versus 10. Precision was 59.3% versus 60.0%; missed incidents were 11 versus 10. This does not establish consistent ML superiority. See `RESULTS.md` for complete denominators, precision, misses, all-run unmatched alerts and whole-run bootstrap intervals. Calibration still shows overconfidence. Do not claim statistically established model superiority or interpret scores as production outage probabilities.

**Failure handling:** missing receipts show stale status; a gap rewarms; model failure or nonfinite output uses explicit degraded static fallback. Consumer exceptions are counted and health becomes degraded. Sudden unseen incidents had no early warnings. External distributions require authorization, validation and calibration.

**Explanation:** Granite 4.0 H 350M base via the supplied llama.cpp runtime generates one of two verified wordings under a JSON grammar. Every evidence ID in the summary is required. This is constrained wording, not unrestricted causal reasoning. A labeled deterministic fallback covers invalid/unavailable generation. No real action executes.

**Security:** trusted joblib artifacts only. The hash detects mismatch, not replacement of both manifest and artifact. Native image provenance and external audit anchoring are future hardening work. Measurements shown in an incident are evidence, not SHAP attribution or proven root cause. Declared service priorities are software policy, not learned clinical risk.
