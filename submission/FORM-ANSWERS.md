# RASCALS_IBM Z Datathon 2026 Project

Solution: ContinuityGuard. Team: ANBU SELVAN T; SAHANA G; DHARSHINI E; POOJA V. Institution: Hindustan Institute of Technology and Science.

## Problem

```text
Hospital digital services share infrastructure. Developing pool exhaustion, retry cascades or resource pressure can delay access to results and disrupt dependent services before an operator has a useful warning. ContinuityGuard addresses system availability: identify abnormal activity as telemetry arrives, warn of an approaching service-objective breach, show affected software services and provide evidence-linked investigation steps. Hospital IT operators are the target users. The prototype uses controlled synthetic service telemetry; it does not use patient data or make clinical decisions.
```

## Solution overview

```text
A validated bounded queue feeds causal rolling features on LinuxONE. A calibrated logistic model scores near-term breach risk. Initial threshold warnings are retained; ML filters low-risk repeats, while observed breach limits bypass filtering. Isolation Forest separately scores novelty. Persistent risk creates incidents with measurements, declared dependencies and runbooks. Local Granite generates schema-constrained wording with complete evidence IDs and a labeled fallback. A paired simulator previews allowlisted action versus no action under identical demand. Jupyter separates whole-run training, calibration, validation and fresh final testing. The frozen V5 test warned before 130/135 incidents, with median early lead 11s versus 11s for thresholds; precision was 45.3% versus 43.5%. These are synthetic results, not proof of consistent superiority.
```

## IBM Z / LinuxONE use

```text
Training, testing, scoring, novelty, local Granite, API processing and SQLite journaling execute natively on our LinuxONE Community Cloud s390x VM. Six saved Jupyter notebooks retain outputs, model hashes and failure tests. Podman runs the app as UID 1000 with a read-only root, CPU/memory/PID limits, dropped capabilities, no-new-privileges and authenticated TLS/SSH access. 43 native tests passed. A real local HTTP/queue/journal trial processed 1000/1000 synthetic window events at 100 offered events/s over 10 seconds. Platform screenshots and verification outputs are public. The two relevant provided sample labs executed before project work; exact organizer prerequisite mapping still needs confirmation. We do not claim z/OS integration, AI hardware acceleration or production-scale performance.
```

## Value and beneficiaries

```text
Hospital IT operators benefit from one reviewable path from warning to evidence, software-service priority, investigation and response preview. The aim is earlier attention to developing faults and clearer operational tradeoffs, supporting the availability of essential digital services. The preview reports modeled successful urgent-results transactions and deferred optional work together, with no real remediation. The implementation is reusable for authorized service telemetry after domain validation and calibration. Current value is a working, tested LinuxONE prototype and reproducible evaluation, not a measured patient outcome or proven real-world outage reduction. The latest results include misses, false alerts, baseline comparison and uncertainty rather than claiming perfect detection.
```

## Open-source resources

```text
https://github.com/linuxone-community-cloud/jupyter-lab-ml
https://scikit-learn.org/
https://numpy.org/
https://github.com/IBM/ai-toolkit-for-z-and-linuxone
https://onnx.ai/
https://github.com/onnx/sklearn-onnx
https://scipy.org/
https://joblib.readthedocs.io/
https://fastapi.tiangolo.com/
https://www.starlette.io/
https://www.uvicorn.org/
https://docs.pydantic.dev/
https://jupyter.org/
https://pandas.pydata.org/
https://matplotlib.org/
https://psutil.readthedocs.io/
https://www.sqlite.org/
https://podman.io/
https://github.com/abetlen/llama-cpp-python
https://github.com/ggml-org/llama.cpp
https://huggingface.co/ibm-granite/granite-4.0-h-350m-base
https://github.com/python-pillow/Pillow
https://github.com/pypdfium2-team/pypdfium2
https://github.com/imageio/imageio-ffmpeg
https://ffmpeg.org/
Full credits: https://github.com/ANBU-SELVAN-1907/RASCALS-IBM-DATATHON/blob/main/docs/ATTRIBUTIONS.md
```

Copy each block into its corresponding portal field. Upload the reviewed PDF and a <=3-minute accessible YouTube/Vimeo video. Public repository: https://github.com/ANBU-SELVAN-1907/RASCALS-IBM-DATATHON

Manual portal submission and prerequisite mapping confirmation remain team actions.
