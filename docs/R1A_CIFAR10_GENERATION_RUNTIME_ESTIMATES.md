# R1A CIFAR-10 Generation Runtime Estimates

`NO_REAL_EVIDENCE`

These are planning estimates only, not empirical project results.

Claim allowed: `False`

## Assumptions

- Kaggle T4x2 with two independent processes.
- CIFAR-10 32x32 RGB image output.
- Batch size is tuned after a small pilot.
- Disk IO, model download time, scheduler settings, and Kaggle load can dominate short runs.
- Failed checkpoint loading is a blocker, not a measured result.

## Planning Table

| model source | 1,000 samples | 10,000 samples | 50,000 samples | notes |
|---|---:|---:|---:|---|
| `google/ddpm-cifar10-32` | ~10-45 min | ~1-6 hr | ~6-24+ hr | DDPM sampling may be slower depending on scheduler/steps |
| `FrankCCCCC/ddpm_ema_cifar10` | ~10-60 min | ~1-8 hr | ~6-24+ hr | Scheduler and DDIM settings need real-run confirmation |
| `FrankCCCCC/cfm-cifar10-32` | ~5-45 min | ~0.5-6 hr | ~3-18+ hr | Flow-matching path may be faster, but loader/scheduler behavior must be validated |

## Interpretation

Use the 1,000-sample pilot first. Promote to 10,000 only after all three model manifests validate with no duplicate seeds, duplicate paths, or missing hashes. Promote to 50,000 only after pilot and medium runs have clean manifests and reproducible command logs.

These estimates do not include feature extraction. Feature extraction remains the later Kaggle step after local sample-package validation.
