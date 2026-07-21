# CertGen Maximum-Ceiling Test Matrix

| Lane | Baseline | Final target |
|---|---:|---:|
| Default non-recursive | 266 passed, 4 deselected | 274 passed, 4 deselected |
| Explicit integration audit | 4 passed, 266 deselected | 4 passed, 274 deselected |
| Statistical | 19 passed | Pass |
| Artifact contracts | 25 passed | Pass |
| Runtime hardening | 10 passed | Pass |
| Real-execution closure | 9 passed | Pass |
| Final run-ready | 8 passed | Pass |
| Post-cache closure | 3 passed | Pass |
| Maximum-ceiling contracts | New | 8 passed |
| CVPR / forensic / V9 / final pre-run | Pass | Pass |
| Notebooks | 5/5 static; deterministic | 5/5 static; deterministic |
| Ruff / critical mypy | Pass / 41 files pass | Pass |
| Full mypy debt | 111 errors in 34 files, 295 checked | Must not increase |
| Paper | 5 pages | Compile |
| Portable archive | Fixed archive verified | 823 members; 10 portable tests; 5 notebooks; rehearsal pass |

No lane may require internet, CUDA, CIFAR, checkpoints, real outputs, or empirical claims.
