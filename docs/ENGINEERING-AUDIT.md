# Engineering audit and fixes

The native Jupyter correctness report contains the final test count and complete test names/output. Tests, actual HTTP measurements, local Granite proof, platform inspection, restart and browser checks provide evidence for tested behavior; they cannot prove the absence of every bug.

| Finding | Correction | Regression evidence |
|---|---|---|
| 90-second incident allowance differed from 60-second prediction target | V3 introduced the common 60-second horizon; V5 retains it and evaluates a frozen policy on fresh seeds | Current report method/split manifest; earlier reports retained |
| Permanent alert latch suppressed a later qualifying warning | A shared, bounded episode recheck applies to every comparator | Previously inspected regression now preserves the 51-second warning; online/offline parity |
| Filtering initial warnings improved precision at the expense of recall in the rejected V4 trial | V5 preserves initial threshold signals and filters only persistent repeats, with observed-breach bypass | Fresh paired comparison; archived V4; first-warning and repeat-policy tests |
| Long event gaps retained old feature/persistence state | Rewarm per service after gaps over five seconds; clear votes and SLO continuity at the actual gap | Gap/warmup test; online/offline parity |
| Invalid direct-engine data could advance time before validation | Validate finite values before committing feature state | Nonfinite input followed by valid input test |
| Nonfinite model output could appear ready | Reject invalid output shapes/values and label static fallback as degraded | Nonfinite model-output test |
| External input could mix with demo and claim synthetic provenance | Explicit mutually exclusive sessions; server-owned provenance; no external paired preview | Mode-transition/provenance tests; HTTP integration |
| Consumer exception could terminate queue processing silently | Count failed batches, expose error and degraded health, always complete queue accounting | Injected storage-error test; queue join remains live |
| Header-only body sizing missed chunked payloads | Count actual POST bytes before forwarding a bounded body | Actual chunked oversized-body test |
| Unicode invalid credentials could raise a server error | Compare UTF-8 bytes safely; reject invalid login | Unicode authentication test |
| A finished replay could misleadingly resume without a producer | Reject pause/resume without an active replay; display finished state | Inactive pause test and browser check |
| Generated summary could cite more IDs than its metadata | Grammar requires the complete ordered evidence list; validate again | Actual Granite proof and missing-model fallback test |
| Long-lived streams delayed shutdown; generation might outlive journal | Bound stream lifetime, bound server graceful connection shutdown, join explanation worker before closing journal | Actual restart with active SSE client and retained audit prefix |
| Audit verification loaded all history at once | Stream verification rows under a journal lock | Tamper/persistence tests; audit history still needs operational rotation |
| Sources/UI difficult to review | Format HTML/CSS/JS, add native platform proof, publish data/model/design cards and rubric map | Source, live proof panel and screenshots |

## Remaining operational limits

The data is synthetic and narrow; ML did not consistently outperform thresholds under the corrected evaluation. The system has one VM, one consumer and token-based prototype access. Input schemas assume declared services and agreed one-second aggregation. Event deduplication is bounded in memory, not durable exactly-once semantics. A partial storage failure needs upstream reconciliation. Audit history grows and requires retention/anchoring policy. Model hashes are integrity checks, not signed provenance. A local response preview is a simulator experiment, not causal production evidence. No production readiness, perfect detection, total security or bug-free guarantee is made.
