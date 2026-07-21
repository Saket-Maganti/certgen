# Final Runtime-Hardening Test Matrix

This matrix distinguishes local proof from real execution. The final command ledger is authoritative for exit codes and durations.

| Lane | Expected final scope | Evidence boundary |
|---|---|---|
| Default non-recursive pytest | `241 passed, 4 deselected` in 3.94s | local/fixture validation only |
| Explicit integration audit | `4 passed, 241 deselected` in 18.06s; each wrapper launches the default lane | integration validation only |
| Runtime hardening + portable archive | `11 passed` in 1.10s | fake adapters; no real models |
| Portable archive | 1 non-Git test | release validation only |
| Statistical | 31 tests | synthetic/statistical implementation proof |
| Artifact contracts | 25 tests | fixtures and hostile archives only |
| CVPR architecture/runtime/gates | `15 passed`; V9 compatibility `22/22` | structural/compatibility proof |
| Extended synthetic/gates | 3 tests | synthetic validation only |
| Synthetic end-to-end command | preflight→2 workers→resume→features/import/cache/gates/certificate/ranking/firewall | `synthetic_validation_only`, claim false |
| Notebook static analyzer | 5/5 notebooks | static only; real Kaggle required |
| Compile/import/Ruff/critical mypy | pass; critical mypy `41 source files` | software quality, not evidence |
| Full mypy | exit 1; exactly `111 errors in 34 files`, unchanged from baseline | debt inventory |
| Paper/firewall/privacy/release/diff | pass; paper 5 pages/179,907 bytes/3 overfull boxes | publication/release hygiene only |
| Clean archive probe | `ARCHIVE_VERIFIED`; 688 members; import pass; portable test `1 passed` | release validation only |

Failure injection covers worker crash, timeout, OOM, corrupt image/cache/ZIP, duplicate seed, missing shard/integrity member, preprocessing mismatch, wrong revision, changed resume config, missing cache asset and insufficient disk.
