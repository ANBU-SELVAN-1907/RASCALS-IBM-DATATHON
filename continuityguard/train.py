"""Train/calibrate/select on separate runs; evaluate once on untouched runs."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import platform
import time
import shutil
import importlib.metadata
import joblib
import numpy as np
from scipy.special import logit
from sklearn.ensemble import IsolationForest, HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import average_precision_score, brier_score_loss
from .simulation import Experiment, SERVICES, HORIZON, simulate, service_breaches, paired_response
from .features import FEATURE_NAMES, matrix
from .evaluation import evaluate_runs, objective, static_flags, robust_score, alert_times
from .models import ModelBundle, diagnosis

KINDS = ("healthy", "healthy_surge", "healthy_shift", "pool_exhaustion", "retry_storm", "memory_pressure")

def dataset(offset, repetitions, kinds=KINDS):
    runs = []
    for ki, kind in enumerate(kinds):
        for rep in range(repetitions):
            seed = offset + ki * 100 + rep
            events, manifest = simulate(Experiment(kind, seed))
            x, ready = matrix(events)
            breaches = service_breaches(events)
            y = np.zeros(len(events), dtype=np.int8)
            eligible = ready.copy()
            for i, event in enumerate(events):
                t = i//len(SERVICES)
                b = breaches[event["service"]]
                eligible[i] = bool(ready[i] and not b[t] and t < len(b)-HORIZON)
                y[i] = bool(b[t+1:t+1+HORIZON].any() and not b[t])
            runs.append({"events": events, "manifest": manifest, "x": x, "ready": ready, "eligible": eligible, "y": y})
    return runs

def stack(runs):
    return np.concatenate([r["x"][r["eligible"]] for r in runs]), np.concatenate([r["y"][r["eligible"]] for r in runs])

def raw_probability(model, x):
    return model.predict_proba(x)[:, 1]

def calibrated(model, calibrator, x):
    p = np.clip(raw_probability(model, x), 1e-6, 1-1e-6)
    return calibrator.predict_proba(logit(p).reshape(-1, 1))[:, 1]

def run_bootstrap(test, systems):
    """Resample whole runs, retaining correlated services within each run."""
    seeds=[r['manifest']['seed'] for r in test]
    draws=np.random.default_rng(97531).integers(0,len(seeds),(500,len(seeds)))
    results={}
    for name,metrics in systems.items():
        groups=[[d for d in metrics['incident_details'] if d['seed']==seed] for seed in seeds]
        recalls,leads=[],[]
        for draw in draws:
            rows=[d for index in draw for d in groups[index]]
            early=[d['lead_seconds'] for d in rows if d['lead_seconds'] is not None and d['lead_seconds']>0]
            if rows:recalls.append(len(early)/len(rows))
            if early:leads.append(float(np.median(early)))
        results[name]={'early_recall_percentile_95':np.percentile(recalls,[2.5,97.5]).tolist(),'median_early_lead_percentile_95_seconds':np.percentile(leads,[2.5,97.5]).tolist()}
    return {'replicates':500,'seed':97531,'unit':'whole run; services within a run stay together','scope':'Uncertainty conditional on this synthetic simulator family, not production generalization. Lead intervals condition on early detections.','systems':results}

def write_plots(out, report, runs, forecasts):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    colors = ["#547083", "#788e8d", "#de9b46", "#168b7a"]
    names = list(report["systems"])
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.1))
    axes[0].barh(names, [report["systems"][n]["early_warning_recall"] or 0 for n in names], color=colors[:len(names)])
    axes[0].set(xlim=(0, 1.03), xlabel="Early-warning recall", title="Untouched synthetic test runs")
    axes[1].barh(names, [report["systems"][n]["false_alarms_per_healthy_service_hour"] or 0 for n in names], color=colors[:len(names)])
    axes[1].set(xlabel="False alarms / healthy service-hour", title="Lower is better")
    fig.tight_layout()
    fig.savefig(out / "benchmark.png", dpi=160)
    plt.close(fig)
    ri = next(i for i, r in enumerate(runs) if r["manifest"]["scenario"] == "pool_exhaustion")
    run = runs[ri]
    indices = [i for i, e in enumerate(run["events"]) if e["service"] == "urgent-results"]
    fig, ax = plt.subplots(figsize=(10, 3.5))
    ax.plot([run["events"][i]["latency_p95_ms"] for i in indices], color="#168b7a", label="Urgent-results latency p95")
    ax.axhline(1000, color="#c2564b", linestyle="--", label="Declared service objective")
    ax.set(xlabel="Synthetic event time (seconds)", ylabel="Latency p95 (ms)", title="Held-out pool-pressure run")
    ax.legend(loc="upper left")
    fig.tight_layout()
    fig.savefig(out / "example-timeline.png", dpi=160)
    plt.close(fig)

def main(output):
    started = time.perf_counter()
    out = Path(output)
    out.mkdir(parents=True, exist_ok=True)
    if (out / 'report.json').exists() and not (out / 'development-v1-report.json').exists():
        shutil.copy2(out / 'report.json', out / 'development-v1-report.json')
    print("Generating independent runs", flush=True)
    train = dataset(1000, 10)
    calibration = dataset(10000, 3)
    validation = dataset(20000, 4)
    # v1/v2 reports were inspected; v3 aligns matching with the 60-second horizon.
    # Model/policy selection uses validation; this final seed range is fresh.
    test = dataset(70000, 10)
    unseen = dataset(80000, 6, ("abrupt_failure",))
    x, y = stack(train)
    xc, yc = stack(calibration)
    xv, yv = stack(validation)
    normal = np.concatenate([r["x"][r["ready"]] for r in train if r["manifest"]["scenario"].startswith("healthy")])
    novelty = IsolationForest(n_estimators=100, max_samples=256, contamination="auto", random_state=17, n_jobs=1).fit(normal)
    normal_reference = np.sort(-novelty.score_samples(np.concatenate([r["x"][r["ready"]] for r in calibration if r["manifest"]["scenario"].startswith("healthy")])))
    candidates = {
        "logistic_regression": make_pipeline(StandardScaler(), LogisticRegression(C=.5, max_iter=500, random_state=17)),
        "boosted_trees_7_leaves": HistGradientBoostingClassifier(max_iter=120, max_leaf_nodes=7, learning_rate=.06, l2_regularization=1, early_stopping=False, random_state=17),
        "boosted_trees_15_leaves": HistGradientBoostingClassifier(max_iter=100, max_leaf_nodes=15, learning_rate=.06, l2_regularization=2, early_stopping=False, random_state=17),
    }
    fitted, comparisons = {}, []
    for name, model in candidates.items():
        print("Fitting", name, flush=True)
        model.fit(x, y)
        pc = np.clip(raw_probability(model, xc), 1e-6, 1-1e-6)
        calibrator = LogisticRegression(C=10, random_state=17).fit(logit(pc).reshape(-1, 1), yc)
        pv = calibrated(model, calibrator, xv)
        comparisons.append({"name": name, "validation_pr_auc": float(average_precision_score(yv, pv)), "validation_brier": float(brier_score_loss(yv, pv))})
        fitted[name] = (model, calibrator)
    novelties = [-novelty.score_samples(r["x"]) for r in validation]
    selections = []
    for candidate, (model, calibrator) in fitted.items():
        probabilities = [calibrated(model, calibrator, r['x']) for r in validation]
        for threshold in (.20, .35, .5, .65, .8, .9, .97):
            for q in (.995, .999, 1.0):
                cutoff = float(np.quantile(normal_reference, q))
                for mode in ('forecast', 'hybrid', 'guarded_forecast'):
                    flags = [(p >= threshold) | ((n >= cutoff) if mode == 'hybrid' else static_flags(r['x']) if mode == 'guarded_forecast' else False) for p,n,r in zip(probabilities,novelties,validation)]
                    metrics = evaluate_runs(validation, flags)
                    selections.append((objective(metrics), candidate, {'mode': mode, 'forecast_threshold': threshold, 'novelty_threshold': cutoff, 'novelty_quantile': q}, metrics))
    _, choice, policy, validation_metrics = max(selections, key=lambda row: (row[0], row[2]['mode'] == 'guarded_forecast', row[2]['forecast_threshold']))
    model, calibrator = fitted[choice]
    center = np.median(normal[:, :7], axis=0)
    scale = np.maximum(1.4826*np.median(np.abs(normal[:, :7]-center), axis=0), .003)
    robust_options = []
    for threshold in (5., 7., 9., 12., 16.):
        metrics = evaluate_runs(validation, [robust_score(r["x"], center, scale) > threshold for r in validation])
        robust_options.append((objective(metrics), threshold))
    robust_threshold = max(robust_options)[1]
    state = {"feature_names": FEATURE_NAMES, "forecast": model, "calibrator": calibrator, "novelty": novelty, "normal_novelty": normal_reference, "policy": policy, "robust_center": center, "robust_scale": scale, "robust_threshold": robust_threshold}
    joblib.dump(state, out / "models.joblib", compress=3)
    manifest = {"version": "cg-2026-10-17-v3", "trained_utc": datetime.now(timezone.utc).isoformat(), "architecture": platform.machine(), "model": choice, "forecast_horizon_seconds": HORIZON, "feature_count": len(FEATURE_NAMES), "sha256": hashlib.sha256((out/"models.joblib").read_bytes()).hexdigest(), "packages": {p: importlib.metadata.version(p) for p in ("numpy", "scikit-learn", "scipy", "joblib")}}
    (out/"manifest.json").write_text(json.dumps(manifest, indent=2))
    bundle = ModelBundle(out)
    forecasts, novelty_scores, final_flags = [], [], []
    for run in test:
        p, n, _ = bundle.predict(run["x"])
        forecasts.append(p)
        novelty_scores.append(n)
        final_flags.append(bundle.decision_flags(p, n, run['x']))
    systems = {
        "Static thresholds": evaluate_runs(test, [static_flags(r["x"]) for r in test]),
        "Robust statistics": evaluate_runs(test, [robust_score(r["x"], center, scale) > robust_threshold for r in test]),
        "Isolation Forest": evaluate_runs(test, [n > policy["novelty_threshold"] for n in novelty_scores]),
        "ContinuityGuard": evaluate_runs(test, final_flags),
    }
    xt, yt = stack(test)
    pt = calibrated(model, calibrator, xt)
    reliability = []
    for low, high in zip(np.arange(0, 1, .2), np.arange(.2, 1.01, .2)):
        mask = (pt >= low) & (pt < high)
        reliability.append({"lower": float(low), "upper": float(high), "count": int(mask.sum()), "mean_prediction": float(pt[mask].mean()) if mask.any() else None, "observed_rate": float(yt[mask].mean()) if mask.any() else None})
    stress_flags = []
    for run in unseen:
        p, n, _ = bundle.predict(run["x"])
        stress_flags.append(bundle.decision_flags(p, n, run['x']))
    responses = []
    for run, flags in zip(test, final_flags):
        times = alert_times(flags, run["ready"])
        times = [(second, service) for service, values in times.items() for second in values]
        if times and run["manifest"]["scenario"] in {"pool_exhaustion", "retry_storm"}:
            second, service = min(times)
            event = run["events"][second*len(SERVICES)+SERVICES.index(service)]
            _, book = diagnosis(event)
            if book["action"] != "none":
                responses.append(paired_response(Experiment(run["manifest"]["scenario"], run["manifest"]["seed"]), second, book["action"]))
    report = {
        "scope": "Synthetic service-simulator evaluation on LinuxONE; not real hospital validation",
        "split": {"training_runs": len(train), "calibration_runs": len(calibration), "validation_runs": len(validation), "test_runs": len(test), "unseen_abrupt_runs": len(unseen), "no_shared_seeds": True, "seconds_per_run": 300, "forecast_training_rows": len(y)},
        "manifest": manifest, "candidate_models": comparisons, "selected_model": choice, "policy": policy,
        "validation_policy_metrics": validation_metrics, "systems": systems,
        "forecast_test": {"pr_auc": float(average_precision_score(yt, pt)), "brier_score": float(brier_score_loss(yt, pt)), "positive_prevalence": float(yt.mean()), "reliability_bins": reliability},
        "run_bootstrap":run_bootstrap(test,systems),
        "unseen_abrupt_failures": evaluate_runs(unseen, stress_flags), "paired_responses": responses,
        "method": {"slo": "p95 >1000 ms or failures/requests >0.10, sustained for three 1-second windows", "persistence": "3 of last 5 flagged windows; 30-second re-alert cooldown", "matching": "one alert per incident, from 60 seconds before onset through 15 seconds after incident end", "healthy_exposure": "healthy, healthy_surge and healthy_shift service-seconds", "selection": "joint model/policy validation: 0.65 early-warning recall + 0.35 precision; penalize false alarms above 0.5/healthy service-hour", "novelty_is_probability": False, "development_history": "v1 30000-series and v2 50000-series were inspected; v3 aligns incident matching to 60 seconds, reselects on validation and tests fresh 70000-series seeds"},
        "limitations": ["Synthetic data and simulator intervention assumptions", "Declared topology and heuristic suspected cause, not causal proof", "Calibrated model output is conditional on the synthetic distribution", "Abrupt incidents can have no observable warning precursor", "No production hospital, z/OS or accelerator validation"],
        "training_and_evaluation_seconds": round(time.perf_counter()-started, 2),
    }
    (out/"report.json").write_text(json.dumps(report, indent=2))
    (out/"split-manifest.json").write_text(json.dumps({name: [r["manifest"] for r in runs] for name,runs in [("train",train),("calibration",calibration),("validation",validation),("test",test),("stress",unseen)]}, indent=2))
    write_plots(out, report, test, forecasts)
    print(json.dumps({"selected": choice, "policy": policy, "final_test": {k:v for k,v in systems["ContinuityGuard"].items() if k!="incident_details"}, "elapsed_seconds": report["training_and_evaluation_seconds"]}, indent=2), flush=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="artifacts")
    main(parser.parse_args().output)
