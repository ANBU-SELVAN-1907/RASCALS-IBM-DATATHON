# RASCALS submission answers

**Title:** `RASCALS_IBM Z Datathon 2026 Project`  
**Project/subtitle:** ContinuityGuard  
**Challenge:** Real-Time AI for Critical Decisions - System Anomaly Detection

Copy only the text inside each block into the corresponding field. Finalize deployment and recording links before submitting. All five text blocks are validated to be under 1,024 characters by `scripts/validate_submission.py`.

## What is the problem you are trying to solve?

```text
Hospital digital services depend on shared infrastructure. Developing database bottlenecks, retry cascades or resource pressure can delay access to results and disrupt dependent services before an operator receives a useful warning. A simple threshold may react late or confuse demand changes with failure. ContinuityGuard addresses this system-availability problem: identify abnormal activity as telemetry arrives, warn of an approaching service-objective breach, show the affected software services and provide an evidence-linked investigation path. The prototype uses synthetic service telemetry, not patient data or clinical decisions.
```

## How are you planning to solve the problem? (Brief overview)

```text
ContinuityGuard processes one-second service telemetry through a validated bounded queue and causal rolling features. A calibrated boosted-tree model forecasts a new service-objective breach within 60 seconds; Isolation Forest separately scores novelty. A validation-selected persistence policy creates incidents linked to measurements, a declared dependency map and operator runbooks. A paired simulator previews an allowlisted response against no action under the same future workload. Local Granite generates strictly constrained, validated explanations, with a labeled fallback. Python, scikit-learn, FastAPI, SQLite and Jupyter support the pipeline. Whole runs and distinct seeds separate training, calibration, selection and final testing. On 60 final synthetic runs, the system warned before 43/47 service incidents; median early lead was 37 seconds versus 9 for static thresholds. Precision was 61.4% versus 68.3%, an explicit tradeoff.
```

## How does your solution leverage IBM Z / LinuxONE technologies?

```text
Training and testing execute through saved Jupyter notebooks on our LinuxONE Community Cloud s390x VM (RHEL 9.8, 3 virtual CPUs, 7.3 GiB RAM). The application processes telemetry, extracts features, performs forecast and novelty inference, journals decisions and runs local Granite explanation on LinuxONE. Podman packages the native runtime; the deployment configuration uses a non-root user, resource limits, a read-only root filesystem and loopback access through SSH. We retain model hashes, executed notebooks, test records and resource measurements. A paced direct-engine test processed 100 synthetic window events/s with 9.03–53.60 ms p95 across two runs per four-event batch, excluding HTTP/queue/browser delay. The provided predictive and predictive/generative samples executed before project work; exact prerequisite acceptance remains with the organizer. We do not claim z/OS integration or hardware AI acceleration.
```

## What value does your solution deliver, and who benefits?

```text
Hospital IT operators are the intended users, particularly teams with limited monitoring capacity. Earlier warning and service-impact ordering can give them useful time to investigate a developing fault and protect essential digital-service availability. Patients and staff are potential indirect beneficiaries; no clinical benefit has been measured. Our synthetic final test observed 37-second median early warning, four missed incidents and zero alerts during 10 healthy service-hours, while overall precision was 61.4% because unmatched alerts still occurred on fault runs. The response preview exposes both modeled improvements and deferred-work costs before an operator acts. All results are labeled synthetic and require validation with authorized real telemetry before adoption. The value is a traceable operational decision, not an unexplained anomaly score or autonomous remediation.
```

## Open-source resource links

```text
https://github.com/linuxone-community-cloud/jupyter-lab-ml
https://www.python.org/
https://numpy.org/
https://scipy.org/
https://scikit-learn.org/
https://joblib.readthedocs.io/
https://pandas.pydata.org/
https://matplotlib.org/
https://jupyter.org/
https://fastapi.tiangolo.com/
https://docs.pydantic.dev/
https://www.starlette.io/
https://www.uvicorn.org/
https://www.python-httpx.org/
https://psutil.readthedocs.io/
https://www.sqlite.org/
https://podman.io/
https://github.com/abetlen/llama-cpp-python
https://github.com/ggml-org/llama.cpp
https://huggingface.co/ibm-granite/granite-4.0-h-350m-base
Full attribution and assistance disclosure: https://github.com/ANBU-SELVAN-1907/RASCALS-IBM-DATATHON/blob/main/docs/ATTRIBUTIONS.md
```

## Links

- Repository: https://github.com/ANBU-SELVAN-1907/RASCALS-IBM-DATATHON
- Pitch PDF: after export/push, use the actual `submission/RASCALS-ContinuityGuard-Pitch.pdf` from this repository, or upload the local PDF (maximum 5 MB).
- Supporting documentation: https://github.com/ANBU-SELVAN-1907/RASCALS-IBM-DATATHON/blob/main/docs/METHODOLOGY.md
- Video: record the real demonstration using [VIDEO-SCRIPT.md](VIDEO-SCRIPT.md), upload to an accessible YouTube/Vimeo link, then enter that actual URL. No hosted final video is claimed yet.

The portal closing time supplied by the participant is **18 October 2026, 10:00 PM IST**. Aim to finish manual submission by 9:00 PM IST. Do not treat this as a guarantee against later official changes. The linked Official Rules prohibit automated entries, so the team lead should submit manually.
