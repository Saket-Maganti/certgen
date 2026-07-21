# CertGen CVPR Repository Safety Inventory

The pre-edit baseline was captured on branch `master` at commit
`bff335aa648fd19e2fa7e3cfea293a6ca519a68b`. The checkout was already heavily
dirty. No pre-existing modification, deletion, untracked artifact, cache, or
large file was removed, restored, staged, committed, or overwritten by this
pass.

## Current post-build inventory

Captured on 2026-07-13 after the pre-execution build:

| Item | Count or value |
|---|---:|
| Staged paths | 0 |
| Modified status entries | 87 |
| Added status entries | 0 |
| Deleted status entries | 83 |
| Collapsed untracked status entries | 240 |
| Individual untracked files (`git status -uall`) | 48,322 |
| Individual ignored files (`git status --ignored -uall`) | 449 |
| Cache directories found | 38 |

The very large individual untracked-file count includes pre-existing dataset
material and is not a count of files created by this build.

## ADE20K and files larger than 10 MiB

- ADE20K is irrelevant to the active CertGen CVPR pipeline and is intentionally removed from the canonical reproducibility archive and all active execution paths. The two pre-existing untracked local trees, `ade20k_root/` and `ade20kdataset/`, remain user-owned state and were not destructively deleted by this pass; they are explicitly excluded from export.
- `ade20kdataset/ade20k.zip`: approximately 1.1 GiB; local-only, excluded from export.
- `.mypy_cache/3.11/cache.11.db`: approximately 11 MiB; tool cache, preserved.

## Cache families observed

The checkout contains `.mypy_cache`, `.pytest_cache`, `.ruff_cache`, and Python
`__pycache__` directories across the package and test tree. They were treated
as disposable but user-owned state and were not cleaned. The verification
commands avoid presenting any cache content as experimental evidence.

## Safety boundary

No data/model download, real model execution, Kaggle run, real feature
extraction, empirical certificate, result figure, or paper-claim promotion was
performed. All new CVPR artifacts remain `claim_allowed=false`. The clean archive contains no ADE20K root/data.
