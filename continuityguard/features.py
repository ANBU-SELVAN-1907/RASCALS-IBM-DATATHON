"""Causal bounded-window features shared by offline training and online inference."""
from collections import deque
from datetime import datetime
import numpy as np
from .simulation import SERVICES, LOOKBACK

RAW = ("latency_p95_ms", "pool_used", "queue_depth", "retry_rate", "cpu_used", "memory_used", "error_rate", "requests")
FEATURE_NAMES = list(RAW) + ["queue_per_request", "latency_per_request"] + [f"{x}_slope15" for x in RAW[:6]] + [f"{x}_mean15" for x in RAW[:6]] + [f"service_{s}" for s in SERVICES]

def timestamp(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()

class FeatureWindow:
    def __init__(self):
        self.history = {s: deque(maxlen=LOOKBACK) for s in SERVICES}
        self.last = {}

    def push(self, event):
        service = event["service"]
        moment = timestamp(event["event_time"])
        if moment <= self.last.get(service, float('-inf')):
            raise ValueError("Event time must increase within each service")
        self.last[service] = moment
        raw = np.array([event["latency_p95_ms"], event["pool_used"], event["queue_depth"], event["retry_rate"], event["cpu_used"], event["memory_used"], event["failures"] / max(1, event["requests"]), event["requests"]], dtype=np.float64)
        self.history[service].append((moment, raw))
        rows = list(self.history[service])
        last = rows[-15:]
        previous_time, previous = last[0]
        duration = max(1., moment - previous_time)
        slopes = (raw[:6] - previous[:6]) / duration
        means = np.mean([r[1][:6] for r in last], axis=0)
        vector = np.concatenate((raw, [raw[2] / max(1, raw[7]), raw[0] / max(1, raw[7])], slopes, means, [float(service == s) for s in SERVICES]))
        return vector.astype(np.float32), len(rows) >= 15

def matrix(events):
    window = FeatureWindow()
    values, ready = [], []
    for event in events:
        row, ok = window.push(event)
        values.append(row)
        ready.append(ok)
    return np.asarray(values), np.asarray(ready)
