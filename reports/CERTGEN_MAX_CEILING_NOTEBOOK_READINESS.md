# CertGen Maximum-Ceiling Notebook Readiness

Status: `KAGGLE_RUN_READY_BY_LOCAL_CONTRACT`
Reality boundary: `REAL_KAGGLE_VALIDATION_REQUIRED`

All five canonical notebooks pass static analysis and deterministic regeneration. Their contracts include deterministic input discovery, GPU-count checks, dependency/asset network separation, one worker per GPU, disk and asset preflight, exact resume identity, validated completion markers, atomic shards and final ZIPs, ZIP rebuild/reuse, copy-back instructions, isolated CUDA workers, and explicit failure summaries.

No notebook was claimed as Kaggle-tested. No CUDA, model asset, or real data was used in this audit. Claim allowed: `false`.
