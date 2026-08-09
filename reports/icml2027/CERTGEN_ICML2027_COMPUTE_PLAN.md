# CertGen ICML 2027 — Compute Plan

All results in this report are engineering or synthetic-validation evidence only. They are not real-generator or empirical paper evidence. `claim_allowed=false`.

Local CPU measurements are quick=4.736s, medium=4.904s, and overnight=27.790s on the recorded workstation; zero CPU work remains.

GPU estimates below are planning ranges and **PLANNING_ESTIMATE_NOT_MEASURED** until authenticated T4 x2 telemetry exists.

| Stage | Planning range |
|---|---:|
| diagnostic | 10–30 min |
| preflight | 15–45 min |
| 1k generation | 0.25–1.5 h |
| 1k features | 0.25–0.75 h |
| DINO preflight / features | 0.25–2 h each |
| cross-family preflight | 0.5–2 h |
| 10k generation / features | 1–6 h / 1–4 h |
| FFHQ / ImageNet / text-to-image | 2–12 h each after protocol approval |

The deterministic planner's prospective CIFAR 10k point estimate is 1.374 aggregate GPU-hours with one session, 5,000-image shards, and end-of-stage copyback; it remains an unauthenticated planning value.
