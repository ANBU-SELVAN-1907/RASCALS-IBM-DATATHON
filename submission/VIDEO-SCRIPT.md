# Record a real 2:50 demonstration

Maximum allowed: 3 minutes including transitions and credits. Use 1080p if readable. Do not show tokens, authentication URLs, account emails, private keys or unrelated windows. All demo telemetry is synthetic and the page must retain that label. Team members should explain the parts they understand; do not invent identities or voice another person without consent.

## 0:00-0:20 - Problem

"We are RASCALS. ContinuityGuard investigates developing failures in the infrastructure behind hospital digital services. A slow shared dependency can delay several services. Our goal is to give operators useful warning time and clear evidence before a service objective is breached."

Show the title and a small dependency map. If citing the NHS incident, use its exact source and clarify that this prototype was not tested on or shown to prevent that incident.

## 0:20-0:40 - LinuxONE evidence

"Our training and testing run through Jupyter on LinuxONE, and the runtime is native s390x. This saved notebook shows the data split, model selection and final evaluation. The application keeps inference and incident processing on the same VM as the demo stream."

Show the actual s390x output, executed notebook and redacted container/resource evidence. Do not imply that a CPU flag or library file proves AI accelerator use.

## 0:40-1:30 - Controlled live demo

"This is a controlled database-pressure scenario at four-times event-time replay. The system tracks pool occupancy, queues, retries and service latency. After the feature window warms, persistent forecast risk produces an incident. Here are the actual measurements, affected services and suspected dependency. The source is a hypothesis, not proven causality."

Start the demo just before recording this segment or use a clearly labeled continuous replay capture. Keep source event time, replay speed and synthetic labels visible. Do not edit the alert timing to make it appear earlier.

## 1:30-1:55 - Decision support

"The operator can inspect a runbook and compare the modeled response with taking no action under the same future demand. The preview reports successful urgent-results transactions, breach duration and the cost of deferred optional work. It acts only in the simulator. Local Granite can explain the evidence under a strict output schema; invalid output falls back explicitly."

Show a real response preview and actual completed explanation. If generation used fallback, say so; do not label fallback text as generated.

## 1:55-2:30 - Results and tradeoff

"On sixty independent final synthetic runs, ContinuityGuard warned before forty-three of forty-seven service incidents. Median lead among early warnings was thirty-seven seconds, compared with nine for static thresholds. Precision was sixty-one point four percent, lower than the threshold baseline's sixty-eight point three percent. Both missed four incidents. No alerts occurred in ten healthy service-hours. These are simulator results, not hospital production performance."

Show the table including precision and misses. Add the short engine benchmark only if time remains: 100 synthetic window events per second, 9–54 ms p95 across two runs per four-event engine batch; excludes HTTP, queue and browser delay.

## 2:30-2:50 - Contribution and next step

"Our contribution connects early-warning evidence, service priorities and a repeatable response preview. The code, model manifest and executed notebooks are in our repository. Next we need authorized real telemetry and operator feedback to test adoption. Thank you."

Show repository URL and team name. Include assistance/source credits without obscuring the demo. Export and verify final duration before upload; a video script is not itself a submitted video.
