# CertGen Real-Execution Closure Notebook Readiness

All five canonical CVPR notebooks regenerate deterministically and pass the static analyzer. The Phase‑1 diagnostic, preflight, generation, and feature notebooks also match deterministic source; the preflight notebook was refreshed after the live reference action changed.

| Notebook lane | Local status | Real Kaggle status |
|---|---|---|
| checkpoint + extractor preflight T4×2 | static and builder-faithful contract pass | not run |
| CIFAR-10 generation T4×2 1k | static and synthetic contract pass | not run |
| generic generation T4×2 | static and synthetic contract pass | not run |
| feature extraction T4×2 1k | static and synthetic contract pass | not run |
| generic feature extraction T4×2 | static and synthetic contract pass | not run |
| Phase‑1 launch bundle | deterministic; launch audit 11/11 | not uploaded/run |

The notebooks declare split network policy, isolated workers, deterministic per-GPU queues, strict markers, shared output schema, idempotent final-ZIP recovery, copy-back validation, and `claim_allowed=false`. Allowed description: `run-ready by local contract; real Kaggle execution required`.
