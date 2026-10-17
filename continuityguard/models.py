"""Versioned novelty and future-breach inference; never treat novelty as probability."""
from pathlib import Path
import hashlib
import json
import joblib
import numpy as np
from scipy.special import logit
from .features import FEATURE_NAMES

class ModelBundle:
    def __init__(self, directory):
        directory = Path(directory)
        manifest = json.loads((directory / "manifest.json").read_text())
        content = (directory / "models.joblib").read_bytes()
        if hashlib.sha256(content).hexdigest() != manifest["sha256"]:
            raise RuntimeError("Model integrity mismatch")
        self.manifest = manifest
        self.state = joblib.load(directory / "models.joblib")
        if self.state["feature_names"] != FEATURE_NAMES:
            raise RuntimeError("Feature schema mismatch")

    def predict(self, values):
        values = np.atleast_2d(values)
        raw = self.state["forecast"].predict_proba(values)[:, 1]
        if self.state.get("calibrator") is not None:
            p = self.state["calibrator"].predict_proba(logit(np.clip(raw, 1e-6, 1-1e-6)).reshape(-1, 1))[:, 1]
        else:
            p = raw
        novelty = -self.state["novelty"].score_samples(values)
        reference = self.state["normal_novelty"]
        percentile = np.searchsorted(reference, novelty, side="right") / len(reference)
        return p, novelty, percentile

    def flags(self, probability, novelty):
        policy = self.state["policy"]
        forecast = probability >= policy["forecast_threshold"]
        anomaly = novelty >= policy["novelty_threshold"]
        if policy["mode"] == "forecast":
            return forecast
        if policy["mode"] == "novelty":
            return anomaly
        return forecast | anomaly

    def decision_flags(self, probability, novelty, values):
        from .evaluation import static_flags,confirmed_flags
        if self.state['policy']['mode']=='repeat_filtered':
            return static_flags(np.atleast_2d(values))
        if self.state['policy']['mode']=='risk_filtered':
            values=np.atleast_2d(values)
            return (probability>=self.state['policy']['forecast_threshold']) | (static_flags(values) & (probability>=self.state['policy']['warning_gate'])) | confirmed_flags(values)
        if self.state['policy']['mode'] == 'guarded_forecast':
            return (probability >= self.state['policy']['forecast_threshold']) | static_flags(np.atleast_2d(values))
        return self.flags(probability, novelty)

    def refresh_flags(self, probability, values):
        from .evaluation import repeat_refresh_flags
        values=np.atleast_2d(values)
        if self.state['policy']['mode']!='repeat_filtered':return np.ones(len(values),dtype=bool)
        return repeat_refresh_flags(probability,values,self.state['policy']['warning_gate'],self.state['policy'].get('trend_guard',False))

def evidence(event, vector):
    """Measurements and slopes are inspectable evidence, not model attribution."""
    candidates = [
        (event["pool_used"] / .8, "E1", "Connection pool occupancy", round(event["pool_used"] * 100, 1), "%"),
        (event["retry_rate"] / .15, "E2", "Retry rate", round(event["retry_rate"] * 100, 1), "%"),
        (event["queue_depth"] / 15, "E3", "Waiting queue", round(event["queue_depth"], 1), "requests"),
        (event["memory_used"] / .6, "E4", "Memory occupancy", round(event["memory_used"] * 100, 1), "%"),
        (event["latency_p95_ms"] / 800, "E5", "Latency p95", round(event["latency_p95_ms"], 1), "ms"),
    ]
    return [{"id": row[1], "label": row[2], "value": row[3], "unit": row[4]} for row in sorted(candidates, reverse=True)[:3]]

RUNBOOKS = {
    "pool": {"id": "RB-POOL", "title": "Investigate database connection pressure", "action": "defer_batch", "steps": ["Inspect connection occupancy and queue growth.", "Check for stuck or long-running database requests.", "Preview deferring optional sandbox reporting work.", "Preserve urgent-results traffic and review recovery measurements."]},
    "retry": {"id": "RB-RETRY", "title": "Investigate a dependency retry cascade", "action": "cap_retries", "steps": ["Inspect retry rate and dependency latency.", "Check the affected dependency before restarting services.", "Preview a bounded retry policy in the sandbox.", "Verify reduced failures and the cost to deferred work."]},
    "memory": {"id": "RB-MEMORY", "title": "Investigate resource growth", "action": "none", "steps": ["Inspect the observed memory trend.", "Correlate growth with recent workload changes.", "Collect diagnostics for operator review.", "Do not automatically restart critical services."]},
}

def diagnosis(event):
    if event["retry_rate"] > .12:
        return "retry", RUNBOOKS["retry"]
    if event["memory_used"] > .5 and event["pool_used"] < .79:
        return "memory", RUNBOOKS["memory"]
    return "pool", RUNBOOKS["pool"]
