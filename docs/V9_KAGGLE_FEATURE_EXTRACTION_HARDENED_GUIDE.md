# V9 Hardened Kaggle Feature Extraction Guide

> **LEGACY_COMPATIBILITY_ONLY — NOT CANONICAL GUIDANCE.** Use `CERTGEN_CVPR_FINAL_EXECUTION_HANDBOOK.md`.

`NO_FAKE_RESULTS`
`NO_REAL_EVIDENCE`
`not paper evidence`
`claim_allowed=false`

Notebook: `notebooks/kaggle/v9_cifar10_feature_extraction_t4x2_1k_hardened.ipynb`

Run only after generation outputs are imported and the feature input ZIP is ready. The notebook validates roles, preprocessing lock hash, runs Inception/CLIP two-shard extraction, merges/splits caches, validates sidecars, and writes an output ZIP integrity manifest.

Expected output:

```text
/kaggle/working/certgen_cifar10_feature_outputs_v9_1k.zip
```

Copy back:

```text
data/kaggle_outputs/certgen_cifar10_feature_outputs_v9_1k.zip
```

Import:

```bash
commands/v9_cpu_execution/04_import_feature_zip_v9.sh
```

The notebook does not run metric reproduction or certificates.
