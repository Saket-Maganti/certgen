# CertGen Final 100 Percent Pre-Run Baseline

Baseline captured before the final pre-run closure implementation on branch `master`, commit `bff335aa648fd19e2fa7e3cfea293a6ca519a68b`.

The pre-existing dirty worktree was preserved: 91 modified files, 83 deleted files, and 294 untracked paths at intake. No reset, checkout, clean, or deletion was performed.

## Local-safe baseline

- Python compilation and eight critical package imports: pass.
- Default tests: `258 passed, 4 deselected`.
- Integration audit lane: `4 passed, 258 deselected`.
- Statistical lane: `31 passed`.
- Artifact-contract lane: `15 passed`.
- Runtime-hardening lane: `11 passed`.
- Real-execution-closure lane: `9 passed`.
- Final run-ready closure lane: `8 passed`.
- Notebook static audit: 5/5 pass; two regenerations are byte-identical.
- CVPR audit: 8/8; forensic audit: 8/8; V9 compatibility: 22/22.
- Paper firewall, privacy scan, release scan, Ruff, paper build, and `git diff --check`: pass.
- Critical mypy: no issues in 34 source files.
- Full mypy: unchanged historical debt of `111 errors in 34 files` across 286 source files.
- Paper: five pages; three non-fatal overfull boxes.

## Gap classification

| Finding | Classification | Baseline evidence |
|---|---|---|
| Shared worker-version contract | `CONFIRMED` | orchestrator defaults to `certgen.worker.v2` while feature and extractor-preflight workers emit `certgen.worker.v3` |
| Study/profile-bound reference draw builder | `PARTIALLY_FIXED` | a generic draw helper and CLI exist, but no canonical profile/study/control role contract exists |
| Canonical control-artifact builder | `CONFIRMED` | no canonical builder or output package exists |
| Canonical certificate-input builder | `CONFIRMED` | certificates consume manually assembled NPZ bundles |
| Artifact-driven next actions | `CONFIRMED` | late-stage commands contain hardcoded placeholder paths |
| Separate live/portable reporting | `PARTIALLY_FIXED` | archive reports portable checks, but the final summary conflates them |
| Explicit CLIP redistribution policy | `PARTIALLY_FIXED` | local snapshot handling exists, but release/legal fields and exclusion policy are incomplete |

Baseline evidence is local software and fixture validation only. No real CIFAR data, model asset, Kaggle job, CUDA execution, empirical metric, certificate, or paper evidence was produced; `claim_allowed=false`.
