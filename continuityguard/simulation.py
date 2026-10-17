"""A bounded, reproducible service-system simulator. All telemetry is synthetic.

Exogenous demand/noise are generated before interventions, so paired experiments
share exactly the same future disturbance. No fault metadata enters the detector.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import numpy as np

SERVICES = ("database", "urgent-results", "appointments", "batch-reporting")
PRIORITIES = {"database": 0, "urgent-results": 3, "appointments": 2, "batch-reporting": 1}
SCENARIOS = ("healthy", "healthy_surge", "healthy_shift", "pool_exhaustion", "retry_storm", "memory_pressure", "abrupt_failure")
FAULTS = {"pool_exhaustion", "retry_storm", "memory_pressure", "abrupt_failure"}
DEPENDENCIES = {"urgent-results": ["database"], "appointments": ["database"], "batch-reporting": ["database"], "database": []}
HORIZON = 60
LOOKBACK = 30

@dataclass(frozen=True)
class Experiment:
    scenario: str
    seed: int
    seconds: int = 300
    strength: float | None = None

    def __post_init__(self):
        if self.scenario not in SCENARIOS or not 90 <= self.seconds <= 1200:
            raise ValueError("Invalid bounded experiment")

def simulate(spec: Experiment, action: str = "none", action_at: int | None = None):
    """Return observable events and a separate evaluator-only manifest."""
    if action not in {"none", "defer_batch", "cap_retries"}:
        raise ValueError("Unknown sandbox action")
    rng = np.random.default_rng(spec.seed)
    n = spec.seconds
    onset = int(rng.integers(75, max(76, min(130, n - 90))))
    severity = spec.strength if spec.strength is not None else float(rng.uniform(.7, 1.2))
    demand = np.maximum(8, 44 + 8 * np.sin(np.arange(n) / 21 + rng.uniform(0, 6)) + rng.normal(0, 3, n))
    noise = rng.normal(0, 1, (n, len(SERVICES), 7))
    if spec.scenario == "healthy_surge":
        demand *= 1 + .85 * np.exp(-((np.arange(n) - onset - 35) / 28) ** 2)
    if spec.scenario == "healthy_shift":
        demand += 18 * (np.arange(n) > onset)
    start = datetime(2026, 10, 17, tzinfo=timezone.utc)
    events, latent = [], []
    queues = np.zeros(len(SERVICES), dtype=float)
    for t in range(n):
        progress = np.clip((t - onset) / 95, 0, 1)
        # Some mild faults do not become outages; these remain negative outcomes.
        pool_fault = severity * progress if spec.scenario == "pool_exhaustion" else 0
        retry_fault = severity * progress if spec.scenario == "retry_storm" else 0
        memory_fault = severity * progress if spec.scenario == "memory_pressure" else 0
        abrupt = float(spec.scenario == "abrupt_failure" and onset <= t < onset + 55)
        active = action_at is not None and t >= action_at
        deferral = active and action == "defer_batch"
        retry_cap = active and action == "cap_retries"
        pool = np.clip(.35 + demand[t] / 330 + .45 * pool_fault + .11 * memory_fault + .2 * abrupt - .22 * deferral, .1, .995)
        retries = max(.005, .008 + .46 * retry_fault + .09 * abrupt - .31 * retry_cap)
        memory = np.clip(.31 + .36 * memory_fault + .09 * pool_fault, .1, .99)
        effective = pool + .85 * retries + .95 * max(0, memory - .47) + .45 * abrupt
        for si, service in enumerate(SERVICES):
            z = noise[t, si]
            multiplier = (1.0, .38, .32, .30)[si]
            offered = max(1, round(demand[t] * multiplier + z[0] * 1.3))
            deferred = round(offered * .7) if deferral and service == "batch-reporting" else 0
            requests = max(1, offered - deferred)
            pressure = max(0, effective - .66)
            queues[si] = max(0, .84 * queues[si] + pressure * requests * .52 - 1.3 + z[1] * .7)
            latency = max(25, 65 + requests * 1.5 + pressure ** 1.5 * 3400 + queues[si] * 6 + z[2] * 13)
            error_rate = float(np.clip((effective - .81) * .72 + queues[si] / 600 + z[3] * .002, 0, .85))
            failures = min(requests, round(requests * error_rate))
            events.append({
                "event_id": f"{spec.seed}:{service}:{t}",
                "event_time": (start + timedelta(seconds=t)).isoformat(),
                "service": service, "requests": requests, "failures": failures,
                "latency_p95_ms": round(latency, 3), "pool_used": round(float(np.clip(pool + z[4] * .008, 0, 1)), 5),
                "queue_depth": round(float(queues[si]), 3),
                "retry_rate": round(float(np.clip(retries + z[5] * .008, 0, 1)), 5),
                "cpu_used": round(float(np.clip(.22 + demand[t] / 170 + .12 * progress * (spec.scenario in FAULTS) + z[6] * .012, 0, 1)), 5),
                "memory_used": round(float(np.clip(memory + z[6] * .006, 0, 1)), 5),
                "source_mode": "synthetic", "deferred_requests": deferred,
            })
        latent.append({"second": t, "fault_active": t >= onset and spec.scenario in FAULTS})
    manifest = {"scenario": spec.scenario, "seed": spec.seed, "onset": onset, "strength": severity,
                "seconds": n, "action": action, "action_at": action_at,
                "data_scope": "controlled synthetic service simulator; not hospital production telemetry"}
    return events, manifest

def service_breaches(events):
    """SLO: latency p95 >1000 ms or observed errors >10%, for 3 windows."""
    values = {s: [] for s in SERVICES}
    for event in events:
        values[event["service"]].append(event["latency_p95_ms"] > 1000 or event["failures"] / event["requests"] > .10)
    result = {}
    for service, raw in values.items():
        raw = np.asarray(raw, dtype=bool)
        sustained = np.zeros(len(raw), dtype=bool)
        for t in range(2, len(raw)):
            sustained[t] = bool(raw[t-2:t+1].all())
        result[service] = sustained
    return result

def paired_response(spec, action_at, action):
    baseline, _ = simulate(spec)
    intervention, _ = simulate(spec, action=action, action_at=action_at)
    def total(events, service):
        selected = [e for e in events[action_at * len(SERVICES):] if e["service"] == service]
        return sum(e["requests"] - e["failures"] for e in selected)
    before = service_breaches(baseline)
    after = service_breaches(intervention)
    return {
        "scope": "paired synthetic experiment; effects are simulator assumptions",
        "action": action, "action_at_second": action_at,
        "urgent_success_without": total(baseline, "urgent-results"),
        "urgent_success_with": total(intervention, "urgent-results"),
        "urgent_success_difference": total(intervention, "urgent-results") - total(baseline, "urgent-results"),
        "urgent_breach_seconds_without": int(before["urgent-results"][action_at:].sum()),
        "urgent_breach_seconds_with": int(after["urgent-results"][action_at:].sum()),
        "deferred_batch_requests": sum(e["deferred_requests"] for e in intervention if e["service"] == "batch-reporting"),
        "same_exogenous_seed": spec.seed,
    }
