# CertGen Final Run-Ready Baseline

Baseline captured before the final run-ready value-upgrade implementation on branch `master`, commit `bff335aa648fd19e2fa7e3cfea293a6ca519a68b`.

The pre-existing dirty worktree was preserved: 91 modified files, 83 deleted files, and 279 untracked paths at intake. Those changes are user-owned and were not reset or discarded.

## Results

- Compile and ten critical imports: pass.
- Default non-recursive tests: `250 passed, 4 deselected`.
- Explicit integration audits: `4 passed, 250 deselected`.
- Statistical lane: `31 passed`.
- Artifact-contract lane: `15 passed`.
- Runtime-hardening lane: `11 passed`.
- Real-execution-closure lane: `9 passed`.
- Canonical notebook regeneration: deterministic for all five notebooks.
- Notebook static analyzer: 5/5 pass; real Kaggle execution remains untested.
- CVPR audit: 8/8 pass.
- Forensic audit: 8/8 pass.
- V9 compatibility audit: 22/22 pass.
- Paper firewall, release scan, privacy scan, artifact registry, registry audit, Ruff, paper build, and `git diff --check`: pass.
- Scoped critical mypy: no issues in 28 source files.
- Full mypy: the historical baseline remains `111 errors in 34 files` across 280 source files.
- Paper build: five pages, with three non-fatal overfull boxes.

## Confirmed closure gap

The passing historical audits do not exercise the live registry-to-builder continuity required by the final prompt. Direct inspection confirms that the canonical preflight builder accumulates blockers from every CIFAR registry row, including unselected CFM and DINO rows. The existing synthetic runtime is contract-rich but does not execute the requested builder-faithful selected-profile path.

Baseline verdict:

`CVPR_CORE_AND_RUNTIME_CONTRACTS_VALID / REAL_RUN_HANDOFF_PARTIAL / BLOCKED_BY_REFERENCE_INPUT_AND_LIVE_BUILDER_DEFECTS`

All baseline commands were local, CPU-only, network-free, and non-empirical. No real dataset, checkpoint, Kaggle job, generation, feature extraction, metric result, or certificate was produced.
