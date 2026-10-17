# Demonstrate the actual deployed solution

The public dashboard is at https://148.100.99.173:8443. Follow PUBLIC-ACCESS.md to verify its certificate manually, then use the private app token. Jupyter uses a different token at https://148.100.99.173:8888/lab. Neither token belongs in a video or public URL.

1. Show the assigned LinuxONE instance, then the executed notebook and its `s390x` output. In the dashboard's Evaluation evidence view, show the model version/hash and live containment properties. Explain that the browser is only a client.
2. In Service overview, select **Database connection pressure** and **4x event-time replay**, then **Run scenario**. The fixed synthetic example lasts about 75 wall-clock seconds for five minutes of event time. Warmup and persistence intentionally delay the first alert.
3. Inspect the first database incident. Its retained evidence includes connection pool 83.3%, waiting queue 12.3 and memory 37.3%. Explain that a threshold guard can also trigger an alert; the score alone is not its complete cause. The declared dependency map identifies downstream software services.
4. Click **Explain with local Granite**. Generation runs asynchronously on the same IBM VM; wait for its actual status rather than claiming instant generation. Confirm the output cites every retained evidence ID and names the runbook. A fallback is labeled when native generation is unavailable.
5. Click **Preview a sandbox response**. For this fixed example the paired simulator reports 315 additional successful urgent-results transactions, 104 to 0 modeled breach seconds and 1,238 deferred optional requests. Those are simulator-conditional results; no real host or service is remediated.
6. Open the seven-scenario gallery and full evaluation. Healthy examples, sudden failures, missed incidents and baseline comparisons are included. Fixed seed examples illustrate behavior; they do not replace fresh evaluation.
7. In Jupyter, open `04_original_measurements.executed.ipynb`. Show the actual raw-data hash and plotted measurements. Increased real request computation was observed, separately from simulated hospital-service telemetry.
8. Open SUMMARY.md, the model/data cards and IBM-TOOLKIT.md. Explain why the chosen small model fits the task and which Toolkit steps actually ran. Supported IBM Toolkit container execution and acceleration remain unverified without entitlement.

For the compulsory video, use the reviewed 2:44 walkthrough or record the same concise sequence with team narration. The 6:18 implementation guide is supporting material. Both generated videos are chaptered evidence walkthroughs, not continuous recordings of provisioning. Upload the short version to an accessible YouTube/Vimeo URL and check it signed out before manual portal submission.

After a replay ends, receipt age becomes stale because the producer stopped. This is expected; **Run scenario** starts a fresh session. A container restart preserves the journal but resets live windows and browser sessions. For external telemetry use an explicit external session; simulator response previews are disabled there.
