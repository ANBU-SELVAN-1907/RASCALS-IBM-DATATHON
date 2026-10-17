# Short submission narration

## Problem: developing failures in essential services

We are RASCALS from Hindustan Institute of Technology and Science. ContinuityGuard identifies developing system faults and gives operators a reviewable warning before disruption. Our demonstration uses original controlled scenarios, with a separate experiment containing actual LinuxONE service measurements. This is a chaptered evidence walkthrough, with labeled synthetic narration.

## Solution: AI and the decision path stay on LinuxONE

Native s390x Jupyter fits and tests the models. The deployed app combines calibrated boosted-tree forecasts, a threshold guard and separate novelty scores. Persistent signals create incidents with retained measurements, dependency priorities and runbooks. Local Granite generates constrained wording. The operator can inspect a paired simulator response before deciding what to investigate.

## Working scenarios and actual operator output

The actual dashboard runs on the assigned IBM VM. Pool pressure and retry-cascade examples warn before sustained service breach. A sudden failure is detected at onset, without a promised precursor. The action preview reports modeled benefit with deferred optional work. It executes no remediation against a real service.

## Original measurements, with raw-data provenance

We also collected real request timings and process counters from a bounded microservice on LinuxONE. Increased request computation raised measured latency. A separate baseline-trained novelty detector flagged the controlled pressure. The raw CSV, timestamps, recovery false alerts and hash are published. This experiment does not validate hospital outage prediction.

## Evaluation: report the misses and competitive baseline

On sixty fresh synthetic runs, both ContinuityGuard and static thresholds warned before thirty-one of forty-three service incidents. Median early lead was thirteen seconds versus ten. Precision was fifty-nine point three percent versus sixty percent. These results and uncertainty do not establish consistent model superiority. Earlier development reports remain available.

## LinuxONE proof, tests and IBM Toolkit boundary

37 native tests passed. Actual authenticated HTTP ingestion processed all one thousand offered events in the short test. Container controls, model hashes and restart evidence are public. IBM Toolkit deployment guidance was applied, and an optional Random Forest export was checked. Entitled Toolkit execution and hardware acceleration are not claimed.

## Learnings and a complete reproducible handoff

We learned to align prediction and evaluation horizons, distinguish queue timing from inference, and separate measured data from simulation. The repository contains the summary, five executed notebooks, scenarios, source, outputs, deployment and access instructions. Review the short video, confirm required labs and submit manually. ContinuityGuard makes warning evidence and next steps inspectable.


# Extended implementation narration

## 01 / What the project does

This implementation guide follows RASCALS ContinuityGuard from environment setup through model training, testing, actual measurements, deployment and operator output. The problem is system anomaly detection: identify developing abnormal activity and alert an organization before a major disruption. We use a hospital-software scenario to define service priorities. No patient data or clinical decisions are involved. The guide is chaptered, using actual saved evidence and reproducible commands; it is not a continuous recording of provisioning.

## 02 / Prepare the real IBM LinuxONE environment

Start with your assigned LinuxONE Community Cloud VM and its private SSH key. Our host is RHEL nine point eight, with native s390x architecture and Podman. Confirm the operating system instead of applying Ubuntu commands blindly. Keep the key outside the repository. Complete both organizer-assigned labs before original project work; our sample execution evidence is retained, but the exact category mapping requires organizer confirmation.

## 03 / Open authenticated Jupyter on the IBM VM

The assigned VM now provides Jupyter over TLS on port eight eight eight eight, and the dashboard over TLS on port eight four four three. Verify the published certificate fingerprint manually before entering either token. The certificate is short-lived and self-signed. Jupyter and the app use separate private tokens. An SSH tunnel is an alternative route to the same VM; localhost does not mean the models run on the laptop.

## 04 / Place and understand the source

Clone the repository into persistent Jupyter shared storage and open its notebooks directory. Read SUMMARY dot m d and the model and data cards. The simulator, features, model training, streaming engine, explanation and API are separate source modules. The final model is frozen at version three. The raw original measurements are separate from the synthetic hospital-service scenarios.

## 05 / Train, calibrate, select and evaluate

Run notebook zero one from top to bottom on the native kernel. It fits three tabular forecasting candidates on sixty training runs, fits calibration on eighteen separate runs, and selects the model and alert policy on twenty-four validation runs. Sixty fresh final runs are scored afterward. Current and historical features never contain future values or fault metadata. The target and early incident matching both use sixty seconds.

## 06 / Read the results before making claims

The selected model is small histogram gradient boosting, with maximum seven leaves and a separate sigmoid calibrator. The selected policy combines a high learned score with explicit operational thresholds. Isolation Forest reports novelty separately. Both the submitted system and static baseline warned before thirty-one of forty-three final service incidents. Precision and misses remain competitive with the baseline, rather than demonstrating consistent learned-model superiority. Publish that tradeoff.

## 07 / Run the engineering checks

Run notebooks zero two and zero three. The latter tests the final source, starts an isolated real HTTP service for ingestion checks and verifies local Granite output. Inspect actual test names, counts and failure records. The bounded queue rejects overload explicitly. Invalid inputs, gaps, source provenance and consumer errors have regression coverage. Queue acceptance is not completed inference; each timing boundary is labeled.

## 08 / Inspect original service measurements

Notebook zero four collects actual timings and process counters from a bounded localhost computation service on LinuxONE. It observes baseline behavior, deliberately increases the real request computation, then records recovery. A separate Isolation Forest is fitted on baseline observations only. Here is the actual executed notebook with the architecture, source call and measured outputs. No latency values were invented. This small experiment is not a production hospital incident.

## 09 / Review IBM Toolkit preparation

Notebook zero five trains a separate Random Forest challenger using the existing training and validation runs, exports ONNX and checks its structure. That family appears in IBM Snap ML import documentation. The participant has no configured registry entitlement, so the supported IBM container and acceleration have not run. Toolkit deployment guidance is applied to identity, filesystem and protected access, with remaining rootful and host-networking limits stated.

## 10 / Deploy without losing evidence

Build the application on LinuxONE using the provided deployment script. Deliberate replacement preserves the state volume and a stopped rollback container. The application runs with limited CPU, memory and PIDs, a read-only root, non-root identity and dropped capabilities. Run verification to check model consistency, local generation and restart persistence. Public access uses a separate TLS proxy and a narrow SELinux policy; authentication stays enabled.

## 11 / Start a scenario and inspect the warning

In the deployed dashboard, select database connection pressure and four-times replay. The interface labels synthetic event time and the fixed scenario severity. Wait for warmup and persistent risk. Select an incident and inspect its retained measurements, declared affected software services and runbook. Local Granite cites verified evidence and cannot run shell commands. The response preview compares the same future workload with and without a simulator action. It shows deferred optional work with the modeled benefit.

## 12 / Cover the remaining scenarios and external input

Healthy load, surge and shift examples should not be equated with failures. The gallery also shows pool exhaustion, retry cascades, memory pressure and sudden failure. For authorized real telemetry, explicitly start an external session and send already-aggregated windows through the adapter. The server overrides synthetic provenance, and response previews are disabled. A model trained on our simulator requires validation and calibration before operational use on an organization’s data.

## 13 / Learnings, cleanup and final submission

The main lessons were native platform compatibility, consistent evaluation horizons, honest timing boundaries and complete evidence references. Keep required models, lab volumes, executed notebooks and source. Remove only verified reproducible build intermediates, never unreviewed data. Review the pitch, output gallery, summary and resource credits. Upload the compulsory video under three minutes to an accessible YouTube or Vimeo link. This longer guide is supporting material; submit the event form manually.
