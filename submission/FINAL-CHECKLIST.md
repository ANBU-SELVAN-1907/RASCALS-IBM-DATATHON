# Submission handoff

Prepared for team RASCALS. The project is a working LinuxONE prototype; no score or prize is guaranteed.

- **Repository:** https://github.com/ANBU-SELVAN-1907/RASCALS-IBM-DATATHON
- **Challenge:** Real-Time AI for Critical Decisions / System Anomaly Detection.
- **Form text:** copy the five blocks in `FORM-ANSWERS.md`; each is below 1,024 characters.
- **Pitch:** `RASCALS-ContinuityGuard-Pitch.pdf`, 14 readable slides, approximately 0.41 MB, below the 5 MB limit. Includes problem, solution, flows, models, outputs, scenarios, distinctive features and datathon learnings.
- **Compulsory video draft:** `RASCALS-ContinuityGuard-Walkthrough.mp4`, 2:44.60 container duration, 1920x1080, H.264/AAC. This is a narrated walkthrough of actual saved evidence, not continuous live recording. The synthetic voice is labeled. Review it and preferably replace narration with team members explaining their own work using `VIDEO-SCRIPT.md`.
- **Supporting video:** `RASCALS-Implementation-Guide.mp4`, 6:17.99 container duration, Full HD. Covers VM/access, source, training, evaluation, tests, measured data, Toolkit boundary, deployment and operator workflow. Do not upload it as the compulsory <=3-minute video.
- **Complete explanation:** `../SUMMARY.md`, `../docs/OUTPUTS.md` and `../docs/DEMO-GUIDE.md`.
- **Supporting documentation:** link the repository's `docs/DEPLOYMENT.md`, `docs/METHODOLOGY.md` and `evidence/`.
- **Resources:** the fifth form block contains direct resource links; fuller attribution is in `docs/ATTRIBUTIONS.md`.

## Team actions still required

1. Confirm with the organizer that the executed Churn and Loan sample notebooks satisfy the exact two mandatory lab assignments. The public repository did not explicitly map notebook names to the guidebook categories. We do not certify acceptance.
2. Review and understand the model, simulator assumptions, precision tradeoff and assistance disclosure. Do not claim production hospital validation, proven causality, AI accelerator use, z/OS deployment or guaranteed novelty.
3. Upload the reviewed video to YouTube or Vimeo with visibility that permits judges to watch without requesting access. A GitHub MP4 does not replace the requested YouTube/Vimeo field. Check the final uploaded duration.
4. Open the public repository and video in a signed-out browser. Upload the PDF or supply its accessible link. Enter the actual video URL and other fields manually in the event portal.
5. Submit before the organizer's deadline. The user-provided portal deadline is **18 October 2026, 22:00 IST**; target 21:00 IST and verify the portal timezone.

The portal has not been submitted, and no YouTube/Vimeo upload or organizer confirmation is claimed. Protect the app/Jupyter tokens and SSH key; none belong in a public repository or recording.

## Verified technical handoff

Five executed project notebooks have success records on s390x. The final native suite passed 37 tests with no failures/errors/skips. The frozen main model is v3; a separate original measured-service CSV and an optional validation-only ONNX challenger are clearly distinguished. Registry entitlement is unavailable: no supported IBM Toolkit runtime or acceleration is claimed. Jupyter and the dashboard are reachable over authenticated TLS by public IP, with manual certificate verification required; see `../docs/PUBLIC-ACCESS.md`.
