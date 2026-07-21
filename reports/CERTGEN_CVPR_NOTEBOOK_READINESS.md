# CertGen CVPR Notebook Readiness

| Notebook | Static validation | Fixture validation | T4x2 | Resume | Unverified risk |
|---|---|---|---|---|---|
| checkpoint preflight | pass | structural only | two process workers | hash-bound per model | packages, network, auth, real model load |
| CIFAR 1k generation | pass | structural only | deterministic shard allocation | manifest/hash validation | adapters, throughput, disk, scheduler behavior |
| generic generation | pass | structural only | config-driven | per-shard | every future model needs preflight |
| CIFAR 1k features | pass | structural only | two process workers | cache finite/hash validation | runtime adapter and DINO variant |
| generic features | pass | structural only | config-driven | per-shard | memory, exact preprocessing, cache merge |

Static validation is not successful Kaggle execution. Every notebook remains `real_run_required`, `run_log_only`, and `claim_allowed=false`.
