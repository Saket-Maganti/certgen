# R0 Runtime Estimates: CPU and Kaggle T4x2

`NO_REAL_EVIDENCE`

These are planning estimates, not empirical project results.

Actual runtime depends on file count, disk IO, batch size, image resolution, model architecture, dataloader speed, preprocessing, Kaggle session behavior, and whether samples are already released.

## CPU Local Estimates

Assume a Mac/M4-class CPU or similar local machine, using cached feature arrays.

| Task | Planning estimate | Notes |
|---|---:|---|
| Provenance ledger validation | seconds to minutes | Depends on row count and local path checks. |
| Sample manifest validation | seconds to minutes | Hash checks can make this slower for large manifests. |
| Preprocessing lock validation | seconds | Pure JSON/config validation. |
| Feature-cache validation | seconds to minutes | Depends on feature file sizes and hash policy. |
| Metric reproduction from cached features | seconds to minutes | No image model loading; uses cached arrays. |
| RBF-MMD / CMMD certificates for 5 pairs | seconds to minutes per pair | Depends on sample count, block size, and feature dimension. |
| Optional-stopping lab | minutes | Depends on simulation count and budget. |
| Block-size sensitivity | seconds to minutes | Depends on number of block sizes and cached feature size. |
| Report generation | seconds | Pure local rendering. |
| R0 audit | seconds to minutes | Includes filesystem scans and readiness checks. |

CPU certificate/report runs from cached features should usually be seconds to minutes, not GPU jobs.

## Kaggle T4x2 Estimates

Use Kaggle T4x2 only for feature extraction or optional sample generation.

| Task | Planning estimate | Assumptions |
|---|---:|---|
| Inception features, 50k CIFAR-sized images | ~10-40 min | T4x2, simple two-shard extraction, adequate dataloader throughput. |
| CLIP features, 50k CIFAR-sized images | ~20-90 min | Depends heavily on CLIP variant and resize policy. |
| DINOv2 features, 50k CIFAR-sized images | ~30-120 min | Depends on DINOv2 variant and image resolution. |
| CIFAR sample generation from lightweight generator | ~1-6 hr per 50k samples | Only if released samples are unavailable and generator provenance is clear. |
| CIFAR diffusion-style generation | ~6-24+ hr per 50k samples | Highly variable; may exceed practical Kaggle limits. |
| Shard merge and validation | minutes to tens of minutes | Depends on output size and Kaggle disk IO. |

After Kaggle produces cached artifacts, copy them back and run CertGen validation, reproduction, certificates, reports, and audits on CPU.
