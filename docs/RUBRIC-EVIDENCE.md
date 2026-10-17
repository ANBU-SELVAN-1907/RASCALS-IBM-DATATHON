# RASCALS: rubric and requirement evidence map

Project title: **RASCALS_IBM Z Datathon 2026 Project**. Solution: **ContinuityGuard**.

Team: ANBU SELVAN T; SAHANA G; DHARSHINI E; POOJA V. Institution: Hindustan Institute of Technology and Science.

This map supports review; it does not award marks or guarantee a placing. The participant-supplied `IBM_Z_Datathon_2026_Submission_Guidelines.md` and linked Participant Guidebook define the requirements. A copy of the supplied submission guidelines is retained in `submission/IBM_Z_Datathon_2026_Submission_Guidelines.md` with source attribution. Guidebook: https://docs.google.com/document/d/1tt0ZhUyirXDtHIEum3JhG-ZIj6y-YpUc5e15mPT78w4/mobilebasic

| Criterion | What is implemented | Inspectable evidence | Limit to state |
|---|---|---|---|
| Community value and theme | Early system-risk warning for infrastructure supporting hospital software services; priorities protect essential service availability | Problem slide, live sandbox, paired response, `docs/RESULTS.md` | Potential community value; no measured patient benefit or production prevention |
| Novelty and originality | Evidence-linked warning, declared dependency priorities, constrained local wording, and same-workload action/no-action preview in one reproducible pipeline | Original `continuityguard/` implementation, Git history, paired-history regression test | Established ML methods; no world-first or unaided-development claim |
| Technical architecture | Validated bounded ingestion; causal feature windows; calibrated forecasting; independent novelty; threshold guard; persistent incidents and journal | Architecture slide, `web.py`, `runtime.py`, `models.py`, executed notebooks | One VM and one consumer; no multi-node availability or peak-scale claim |
| AI/ML on LinuxONE | Native s390x fitting, calibration, model/policy selection, evaluation, inference and local Granite generation | Three executed notebooks; model manifest; `evidence/jupyter-ai-proof.json`; `/api/platform-proof` | Linux on LinuxONE, not z/OS; no proven accelerator use |
| Security and compute | Non-root process; CPU/memory/PID limits; read-only root; no-new-privileges; capabilities dropped; SSH loopback access; bounded actual POST bytes | Containerfile, deployment script, live platform proof and screenshot, deployment verification JSON | Host networking is a tradeoff; prototype token auth; no security certification |
| Scalability | Bounded queue and event history, batch inference, explicit HTTP 429, measured HTTP path | `artifacts/http-benchmark.json`; queue-saturation and consumer-failure tests | Short local-VM trials with synthetic fixtures; not WAN/browser latency or production capacity |
| Execution and pitch | Working demo, team-named PDF, narrated evidence video, source and form answers | `submission/`, `evidence/`, public GitHub | Video is a saved-evidence walkthrough with labeled synthetic voice; team review/upload required |
| AI innovation award | Integration of predictive warning, accountable evidence and a controlled decision preview | Demo, model comparison, failure tests, source | Innovation is in this integration; expert judges determine originality and impact |

## Mandatory requirements: distinguish evidence from certification

| Requirement | Status |
|---|---|
| Project title contains team name | Exact title in team metadata, pitch, README and app title |
| Theme 1 / System Anomaly Detection | Explicit problem, streaming detector, alert and investigation workflow |
| Code/public repository | https://github.com/ANBU-SELVAN-1907/RASCALS-IBM-DATATHON |
| Both prerequisite AI labs before project work | Churn multi-model and Loan predictive/generative examples executed before original project implementation; timestamps/source commit retained. Exact mapping to organizer-assigned prerequisites remains unconfirmed; see `LABS.md` |
| Compulsory video, maximum three minutes | Prepared MP4 and duration manifest; final accessible YouTube/Vimeo URL must be supplied by the team |
| PDF no larger than 5 MB | Enforced by generation and package validation; rendered pages reviewed |
| Open-source resource URLs | Form block plus `ATTRIBUTIONS.md` |
| Original work during build window | Project history and executed notebook timestamps retained; assistance disclosed. Team must confirm organizer interpretation and personal eligibility |
| Registration, college status, abstract and mandatory session attendance | Team/organizer records required; cannot be established by code execution |
| Manual portal submission by deadline | Not submitted by this agent. Follow the actual portal clock and official rules |

## Do not make these claims

Do not claim guaranteed full marks, a bug-free system, real hospital outage prevention, autonomous remediation, learned causal root cause, better performance on every metric, production calibration, encrypted/signed immutable audit records, real request throughput from synthetic aggregate events, z/OS deployment or hardware acceleration. Report the latest v3 results, confidence intervals and misses together. v1/v2 reports are development history, not the current result.
