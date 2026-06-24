# Reproducibility Capsule V3

`NO_REAL_EVIDENCE`

Environment:

- Python 3.10+.
- Required lightweight packages: numpy, scipy, PyYAML, pytest for tests.
- Optional heavy packages: torch, torchvision, transformers, timm.
- No paid dependencies, paid APIs, paid cloud, or mandatory GPU.

Expected layout:

- `registry/provenance/`
- `registry/v3/`
- `data/features/`
- `data/results/`
- `docs/`

Execution order is listed in `docs/V3_RUNBOOK.md`. Smoke fixtures remain synthetic. A first real pilot requires user-supplied or verified public/free feature caches.
