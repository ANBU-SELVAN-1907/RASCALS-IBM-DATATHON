# IBM AI Toolkit: applied guidance and explicit execution boundary

Reference: [AI Toolkit for IBM Z and IBM LinuxONE](https://github.com/IBM/ai-toolkit-for-z-and-linuxone). We used its [deployment guidance](https://github.com/IBM/ai-toolkit-for-z-and-linuxone/blob/main/deployment-guidelines.md) to review container separation, identity, filesystem controls and protected network access. This is not IBM certification or a claim that the supported Toolkit runtime was installed.

| Area | Applied here | Evidence / remaining limit |
|---|---|---|
| Separate functions | Jupyter, application and TLS proxy run separately | Native containers and systemd proxy |
| Identity and filesystem | UID 1000 app, read-only root, no-new-privileges, dropped capabilities | Live platform proof; Podman host operation is still rootful |
| Network protection | TLS proxy and existing token authentication; backends stay loopback | Public connectivity evidence; self-signed certificate needs manual verification |
| SELinux | Enforcing; narrow proxy-to-backend port-label policy | Broad `httpd_can_network_connect` remains off |
| Data controls | Private keys/tokens excluded; model hashes and original measurement hashes retained | Hashes establish consistency, not signed provenance |
| Network isolation | Current application still uses host networking | Explicit limitation; do not advertise production isolation |

## Snap ML preparation

Notebook `05_toolkit_readiness.ipynb` actually trains a separate 40-tree Random Forest challenger on LinuxONE and checks its ONNX export. It uses only existing training/validation splits; it does not inspect a new test set or replace the frozen predictor. Its validation PR-AUC and export hash are retained in `artifacts/toolkit/readiness.json`.

IBM lists Random Forest among supported model-import families for [Snap ML](https://snapml.readthedocs.io/en/latest/model_import.html). The deployed V5 logistic pipeline remains in standard scikit-learn; no Snap ML serving/parity claim is made. This separate Random Forest preparation predates V5 and does not replace its selected detector. Export/checking an ONNX model is **not** Snap ML execution. The IBM container requires registry credentials; the participant reported no entitlement/login. Accordingly, `toolkit_container_executed=false` and `hardware_acceleration_verified=false` remain in the report.

After the team obtains authorized registry access, the optional path is to select an entitled pinned image from [IBM's Snap ML documentation](https://github.com/IBM/ibmz-accelerated-for-snapml), import the candidate using its documented supported API, check raw probability parity, then revalidate calibration, alert policy and incident metrics. Record the selected optimized tree format and actual hardware use before claiming acceleration. This work is planned, not represented as done.
