# Kaggle T4x2 Feature Extraction Runbook R0

`NO_REAL_EVIDENCE`

## Purpose

Use Kaggle T4x2 only to extract and cache features from verified samples. CertGen certificates and audits remain CPU-side after the feature caches are copied back.

## Inputs

- sample manifest: `/kaggle/input/certgen/cifar10_r1_samples.jsonl`
- provenance ledger: `/kaggle/input/certgen/cifar10_r1_ledger.csv`
- preprocessing lock: `/kaggle/input/certgen/cifar10_inception_bilinear_299.json`
- extractor: `inception_v3_pool3`, `clip_vit`, or optional `dinov2`
- output directory: `/kaggle/working/features/<extractor>`
- chunk size / batch size: choose conservatively first, for example `64`
- resume flag: use `--resume` for interrupted shard jobs

## Preflight Checks

Before GPU extraction:

1. Provenance ledger passes local CPU validation.
2. License is known and allowed.
3. Sample manifest exists.
4. Image count matches expected count.
5. Hashes or file list are stable.
6. Preprocessing lock exists and is not a template.
7. Output directory is empty, or the run is explicitly resume-safe.
8. No output sets `claim_allowed=true`.

## T4x2 Parallelism Strategy

Do not use distributed training, NCCL, or model-parallel code. Use simple two-process sharding:

- GPU 0 processes shard IDs whose manifest index is even.
- GPU 1 processes shard IDs whose manifest index is odd.

Example:

```bash
mkdir -p /kaggle/working/features/inception

CUDA_VISIBLE_DEVICES=0 python -m certgen.features.extract \
  --input-manifest /kaggle/input/certgen/cifar10_r1_samples.jsonl \
  --provenance-ledger /kaggle/input/certgen/cifar10_r1_ledger.csv \
  --preprocessing-lock /kaggle/input/certgen/cifar10_inception_bilinear_299.json \
  --extractor inception_v3_pool3 \
  --out-dir /kaggle/working/features/inception \
  --device cuda \
  --batch-size 64 \
  --shard-id 0 \
  --num-shards 2 \
  --resume \
  --execute &

CUDA_VISIBLE_DEVICES=1 python -m certgen.features.extract \
  --input-manifest /kaggle/input/certgen/cifar10_r1_samples.jsonl \
  --provenance-ledger /kaggle/input/certgen/cifar10_r1_ledger.csv \
  --preprocessing-lock /kaggle/input/certgen/cifar10_inception_bilinear_299.json \
  --extractor inception_v3_pool3 \
  --out-dir /kaggle/working/features/inception \
  --device cuda \
  --batch-size 64 \
  --shard-id 1 \
  --num-shards 2 \
  --resume \
  --execute &

wait
```

Repeat with `--extractor clip_vit` for CLIP-feature CMMD, and optionally `--extractor dinov2` for descriptive FD/DINO analyses. DINOv2 is not needed for the R0 rigorous certificate path.

## Output Requirements

Feature caches must record:

- feature array;
- feature model name;
- feature model version or hash if available;
- sample IDs;
- preprocessing lock hash;
- source manifest hash;
- provenance ledger hash;
- extraction timestamp if available;
- device info;
- shard ID and number of shards;
- evidence status;
- `claim_allowed=false`.

## Merge Step

After both GPU processes finish:

```bash
python -m certgen.features.merge_shards \
  --shard-dir /kaggle/working/features/inception/shard-000-of-002 \
  --shard-dir /kaggle/working/features/inception/shard-001-of-002 \
  --extractor inception_v3_pool3 \
  --out-npz /kaggle/working/features/merged/reference_inception.npz \
  --out-sidecar /kaggle/working/features/merged/reference_inception.sidecar.json
```

The merge must:

- validate shard completeness;
- detect duplicate sample IDs;
- sort deterministically by sample ID;
- write a merged `.npz`;
- write a JSON sidecar;
- preserve `claim_allowed=false`;
- never overwrite without `--force`.

After copying the merged caches back, run the CPU-side validation commands in `commands/r0_cpu/`.
