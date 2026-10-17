# Model card

**Version:** cg-2026-10-17-v2. Integrity and package details: [manifest](../artifacts/manifest.json).

**Purpose:** rank risk of a new declared software-service breach in the next 60 event-time seconds in a controlled synthetic workload. Operational decision support; not a clinical system.

**Models:** scikit-learn HistGradientBoostingClassifier, 120 boosting iterations, maximum seven leaves per tree, learning rate 0.06, L2=1; a separate sigmoid calibrator; Isolation Forest with 100 trees and 256-sample subsampling for novelty. The source defines exact parameters. The final alert policy uses calibrated forecast score >=0.8 with persistence, selected on validation. Novelty remains separately visible.

**Inputs:** 26 causal numerical features: eight current measurements; queue/request and latency/request ratios; six 15-observation slopes; six means; four service-identity values. At least 15 observations are needed to issue model alerts. Older/out-of-order events are rejected rather than rewriting past decisions.

**Training environment:** Python 3.12.15, scikit-learn 1.9.0, NumPy 2.0.2, SciPy 1.13.1, joblib 1.6.0 on LinuxONE s390x. Full run manifests and executed Jupyter notebooks are included.

**Results:** 43/47 early detections, 4 missed, 61.4% incident precision, 37-second median early lead; zero observed alerts in 10 synthetic healthy service-hours. PR-AUC 0.8499, positive prevalence 0.05022, Brier score 0.01665. Calibration bins show remaining overconfidence, especially in intermediate/high scores. Do not interpret a displayed score as a hospital-specific outage probability.

**Failure modes:** sudden faults may have no precursor; novel workloads can shift the feature distribution; domain adaptation is untested; false alerts may burden operators. The independent abrupt stress set detected all 24 service incidents but warned before none.

**Interpretability:** the interface exposes current signals, score, novelty percentile and a declared dependency hypothesis. These displayed signals are operator evidence, not SHAP values or proven causal feature attribution. Service priorities are configured policy choices.

**Runtime fallback:** failed model inference is explicitly shown as degraded mode and uses static thresholds. No forecast percentage is fabricated when the model fails. Missing recent receipts show stale telemetry.

**Local generation:** IBM Granite 4.0 H 350M base, bundled in the organizer image, through llama.cpp. JSON grammar constrains generation to two evidence-grounded wording options and valid evidence/runbook IDs; these are validated again before display. This is deliberately limited generation, not unrestricted reasoning or autonomous remediation. Failure uses a labeled deterministic fallback. Model weights are not redistributed in this repository.

**Deployment restriction:** load only trusted joblib artifacts. SHA-256 checks detect mismatch against the manifest, but do not authenticate an attacker-replaced model and manifest pair. The application image supplies both. Production would need signed provenance, authorization, broader validation and monitored drift/retraining policies.
