# CertGen Real-Execution Closure Baseline

Repair baseline captured on 2026-07-21 on branch `master`, commit `bff335aa648fd19e2fa7e3cfea293a6ca519a68b`. The large dirty user-owned worktree was preserved; no unrelated modification or deletion was reverted.

- Python `3.11.9`; Ruff `0.15.8`; mypy `2.1.0`.
- Default local-safe tests: `279 passed, 4 deselected`.
- Integration audit: `4 passed, 279 deselected`.
- Statistical lane: `31 passed`; artifact lane: `25 passed`; runtime closure lane: `25 passed` at intake.
- Compilation, imports, Ruff, paper build/firewall, privacy/release safety, registry, CVPR, forensic, and V9 audits passed.
- Critical mypy passed; full mypy reproduced `111 errors in 34 files`.
- Five canonical notebooks passed deterministic regeneration and static validation.
- The local `cifar-10-python.tar.gz` candidate existed but was not validated because real reference execution was explicitly outside this pass.
- The inherited portable-archive evidence was stale (`718` members and `10` portable tests) and required regeneration.

Baseline classification: scientific/statistical core healthy; real-execution handoff required targeted contract repairs; empirical evidence absent; reference validation remained the first authorized external-input boundary.
