# External service-window input

The current model learns a controlled hospital-software simulator. Receiving real input does not validate the model for a different organization. Obtain permission, agree metric semantics and service identities, test/calibrate against labeled incidents, and have operators review alerts before relying on it.

An authorized upstream exporter must aggregate **one window per service per second**. The API accepts the four declared service names. It expects counts, failure counts, observed p95 latency in milliseconds, pool occupancy and CPU/memory fractions in [0,1], nonnegative queue depth and a retry fraction. Do not supply patient records, credentials or arbitrary log text.

Example JSONL window (one object per line):

```json
{"event_id":"site-a:database:20261017T120001Z","event_time":"2026-10-17T12:00:01+00:00","service":"database","requests":40,"failures":1,"latency_p95_ms":310.0,"pool_used":0.76,"queue_depth":8.0,"retry_rate":0.03,"cpu_used":0.61,"memory_used":0.48,"source_mode":"external"}
```

This is an illustrative input, not measured operational data. Event time must be timezone-aware and increase within each service; IDs must be stable and unique within a session. The server rejects impossible/nonfinite fields. An event-time gap greater than five seconds resets that service's feature/persistence state. Fifteen observations warm the model again. Current service identities and aggregation semantics are part of the learned contract, not arbitrary field labels.

On a machine with the SSH tunnel and Python requirements installed, save the app token to a private file outside the repository and run:

```bash
python scripts/send_telemetry.py --url http://127.0.0.1:8080 --token-file /private/app-token --input /authorized/windows.jsonl --reset-session
```

The explicit reset stops the synthetic replay and clears live windows. Omit it when continuing the same external stream. The adapter sends bounded batches, retries HTTP 429 with bounded exponential backoff and reports queue acceptance. Inspect `/api/state` for processing counts; 202 is not an exactly-once durable acknowledgement. Reconcile rejected/duplicate/failed batches with upstream records. Deduplication is bounded in memory and does not promise exactly-once replay after restart.

External and simulated sessions cannot mix. The server overwrites caller-supplied synthetic provenance and disables paired simulation previews for external incidents. `/api/scenario` explicitly returns to a fresh sandbox. Direct API mutations require a bearer token or session cookie plus `X-ContinuityGuard: operator`; the app rejects cross-origin mutations. This is a private loopback prototype, not an internet-facing multi-tenant monitoring service.
