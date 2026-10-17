# Current results: cg-2026-10-17-v3

On 60 fresh synthetic runs, both ContinuityGuard and static thresholds warned before 31/43 service incidents. Median early lead was 13 seconds versus 10. Precision was 59.3% versus 60.0%; missed incidents were 11 versus 10. This does not establish consistent ML superiority.

| Detector | Early recall | Precision | Median early lead | Late | Missed |
|---|---:|---:|---:|---:|---:|
| Static thresholds | 72.1% | 60.0% | 10 s | 2 | 10 |
| Robust statistics | 44.2% | 11.9% | 39 s | 0 | 24 |
| Isolation Forest | 58.1% | 17.7% | 41 s | 0 | 18 |
| ContinuityGuard | 72.1% | 59.3% | 13 s | 1 | 11 |

The final evaluation uses 70000-series seeds. v1 and v2 were inspected development evaluations; their reports remain separately labeled. All detectors share 60-second early matching, 3-of-5 persistence and 30-second cooldown. Forecast fitting and incident scoring now align to the same 60-second horizon. Four service incidents in one run are correlated.

There were 22 unmatched model-policy alerts overall. No alerts occurred in 10 healthy service-hours, which does not prove a zero real false-alarm rate. The abrupt-failure stress set detected 24/24 incidents and warned before none.

Forecast PR-AUC: 0.7864, positive prevalence 3.8%, Brier 0.01601. Reliability bins still show overconfidence. Run-bootstrap intervals resample whole runs, not individual correlated services: see `report.json/run_bootstrap` (500 replicates). These intervals describe uncertainty within the simulator family only.

37 tests passed on s390x, with 0 failures, 0 errors and 0 skipped. The actual authenticated local HTTP trial processed 1000/1000 offered events at 100 events/s over 10 seconds. Queue-ack p95 was 8.006 ms; engine-batch p95 was 8.89 ms. Queue acknowledgement excludes subsequent inference; engine timing excludes queue waiting. Completion throughput includes confirmation polling. Client and server share the VM, fixtures are synthetic, generation is off, and no WAN/browser or sustained peak-capacity claim follows.

The earlier direct-engine measurements are retained, including the slower concurrent-workload repeat. Use the named report and exact boundary instead of quoting the fastest number as a platform guarantee.
