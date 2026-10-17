# Demonstrate the actual deployed solution

The public dashboard is at https://148.100.99.173:8443. Follow PUBLIC-ACCESS.md to verify its certificate manually, then use the private app token. Jupyter uses a different token at https://148.100.99.173:38888/lab. Neither token belongs in a video or public URL.

1. Show the assigned LinuxONE instance, then the executed notebook and its `s390x` output. In the dashboard's Evaluation evidence view, show the model version/hash and live containment properties. Explain that the browser is only a client.
2. In Service overview, select **Database connection pressure** and **4x event-time replay**, then **Run scenario**. The fixed synthetic example lasts about 75 wall-clock seconds for five minutes of event time. Warmup and persistence intentionally delay the first alert.
3. Inspect the **first database incident** by event time. The verified example retains: Waiting queue: 22.2 requests; Connection pool occupancy: 90.1 %; Latency p95: 696.8 ms. Initial warnings come from operational thresholds; the ML score governs repeat triage. The declared dependency map identifies downstream software services.
4. Click **Explain with local Granite**. Generation is asynchronous on the same VM. Confirm its complete evidence references and runbook; unavailable generation has a labeled fallback.
5. Click **Preview a sandbox response**. This verified database example reports 309 additional modeled urgent-results successes, 104 to 0 breach seconds and 1175 deferred optional requests. These are simulator-conditional results; no real service is modified. Other selected incidents can produce different values.
6. Open the seven-scenario gallery and full evaluation. Healthy examples, sudden failures, missed incidents and baseline comparisons are included. Fixed seed examples illustrate behavior; they do not replace fresh evaluation.
7. In Jupyter, open `04_original_measurements.executed.ipynb`. Show the actual raw-data hash and plotted measurements. Increased real request computation was observed, separately from simulated hospital-service telemetry.
8. Open SUMMARY.md, the model/data cards and IBM-TOOLKIT.md. Explain why the chosen small model fits the task and which Toolkit steps actually ran. Supported IBM Toolkit container execution and acceleration remain unverified without entitlement.

For the compulsory video, use the reviewed current short walkthrough or record the same concise sequence with team narration. The longer implementation guide is supporting material. Both generated videos are chaptered evidence walkthroughs, not continuous recordings of provisioning. Upload the short version to an accessible YouTube/Vimeo URL and check it signed out before manual portal submission.

After a replay ends, receipt age becomes stale because the producer stopped. This is expected; **Run scenario** starts a fresh session. A container restart preserves the journal but resets live windows and browser sessions. For external telemetry use an explicit external session; simulator response previews are disabled there.
