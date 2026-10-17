# Defend the implementation in your own words

1. **What problem does this solve?** Developing system faults can disrupt dependent essential software services. We support IT operators with streaming risk, retained measurements, runbooks and a response preview; no clinical decisions.

2. **What is the exact title and team?** RASCALS_IBM Z Datathon 2026 Project / ContinuityGuard. ANBU SELVAN T; SAHANA G; DHARSHINI E; POOJA V. Hindustan Institute of Technology and Science.

3. **What actually runs on LinuxONE?** The native Jupyter training/test kernels, simulator, causal features, forecast, novelty estimator, API, SQLite journal and local Granite. The browser is a client through TLS or SSH. Show the live platform proof, model hash and executed notebooks.

4. **Why LinuxONE rather than a logo in the slides?** Prediction and local generation execute on s390x beside the prototype telemetry/journal, without exporting telemetry to a remote model API. Containers and verified resource/security controls are applied to this actual runtime. No comparative speed superiority is claimed.

5. **Is this IBM Machine Learning for z/OS?** No. This is open-source AI on LinuxONE Community Cloud Linux. We do not claim z/OS integration, z/OS transactions, Telum/Spyre acceleration or certification.

6. **What does Jupyter prove?** Six native notebooks retain fitting, calibration, selection, evaluation, tests, actual HTTP integration and local generation. Their executed copies, success records and architecture/model outputs are in the repository.

7. **Have both mandatory labs been completed?** The Churn multi-model and Loan predictive/generative sample notebooks executed before original project work. Their timestamps and source commit are recorded. The organizer must confirm the exact mapping to its assigned prerequisites; execution alone is not a course-completion certificate.

8. **What is learned?** logistic_C0.1 forecasts a new sustained breach within 60 event-time seconds. Isolation Forest learns healthy variation for a separate novelty score. Sigmoid calibration uses separate runs; production calibration is unproven.

9. **Why this model?** Five candidates and alert-policy variants compete on a declared validation objective. Scaled logistic regression supplies a compact, calibratable score; other candidates include three boosted-tree sizes. We do not call them universally best.

10. **What triggers an alert?** Initial static warnings use 3-of-5 persistence after warmup. A 60-second episode recheck prevents permanent suppression. ML confirms whether a persistent repeat merits notification; observed breach limits bypass the learned filter. Independent forecast paging is disabled. Novelty remains separate.

11. **How much better is it?** On 180 predeclared fresh synthetic runs, ContinuityGuard warned early for 130/135 service incidents versus 130/135 for static thresholds. Precision was 45.3% versus 43.5%; median early lead was 11s versus 11s; misses were 1 versus 1. Unmatched notifications were 162 versus 174. This is a modest measured precision gain within one simulator family, not universal superiority. Report confidence intervals; do not claim a statistically established general advantage.

12. **Why retain AI if thresholds are competitive?** The model supplies a learned, calibratable score and novelty context, while the integration makes decisions inspectable. Current experiments do not justify replacing thresholds. More diverse authorized data and operational validation are needed to establish incremental ML value.

13. **What is new?** This original implementation connects causal warning features, software dependency priorities, evidence receipts, constrained local wording and a same-workload response preview. Algorithms are established; no world-first claim or prior-team code reuse.

14. **How is leakage controlled?** Whole runs and disjoint train/calibration/validation/test seeds; past/current features only; no fault metadata; separate calibration. V1-V4 inspected reports are development history. V5 freezes its protocol and model before new final runs.

15. **Why did the headline change?** V3 aligned the horizon. V4 filtering improved precision but lost early recall and was rejected. V5 preserves first threshold warnings and filters repeats. It freezes selection before new final evaluation; prior results remain published.

16. **Why zero healthy false alerts but low precision?** The zero applies only to 30 healthy service-hours. Overall precision also counts repeat, unmatched and non-breaching fault-run alerts. There were 162 unmatched V5 notifications overall.

17. **Can sudden faults be predicted?** The unseen abrupt stress test detected every tested service incident but warned before none. No precursor means no promised early warning.

18. **Does the diagnosis prove root cause?** No. A declared dependency map and heuristic measured-signal rules propose a suspected source. Service criticality is declared software policy, not learned clinical risk or causal proof.

19. **Does the preview prove outage prevention?** No. Paired branches share exogenous demand/noise and history until an allowlisted simulator action. Benefits follow intervention assumptions. No real host or service is modified.

20. **What does Granite add?** Local constrained wording tied to verified measurements and a runbook. Every evidence ID cited in the text is required. It has no shell tools and cannot execute remediation. Invalid/unavailable generation gets a labeled deterministic fallback.

21. **What happens when inference or storage fails?** Inference exceptions/nonfinite outputs enter explicit degraded static fallback. Consumer exceptions increment failed batches, preserve queue progress and make health degraded. No prediction percentage is invented. Reconcile upstream events after storage failure; this is not exactly-once delivery.

22. **What happens on missing or reordered data?** Receipt age shows stale status. A >5-second event gap resets per-service warmup and persistence. Old/out-of-order/nonfinite events are rejected without poisoning future state. Windows are bounded.

23. **Can external callers spoof a simulator result?** External input requires a separate session, cannot mix with the sandbox and has its provenance overwritten by the server. Paired previews are disabled for external incidents. Real deployment still requires authorized data and domain calibration.

24. **Is the journal tamper-proof?** No. It checks hash links and retains history across restart; externally retain a trusted head to detect whole-history replacement. Signed provenance and external anchoring would be production work.

25. **What do the latency numbers include?** The actual local HTTP test processed 1000/1000 synthetic fixture events at 100 offered events/s over 10 seconds. Queue-ack p95 7.982 ms excludes later processing; engine-batch p95 9.1 ms excludes queue wait. Client/server share the VM; no WAN/browser or maximum sustained-capacity claim.

26. **What security controls were verified?** UID 1000, read-only root, CPU/memory/PID caps, dropped capabilities, no-new-privileges, loopback/SSH, schema/actual body limits, authentication and origin checks. Host networking and single-token access remain explicit prototype limits.

27. **How do you know the implementation works?** 43 native tests pass; inspect the actual test names/output. Additional HTTP, real Granite, container, restart and browser checks retain measured evidence. Passing tests does not prove absence of every bug.

28. **What remains before adoption/submission?** Production adoption needs authorized real telemetry, domain evaluation/calibration, reviewed response steps, identity/operations hardening and reliability trials. Event submission still needs prerequisite mapping confirmation, reviewed YouTube/Vimeo hosting and manual portal entry.

29. **Was AI assistance used?** Yes. Codex assisted architecture, coding, orchestration, tests and submission preparation. The team must understand and disclose its work under organizer guidance. Do not claim unaided development or invent member contributions.

