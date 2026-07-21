# R0 CPU/GPU Execution Policy

`NO_REAL_EVIDENCE`

CertGen certificates and audits are CPU-side. Kaggle GPU is only for producing cached feature/sample artifacts.

## CPU-Default Tasks

The following CertGen tasks must run locally on CPU by default:

- registry and provenance validation;
- sample manifest validation;
- preprocessing lock validation;
- feature-cache validation;
- metric reproduction from cached features;
- bounded RBF-MMD and bounded CMMD/CLIP-feature MMD certificate runs;
- betting confidence sequences and bounded-stream CS checks;
- optional-stopping lab runs;
- block-size sensitivity;
- e-value and e-BH design scaffolding already present in the repo;
- certificate replay;
- report generation;
- R0, V5, and later audit commands.

CPU commands should set:

```bash
PYTHONDONTWRITEBYTECODE=1
CUDA_VISIBLE_DEVICES=""
```

This prevents accidental CUDA dependence in statistical, certificate, report, and audit code.

## GPU-Allowed Tasks

GPU use is allowed only to produce artifacts consumed later by CPU-side CertGen:

- Inception feature extraction from verified samples;
- CLIP feature extraction from verified samples;
- DINOv2 feature extraction if enabled;
- optional sample generation from open checkpoints when released samples are unavailable and provenance is clear.

GPU outputs are still not evidence by themselves. They must be copied back, validated, reproduced against one reported point estimate when applicable, and then consumed by CPU-side certificate code.

## No Claim Promotion

All R0 outputs default to `claim_allowed=false`. Feature extraction and sample generation outputs are `real_features_unvalidated`, `planned_only`, or similarly blocked until validation gates pass. FID and FD-style metrics remain descriptive-only. Polynomial KID remains descriptive/non-certified by default.
