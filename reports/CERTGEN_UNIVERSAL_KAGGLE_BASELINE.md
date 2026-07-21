# CertGen universal Kaggle baseline

- Captured UTC: `2026-07-21T18:19:33Z`
- Branch: `main`
- HEAD: `295c8c88681bb30da93036fd3769776631836b36`
- Worktree: clean (`git status --short` produced no rows)
- Remote: `origin` is the expected `Saket-Maganti/certgen` GitHub repository
- Safety mode: local CPU only; no Kaggle execution, CUDA initialization, checkpoint download, or empirical artifact creation
- Evidence boundary: `claim_allowed=false`

The reproduced command results are recorded in the universal Kaggle command ledgers and summarized here after the baseline lane completes.

## Reproduced baseline

- Default pytest: `291 passed, 4 deselected`.
- Explicit integration audits: `4 passed, 291 deselected`.
- Compile/import smoke: passed.
- Initial hard-coded-path and dependency review found the expected portability gaps: shallow filename-based input discovery, frozen Kaggle mount paths, no diagnostic lock profile, and an active `timm/open-clip` mismatch.

## Final comparison

- Default pytest: `299 passed, 4 deselected` in one process.
- Explicit integration audits: `4 passed, 299 deselected`.
- Focused universal discovery/dependency tests: `8 passed`; combined focused closure/safety lane: `48 passed`.
- Four-account matrix: `36/36` rows passed, with nine lanes per account and an independent 27-stage builder-faithful rehearsal in every account layout.
- Ruff: passed.
- Changed-code mypy: passed for 25 source files.
- Full-tree historical mypy debt improved from `111 errors in 34 files` to `99 errors in 33 files`; no changed-code error remains.
- Fresh-extraction release: `ARCHIVE_VERIFIED`, including `12` portable tests, notebook static validation, import smoke, and the builder-faithful synthetic runtime.
- Final pre-run, maximum-ceiling, CPU-execution, Kaggle-launch, and universal-Kaggle audits: passed.

The ledger contains resolved red runs from implementation iterations (including the intentionally wrong integration marker and an unfrozen provenance template), followed by successful canonical reruns. Expected-boundary rows are limited to historical mypy debt and the genuine external Kaggle diagnostic boundary. No real Kaggle/CUDA run or empirical result was claimed; `claim_allowed=false`.
