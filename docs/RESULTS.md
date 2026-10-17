# Current results: cg-2026-10-17-v5

On 180 predeclared fresh synthetic runs, ContinuityGuard warned early for 130/135 service incidents versus 130/135 for static thresholds. Precision was 45.3% versus 43.5%; median early lead was 11s versus 11s; misses were 1 versus 1. Unmatched notifications were 162 versus 174. This is a modest measured precision gain within one simulator family, not universal superiority.

| Detector | Early recall | Precision | Median early lead | Late | Missed |
|---|---:|---:|---:|---:|---:|
| Static thresholds | 96.3% | 43.5% | 11 s | 4 | 1 |
| Robust statistics | 98.5% | 11.2% | 26 s | 2 | 0 |
| Isolation Forest | 99.3% | 14.3% | 35.5 s | 0 | 1 |
| ContinuityGuard | 96.3% | 45.3% | 11 s | 4 | 1 |

The V5 final evaluation uses predeclared 500000-series seeds, generated only after the model/protocol freeze. V1-V4 are retained development history. All detectors share the scheduler: 3-of-5 persistence, 30-second cooldown and a 60-second persistent-episode recheck. V5 retains initial threshold warnings and uses learned risk only to filter repeats; observed breach limits bypass the filter. Matching stays at 60 seconds before onset through 15 seconds after incident end. Services within a run are correlated. Paired whole-run bootstrap intervals are retained in report.json/paired_bootstrap.

There were 162 unmatched model-policy alerts overall. No alerts occurred in 30 healthy service-hours, which does not prove a zero real false-alarm rate. The abrupt-failure stress set detected 48/48 incidents and warned before none.

Forecast PR-AUC: 0.8179, positive prevalence 4.6%, Brier 0.01691. Reliability bins are retained; production calibration is unverified. Run-bootstrap intervals resample whole runs, not individual correlated services: see `report.json/run_bootstrap` (500 replicates). These intervals describe uncertainty within the simulator family only.

43 tests passed on s390x, with 0 failures, 0 errors and 0 skipped. The actual authenticated local HTTP trial processed 1000/1000 offered events at 100 events/s over 10 seconds. Queue-ack p95 was 7.982 ms; engine-batch p95 was 9.1 ms. Queue acknowledgement excludes subsequent inference; engine timing excludes queue waiting. Completion throughput includes confirmation polling. Client and server share the VM, fixtures are synthetic, generation is off, and no WAN/browser or sustained peak-capacity claim follows.

The earlier direct-engine measurements are retained, including the slower concurrent-workload repeat. Use the named report and exact boundary instead of quoting the fastest number as a platform guarantee.
