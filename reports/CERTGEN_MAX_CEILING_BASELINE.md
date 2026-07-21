# CertGen Maximum-Ceiling Replaced Baseline

The clean fixed archive was tested before maximum-ceiling source edits.

- Default non-recursive lane: `266 passed, 4 deselected` in 8.08 seconds.
- Explicit integration-audit lane: `4 passed, 266 deselected` in 33.17 seconds.
- Focused statistical lane: `19 passed`.
- Artifact-contract lane: `25 passed`.
- Runtime-hardening / real-closure / final-run-ready / post-cache lanes: `10 / 9 / 8 / 3 passed`.
- CVPR / forensic / V9 audits: `8/8`, `8/8`, and pass.
- Final pre-run audit: `24/24`, `CVPR_100_PERCENT_PRE_RUN_READY`.
- Notebook static analysis and deterministic regeneration: `5/5` pass and byte-identical across two regenerations.
- Privacy scan, release scan, paper firewall, Ruff, critical mypy, paper build, and `git diff --check`: pass.
- Critical mypy: no issues in 41 source files.
- Full mypy: unchanged historical debt of `111 errors in 34 files` across 295 source files. Mypy 2.1's incremental cache first raised an internal error; `--no-incremental` produced the stable comparison.
- Paper compilation: 5 pages; only nonfatal overfull-box warnings.

No internet, CUDA, CIFAR data, model checkpoint, generation, feature extraction, or claim-bearing run was used.
