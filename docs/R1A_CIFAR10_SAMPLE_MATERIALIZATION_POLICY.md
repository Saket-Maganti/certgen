# R1A CIFAR-10 Sample Materialization Policy

`NO_REAL_EVIDENCE`

Claim allowed: `False`

R1A prepares sample-package artifacts only. It does not run certificates, does not report model wins, and does not promote any output to paper evidence.

## Required Samples Before Feature Extraction

CIFAR-10 reference samples are required before feature extraction. The reference side must have real local image files, stable sample IDs, hashes when feasible, split labels, resolution metadata, source URL, license status, and `claim_allowed=false`.

Generated model samples are also required before feature extraction. Checkpoints alone are not feature-extraction-ready because there are no image files to hash, shard, cache, or replay. Each generated sample must carry the checkpoint ID, seed, path, image hash, dimensions, generation status, evidence status, and `claim_allowed=false`.

## CPU/GPU Boundary

Sample generation is GPU-side. Feature extraction is GPU-side. Kaggle T4x2 may be used for those two tasks only.

CertGen certificates, reports, audits, provenance validation, preprocessing-lock validation, feature-cache validation, metric reproduction, block-size sensitivity, and optional-stopping checks remain CPU-side.

## Evidence Boundary

All R1A outputs are sample-package artifacts, not paper evidence. A generated or reference sample manifest may unblock later feature extraction, but it is not a metric result and cannot support a paper claim by itself.

R1A artifacts must keep:

- `claim_allowed=false`
- `promote_to_paper_evidence=false`
- FID descriptive-only
- polynomial KID descriptive/non-certified by default
- rigorous clean-core path limited to bounded RBF-MMD and bounded CMMD after feature caches and metric reproduction pass

## R1A Blocker Taxonomy

The R1 readiness report distinguishes:

- `BLOCKED_MISSING_REFERENCE_SAMPLES`
- `BLOCKED_GENERATION_NOT_RUN`
- `BLOCKED_GENERATION_ADAPTER_UNSUPPORTED`
- `BLOCKED_FEATURE_EXTRACTION_NOT_RUN`
- `BLOCKED_METRIC_REPRODUCTION`
- `READY_FOR_KAGGLE_FEATURE_EXTRACTION`
- `READY_FOR_CPU_CERTIFICATE_PILOT`
