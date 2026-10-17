"""Incident-level evaluation. No point adjustment; missed and late incidents count."""
from collections import deque
import numpy as np
from .simulation import SERVICES, service_breaches
from .alert_policy import AlertTracker

def alert_times(flags, ready, refresh_allowed=None):
    tracker=AlertTracker()
    result = {s: [] for s in SERVICES}
    for i, (flag, ok) in enumerate(zip(flags, ready)):
        s, second = SERVICES[i % len(SERVICES)], i // len(SERVICES)
        allow=True if refresh_allowed is None else bool(refresh_allowed[i])
        if tracker.push(s,second,flag,ok,allow):
            result[s].append(second)
    return result

def intervals(breaches):
    positions = np.flatnonzero(breaches)
    result = []
    for p in positions:
        if result and int(p) - result[-1][1] <= 15:
            result[-1][1] = int(p)
        else:
            result.append([int(p), int(p)])
    return result

def evaluate_runs(runs, flags_by_run, early_window=60, keep_details=True, refresh_by_run=None):
    incidents = detected = early = total_alerts = false_alerts = healthy_false = 0
    healthy_seconds = 0
    leads, late, details = [], [], []
    for run_index,(run, flags) in enumerate(zip(runs, flags_by_run)):
        alerts = alert_times(flags, run["ready"],None if refresh_by_run is None else refresh_by_run[run_index])
        breaches = run['breaches'] if 'breaches' in run else service_breaches(run["events"])
        normal = run["manifest"]["scenario"].startswith("healthy")
        if normal:
            healthy_seconds += run["manifest"]["seconds"] * len(SERVICES)
        for service in SERVICES:
            remaining = list(alerts[service])
            total_alerts += len(remaining)
            if normal:
                healthy_false += len(remaining)
            for start, end in intervals(breaches[service]):
                incidents += 1
                matches = [a for a in remaining if start - early_window <= a <= end + 15]
                first = min(matches) if matches else None
                if first is not None:
                    remaining.remove(first)
                    detected += 1
                    if first < start:
                        early += 1
                        leads.append(start - first)
                    else:
                        late.append(first - start)
                if keep_details:details.append({"seed": run["manifest"]["seed"], "scenario": run["manifest"]["scenario"], "service": service, "first_breach_second": start, "alert_second": first, "lead_seconds": start-first if first is not None else None})
            false_alerts += len(remaining)
    return {
        "incidents": incidents, "alerts": total_alerts, "detected": detected,
        "early_detections": early, "late_detections": len(late), "missed": incidents-detected,
        "incident_precision": detected/total_alerts if total_alerts else None,
        "incident_recall": detected/incidents if incidents else None,
        "early_warning_recall": early/incidents if incidents else None,
        "median_early_lead_seconds": float(np.median(leads)) if leads else None,
        "healthy_service_hours": healthy_seconds/3600,
        "healthy_false_alerts": healthy_false,
        "false_alarms_per_healthy_service_hour": healthy_false/(healthy_seconds/3600) if healthy_seconds else None,
        "unmatched_alerts_all_runs": false_alerts, "incident_details": details,
    }

def objective(metrics, budget=.5):
    """Predeclared validation objective; penalize exceeding the alarm budget."""
    recall = metrics["early_warning_recall"] or 0
    precision = metrics["incident_precision"] or 0
    rate = metrics["false_alarms_per_healthy_service_hour"] or 0
    return .65 * recall + .35 * precision - 2 * max(0, rate-budget)

def static_flags(x):
    return (x[:, 0] > 800) | (x[:, 1] > .90) | (x[:, 6] > .08) | (x[:, 4] > .90)

def confirmed_flags(x):
    """Observed service-objective limits bypass learned filtering."""
    return (x[:,0]>1000) | (x[:,6]>.10)

def repeat_refresh_flags(probability,x,gate,trend_guard):
    allow=(probability>=gate)|confirmed_flags(x)
    if trend_guard:allow=allow|(x[:,10]>1.)|(x[:,11]>.001)|(x[:,12]>.1)
    return allow

def robust_score(x, center, scale):
    # Restrict to operational signals. Demand alone is not a failure.
    return np.maximum(0, (x[:, :7] - center)/scale).max(axis=1)
