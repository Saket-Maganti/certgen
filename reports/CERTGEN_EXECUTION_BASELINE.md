# CertGen execution baseline

Baseline captured at `2026-07-21T09:05:30Z` before this pass.

- Initial branch: `master`; initial HEAD: `bff335aa648fd19e2fa7e3cfea293a6ca519a68b`.
- The worktree contained extensive pre-existing user changes; none were reset, cleaned, or discarded.
- The restored root CIFAR archive was preserved while a validated copy was placed at the canonical ignored path.
- Historical quality claims were not trusted. The live final runs are `290 passed, 4 deselected`, plus `4` explicit integration audits.
- Whole-repository mypy debt remains exactly `111 errors in 34 files`; changed execution code is clean.
- Local execution was forced CPU-only with `CUDA_VISIBLE_DEVICES=""` and `CERTGEN_CPU_ONLY=1`.

This baseline is engineering evidence only. `claim_allowed=false`.
