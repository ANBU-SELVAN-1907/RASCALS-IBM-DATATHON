# Prerequisite lab evidence

Before project implementation, the relevant sample workflows from the guidebook's linked official repository executed on the participant's LinuxONE VM:

| Notebook | Result | Finished (17 October 2026, IST) |
|---|---|---|
| `Churn_Scikit_PyTorch.ipynb` | 31 code cells executed successfully | 13:18:16 |
| `Loan_Approval_Demo.ipynb` | 9 code cells executed successfully | 13:19:40 |

Source commit inspected: `345786bedcfb14ba03a16ea59c3dda5d998bbef3`. Platform: RHEL 9.8 host, s390x runtime, Python 3.12.15 inside the supplied container.

The guidebook requires **both** Predictive AI Hybrid AI scenarios (multi-model) and Predictive AI + Generative AI before the team's solution. The public repository does not explicitly map these category names to notebook filenames. The two executed workflows are the closest matches identified, but successful execution is not an organizer certificate or confirmation of prerequisite acceptance. The team must confirm the assigned pair through official event materials or the IBM SME helpdesk if unclear.

Original lab outputs remain separately backed up in the participant workspace and Jupyter `shared/labs`. They are not relabeled as original project code. No lab token, private key or synthetic loan applicant document needs to be published in this repository.

Key learning points: fit preprocessing on training data and reuse it for held-out data; distinguish prediction from generation; validate generated schemas and claims; actual s390x execution does not by itself prove hardware accelerator use.
