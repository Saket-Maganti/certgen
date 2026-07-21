# 05 — Kaggle T4x2 Feature Extraction: Inception + CLIP

Implement/execute `CERTGEN_R1C_KAGGLE_FEATURE_EXTRACTION_INCEPTION_CLIP`.

Goal:

> Extract cached Inception and CLIP features from the validated CIFAR-10 R1 feature-extraction package using Kaggle T4x2.

This is GPU-side. It must only run after the feature-extraction sample package validates.

## Prerequisite

`docs/R1_CIFAR10_REAL_PILOT_READINESS.md` must report:

`READY_FOR_KAGGLE_FEATURE_EXTRACTION`

Do not run this if readiness is blocked.

## Inputs

- sample manifest: `registry/manifests/cifar10_r1_feature_extraction_samples.jsonl`
- provenance ledger: `registry/provenance/cifar10_r1_ledger.csv`
- preprocessing locks:
  - Inception lock
  - CLIP lock
- output root:
  - `/kaggle/working/features/cifar10_r1/`

## T4x2 strategy

Simple two-shard extraction:

- GPU 0: shard 0 of 2
- GPU 1: shard 1 of 2

No distributed training.

## Command file

Create/update:

`commands/r1c_kaggle_feature_extraction/00_extract_inception_clip_t4x2.sh`

It should include a two-GPU sharded extraction for `inception_v3_pool3` and `clip_vit`.

Adjust preprocessing lock filenames to the repo's actual lock names. Do not invent readiness if locks are missing.

## Merge features

After extraction, merge shards with:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m certgen.features.merge_shards \
  --shard-dir <SHARD_0> \
  --shard-dir <SHARD_1> \
  --extractor inception_v3_pool3 \
  --out-npz /kaggle/working/features/cifar10_r1/merged/cifar10_r1_inception.npz \
  --out-sidecar /kaggle/working/features/cifar10_r1/merged/cifar10_r1_inception.sidecar.json
```

Repeat for CLIP.

## Runtime planning estimates

For 1k/model + reference test set:

- Inception: ~5–25 min
- CLIP: ~10–40 min

For 50k/model later:

- Inception: ~10–40 min per 50k CIFAR images
- CLIP: ~20–90 min per 50k CIFAR images

Planning estimates only until measured.

## Copy back

Copy merged feature caches + sidecars back to:

- `data/features/cifar10_r1/`

## No claims

Feature caches are not paper evidence until local validation and metric reproduction pass.
