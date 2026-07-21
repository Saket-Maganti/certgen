# V9 Kaggle Checkpoint Preflight Guide

> **LEGACY_COMPATIBILITY_ONLY — NOT CANONICAL GUIDANCE.** Use `CERTGEN_CVPR_FINAL_EXECUTION_HANDBOOK.md`.

`NO_FAKE_RESULTS`
`NO_REAL_EVIDENCE`
`not paper evidence`
`claim_allowed=false`

Notebook: `notebooks/kaggle/v9_checkpoint_real_load_preflight_t4x2.ipynb`

Run this on Kaggle T4x2 before full 1k generation. It loads each checkpoint and writes 1-4 tiny preflight images per model as `run_log_only` artifacts.

Expected output:

```text
/kaggle/working/certgen_checkpoint_preflight_outputs.zip
```

Copy back locally:

```text
data/kaggle_outputs/certgen_checkpoint_preflight_outputs.zip
```

Import:

```bash
commands/v9_cpu_execution/02_import_checkpoint_preflight_zip.sh
```

Allowed status values:

```text
PREFLIGHT_PASS
PREFLIGHT_BLOCKED_MODEL_LOAD
PREFLIGHT_BLOCKED_SCHEDULER
PREFLIGHT_BLOCKED_CUDA
PREFLIGHT_BLOCKED_DEPENDENCY
```

Do not use preflight images as evidence.
