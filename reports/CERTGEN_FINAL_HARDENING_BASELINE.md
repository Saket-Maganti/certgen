# CertGen Final Hardening Baseline

Captured before runtime-hardening edits on branch `master`, commit `bff335aa648fd19e2fa7e3cfea293a6ca519a68b`. The checkout was already heavily dirty: 87 modified, 83 deleted and 240 collapsed untracked status entries; staged count was zero. All were treated as user-owned state.

| Check | Baseline result |
|---|---|
| Full local-safe pytest | `234 passed in 36.16s`, exit 0 |
| Statistical lane | `31 passed`, exit 0 |
| Artifact-contract lane | `25 passed`, exit 0 |
| Extended synthetic/gate lane | `3 passed`, exit 0 |
| Compilation/import | pass |
| Notebook registry/static checks | registries pass; CVPR audit `8/8`; canonical notebooks `5/5` |
| Forensic / V9 compatibility | `8/8`; `22/22` |
| Ruff | pass |
| Critical mypy | pass across 24 selected files |
| Full mypy debt | exit 1; exactly `111 errors in 34 files` |
| Paper | five pages, 179,907 bytes; three non-fatal overfull boxes |
| Firewall / artifact / release / privacy / diff | pass |
| Real execution | blocked by missing reference input |
| Clean canonical archive | absent before this pass |

No baseline command downloaded data/models, used a GPU, ran Kaggle, or created scientific evidence.
