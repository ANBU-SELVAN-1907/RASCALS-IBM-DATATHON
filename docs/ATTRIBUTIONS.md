# Resources and assistance

The application code, simulator, feature pipeline, evaluation, dashboard and documentation were created during the event work recorded in this repository. Established libraries and supplied IBM labs remain their authors' work.

| Resource | Direct source | Use |
|---|---|---|
| IBM LinuxONE Jupyter/ML environment | https://github.com/linuxone-community-cloud/jupyter-lab-ml | Prerequisite examples, s390x Python/ML environment and supplied Granite model |
| IBM RHEL setup | https://github.com/linuxone-community-cloud/jupyter-lab-ml/blob/main/README_RHEL.md | Podman path for the actual RHEL VM |
| Python | https://www.python.org/ | Runtime, bounded data structures, SQLite and concurrency |
| NumPy | https://numpy.org/ | Numerical arrays and simulator random streams |
| SciPy | https://scipy.org/ | Probability-logit transformation |
| scikit-learn | https://scikit-learn.org/ | Forecast candidates, calibration, Isolation Forest and metrics |
| joblib | https://joblib.readthedocs.io/ | Trusted local model serialization |
| pandas | https://pandas.pydata.org/ | Notebook result tables |
| Matplotlib | https://matplotlib.org/ | Saved benchmark plots |
| Jupyter / nbclient / nbformat | https://jupyter.org/ | Native LinuxONE training/testing notebooks and executed outputs |
| FastAPI | https://fastapi.tiangolo.com/ | Application API |
| Pydantic | https://docs.pydantic.dev/ | Bounded telemetry validation |
| Starlette | https://www.starlette.io/ | ASGI and API testing through FastAPI |
| Uvicorn | https://www.uvicorn.org/ | ASGI server |
| HTTPX | https://www.python-httpx.org/ | Correctness testing transport |
| psutil | https://psutil.readthedocs.io/ | Actual host/process resource measurements |
| SQLite | https://www.sqlite.org/ | Local telemetry and audit persistence |
| Podman | https://podman.io/ | Native s390x containers, caps and persistent volumes |
| llama-cpp-python | https://github.com/abetlen/llama-cpp-python | Local constrained generation |
| llama.cpp | https://github.com/ggml-org/llama.cpp | Local model inference backend |
| IBM Granite | https://huggingface.co/ibm-granite/granite-4.0-h-350m-base | Upstream model family; actual big-endian GGUF supplied in the organizer image |

The source-model card is not a claim that we performed an independent conversion or authenticated the organizer GGUF against upstream weights. We use the supplied artifact and record the image digest. Consult each exact component/model license before redistribution. This repository does not redistribute the lab image or model weights. Source code licensing is not a substitute for third-party dependency terms.

## Problem evidence

[NHS England's 20 June 2024 impact update](https://www.england.nhs.uk/london/2024/06/20/update-on-cyber-incident-clinical-impact-in-south-east-london-thursday-20-june/) reported provisional postponed appointment/procedure counts following the Synnovis incident. It establishes why digital-service continuity matters; it does not validate this prototype or imply it would have prevented that incident.

## Event rules

- Participant guidebook: https://docs.google.com/document/u/0/d/1tt0ZhUyirXDtHIEum3JhG-ZIj6y-YpUc5e15mPT78w4/mobilebasic
- Linked Official Rules: https://www.starhacks.org/ibmzdatathon-official-rule
- Submission portal: https://hack2skill.com/event/datathon-2026

## AI assistance disclosure

The prerequisite examples also use [PyTorch](https://pytorch.org/); their upstream notebook source and data are credited to the organizer-linked repository, not presented as original project code.

Submission-media tooling additionally uses [ReportLab](https://github.com/MrBitBucket/reportlab-mirror), [Pillow](https://github.com/python-pillow/Pillow), [pypdfium2](https://github.com/pypdfium2-team/pypdfium2), [imageio-ffmpeg](https://github.com/imageio/imageio-ffmpeg) and its bundled [FFmpeg](https://ffmpeg.org/). Review their respective licenses when redistributing tools; only generated media is included here. Microsoft Zira/System.Speech supplies the labeled synthetic narration on Windows; it is not an open-source model or a team member's voice.

OpenAI Codex assisted with architecture, implementation, debugging, training orchestration, tests, documentation and submission preparation in this chat at the participant's request. The team is responsible for understanding, verifying, and submitting the work in accordance with organizer guidance. Do not describe the project as unaided or hide assistance in response to a judging question. Assistance is not a claim of IBM endorsement or of originality beyond the specific implementation.

No other team's codebase was imported as the application. The mandatory IBM sample notebooks are credited as prerequisite learning examples, not claimed as the team's original solution.


Additional references: [IBM Journey to AI on Z](https://www.ibm.com/support/z-content-solutions/journey-to-ai-on-z/) explains native AI deployment context. [NHS England, 20 June 2024](https://www.england.nhs.uk/london/2024/06/20/update-on-cyber-incident-clinical-impact-in-south-east-london-thursday-20-june/) supports the slide's 1,294 postponed-appointment context for 10-16 June across two affected trusts. The prototype was not evaluated on that incident and does not claim to prevent ransomware. [Prettier](https://github.com/prettier/prettier) formatted the interface source. The participant supplied the copied submission-guidelines reference; its requirements are not evidence of organizer acceptance.
