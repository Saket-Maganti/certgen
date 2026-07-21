# 13 — Changelog and Expected Final State

## Pack purpose

This mega prompt pack converts CertGen from `CVPR-ready-except-runs` into an execution-first path.

## Expected final states

### Best R1 state

- CIFAR reference materialized.
- 1k/model generated samples materialized.
- manifests merged and validated.
- feature-extraction package ready.
- Kaggle feature extraction command ready or completed.
- local feature caches validated.
- metric reproduction/sanity gates passed.
- CPU certificate pilot run.
- pilot-only undecided fraction computed.
- no `claim_allowed=true` unless explicitly allowed by final evidence contract.

### Acceptable blocked state

- precise blocker reported:
  - missing CIFAR reference;
  - generation failed for specific checkpoint;
  - feature extraction failed;
  - metric reproduction mismatch;
  - certificate sanity failed.

### Bad state

- more generic infrastructure added without executing.
- smoke data used as evidence.
- FID certificate falsely claimed.
- polynomial KID certified despite unbounded kernel.
- `claim_allowed=true` appears before gates pass.

## Core success criterion

The project must move toward the first real number:

> first-benchmark pilot-only undecided fraction.

If this number still does not exist after real sources are available, the project has not advanced scientifically.
