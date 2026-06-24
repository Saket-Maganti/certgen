# V1 Metrics Foundation Report

Implemented:

- `.npz` feature cache save/load helpers.
- Feature manifest creation and shape/hash validation.
- CPU toy MMD, KID, CMMD, FID, and FD-DINOv2 helpers.
- Metric registry with clean-CS support flags.
- Optional feature-extraction stubs for Inception, CLIP, and DINOv2.

Limitations:

- Feature extractors are dry-run placeholders.
- FID and FD-DINOv2 are descriptive-only in V1.
- Toy metric outputs are non-evidence smoke artifacts.
