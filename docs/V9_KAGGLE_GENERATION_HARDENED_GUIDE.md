# V9 Hardened Kaggle Generation Guide

> **LEGACY_COMPATIBILITY_ONLY — NOT CANONICAL GUIDANCE.** Use `CERTGEN_CVPR_FINAL_EXECUTION_HANDBOOK.md`.

`NO_FAKE_RESULTS`
`NO_REAL_EVIDENCE`
`not paper evidence`
`claim_allowed=false`

Notebook: `notebooks/kaggle/v9_cifar10_generation_t4x2_1k_hardened.ipynb`

Run only after checkpoint preflight passes/imports. The notebook uses T4x2 seed sharding, retry logic, per-shard status JSON, resume from completed shards, duplicate checks, and an output ZIP integrity manifest.

Expected output:

```text
/kaggle/working/certgen_cifar10_generation_outputs_v9_1k.zip
```

Copy back:

```text
data/kaggle_outputs/certgen_cifar10_generation_outputs_v9_1k.zip
```

Import:

```bash
commands/v9_cpu_execution/03_import_generation_zip_v9.sh
```

The notebook does not continue to feature extraction.
