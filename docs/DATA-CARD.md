# Data card

**Origin:** original service-system simulator in `continuityguard/simulation.py`. No external dataset or patient data is used for project training/evaluation. IBM's synthetic loan documents are used only in the prerequisite sample lab, not as this detector's training data.

**Granularity:** one synthetic service-level aggregate per second, four services, 300 seconds per experiment. Requests and failures are counts; latency is a generated p95 summary. The prototype does not independently execute that many real HTTP/database transactions.

**Observed fields:** event ID/time, service name, request/failure count, latency p95, pool occupancy, queue depth, retry rate, CPU and memory occupancy, source mode and deferred-request count. Actual host CPU/RAM are measured separately by psutil and clearly labeled.

**Truth separation:** seed, scenario, onset, severity, action and action time are evaluator metadata. They are not supplied to feature extraction/model fitting. Breach labels use future observed simulator outcomes; future values are never predictor features.

**Scenarios:** healthy load, healthy surge, healthy shift, gradual connection-pool exhaustion, retry cascade, memory pressure, plus unseen abrupt-failure stress. Multiple severities include faults that do not reach the declared breach. Seed 101 and severity 1.12 are used for a clearly identified demonstration, separate from the randomized-severity benchmark.

**Intervention assumptions:** batch deferral reduces modeled pool pressure and explicitly defers optional requests; retry capping reduces modeled retry pressure. Such encoded effects are hypotheses for a later real test, not empirical findings about a hospital system.

**Limitations:** simple noise/load dynamics, small fixed topology, repeated fault mechanisms, no real-log parsing, no patient data, no production validation. More independent random seeds improve repeatability estimates within this simulator but do not address structural simulator bias.

**Reuse:** generated telemetry can be recreated from source and split manifests. Do not attach a third-party dataset license to it or imply that synthetic hospital-service labels originated from a hospital.
