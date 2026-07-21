You are working on CertGen in `/Users/saketmaganti/Projects/certGen` after V6.

Global non-negotiables:
- Do not fabricate results.
- Do not create `claim_allowed=true` unless a specific real-evidence gate later permits it; for V7, keep `claim_allowed=false`.
- Do not use smoke/template/synthetic outputs as real evidence.
- Do not run certificates unless real feature caches and metric/sanity gates pass.
- Do not claim rigorous FID certification. FID remains descriptive-only.
- Polynomial KID remains descriptive/non-certified by default unless a separate valid bounded/nonasymptotic justification is implemented and audited.
- Rigorous certificate path remains bounded RBF-MMD / bounded CMMD / valid bounded streams.
- Kaggle T4×2 is for sample generation and feature extraction only. CPU/local is for validation, packaging, metric reproduction, certificates, reports, and audits.
- Every output must clearly label whether it is `NO_REAL_EVIDENCE`, `pilot_only`, `not_paper_evidence`, or `run_log_only`.
- Do not build generic V7 fluff. Build execution leverage: commands, notebooks, validators, packaging, recovery, and run lanes that get the first real pilot unstuck and scalable.

# V7 Prompt 01 — Local Data Onramp for CIFAR-10 Reference

The current blocker is `BLOCKED_MISSING_REFERENCE_SAMPLES`. Build stronger local onramps so the user can unblock without guessing folder format.

Implement:

## 1. Auto-detect CIFAR input root

Create CLI:

```bash
python -m certgen.data.autodetect_cifar10_root
```

It should accept:

- `--search-root`
- `--out-json`
- `--out-report`

It must detect and classify:

- official extracted `cifar-10-batches-py`;
- torchvision-style raw/downloaded structure;
- image-folder tree with class folders;
- flat image directory with manifest;
- unsupported layout.

Do not download data.

## 2. Guided materialization wrapper

Create:

`commands/v7_cpu_execution/01_auto_materialize_cifar_reference.sh`

It should accept one of:

```bash
CIFAR_ROOT=/path/to/root
CIFAR_ARCHIVE_ROOT=/path/to/archive
CIFAR_SEARCH_ROOT=/path/to/search
```

It should:

- detect format;
- call the correct existing materializer;
- write `registry/manifests/cifar10_r1_reference.jsonl`;
- write `data/results/v7_cifar_reference_materialization_summary.json`;
- preserve `claim_allowed=false`;
- fail with exact blocker if no valid source exists.

## 3. Reference preview report

Create:

`docs/V7_CIFAR_REFERENCE_ONRAMP_REPORT.md`

Include:

- detected path;
- detected layout;
- counts;
- resolution;
- split;
- license status;
- next command.

## 4. Tests

Use tiny fake fixtures only. Tests must cover official-batch-like fixture, image-folder fixture, unsupported layout, and no data found.

Do not require internet or real CIFAR-10.
