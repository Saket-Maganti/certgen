# CertGen CVPR Baseline Reproduction

Baseline captured before CVPR-layer edits on branch `master`, commit `bff335aa648fd19e2fa7e3cfea293a6ca519a68b`. The worktree was already heavily dirty; all state was preserved.

| Check | Verdict | Result |
|---|---|---|
| Full offline tests | VERIFIED_CURRENT | 212 passed in 9.73s; exit 0 |
| Statistical documented lane | VERIFIED_CURRENT | 22 passed; exit 0 (not the reported 31 count) |
| Artifact-contract documented lane | VERIFIED_CURRENT | 18 passed; exit 0 (not the reported 25 count) |
| Forensic audit | VERIFIED_CURRENT | 8/8; exit 0 |
| Final execution audit | VERIFIED_CURRENT | BLOCKED_MISSING_REFERENCE_SAMPLES; exit 0 |
| V9 notebook static audit | VERIFIED_CURRENT | pass; static only |
| Paper firewall/artifact registry | VERIFIED_CURRENT | pass |
| Compile/import/ruff | VERIFIED_CURRENT | pass |
| Full mypy | VERIFIED_CURRENT_DEBT | 111 errors in 34 files; exit 1 |
| Paper build | VERIFIED_CURRENT | 5-page placeholder PDF built; warnings only |
| Privacy/secrets scan | VERIFIED_CURRENT | no issue; unknown-license template warnings remain |
| git diff --check | VERIFIED_CURRENT | pass |

No command downloaded data/models or generated scientific evidence.
