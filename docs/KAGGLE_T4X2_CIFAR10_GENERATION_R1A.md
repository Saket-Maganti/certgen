# Kaggle T4x2 CIFAR-10 Generation R1A

`NO_REAL_EVIDENCE`

Claim allowed: `False`

## Purpose

Use Kaggle T4x2 to materialize generated CIFAR-10 samples from the three selected public checkpoint sources. Prefer released samples if they become available and provenance-clean. Use checkpoint generation only with clear checkpoint ID, seed ranges, output hashes, and no claim promotion.

This runbook generates sample-package artifacts only. It does not run feature extraction, metric reproduction, or certificates.

## Checkpoints

| checkpoint_id | adapter | status |
|---|---|---|
| `google/ddpm-cifar10-32` | `DDPMPipeline` | guarded execute supported |
| `FrankCCCCC/ddpm_ema_cifar10` | `DDPMPipeline` | guarded execute supported |
| `FrankCCCCC/cfm-cifar10-32` | `DDPMPipeline` per model card | guarded execute supported; if loader/scheduler fails, stop and record blocked status |

Do not assume success from the model card alone. The first Kaggle run is a small pilot. A failed model-specific load is a blocker, not a partial result.

## Install

```bash
pip install -U diffusers transformers accelerate safetensors torch torchvision
```

## Modes

- small pilot: 1,000 samples per model
- medium: 10,000 samples per model after pilot manifest validation
- full: 50,000 samples per model only after pilot succeeds

All modes use deterministic names, duplicate seed detection, image hashes, checkpoint IDs, and `claim_allowed=false`.

## Small Pilot: 1,000 Samples Per Model

Run one model at a time with two-process seed sharding. This avoids NCCL/distributed training and makes failed checkpoints easy to isolate.

### Google DDPM

```bash
mkdir -p /kaggle/working/samples/google_ddpm /kaggle/working/manifests

CUDA_VISIBLE_DEVICES=0 python -m certgen.generation.generate_cifar10_diffusers \
  --checkpoint-id google/ddpm-cifar10-32 \
  --seed-start 0 \
  --seed-end 500 \
  --num-samples 500 \
  --out-dir /kaggle/working/samples/google_ddpm/gpu0 \
  --manifest-out /kaggle/working/manifests/google_ddpm_gpu0.jsonl \
  --device cuda \
  --batch-size 32 \
  --resume \
  --execute &

CUDA_VISIBLE_DEVICES=1 python -m certgen.generation.generate_cifar10_diffusers \
  --checkpoint-id google/ddpm-cifar10-32 \
  --seed-start 500 \
  --seed-end 1000 \
  --num-samples 500 \
  --out-dir /kaggle/working/samples/google_ddpm/gpu1 \
  --manifest-out /kaggle/working/manifests/google_ddpm_gpu1.jsonl \
  --device cuda \
  --batch-size 32 \
  --resume \
  --execute &

wait
```

### Frank DDPM EMA

```bash
mkdir -p /kaggle/working/samples/frank_ddpm_ema /kaggle/working/manifests

CUDA_VISIBLE_DEVICES=0 python -m certgen.generation.generate_cifar10_diffusers \
  --checkpoint-id FrankCCCCC/ddpm_ema_cifar10 \
  --seed-start 0 \
  --seed-end 500 \
  --num-samples 500 \
  --out-dir /kaggle/working/samples/frank_ddpm_ema/gpu0 \
  --manifest-out /kaggle/working/manifests/frank_ddpm_ema_gpu0.jsonl \
  --device cuda \
  --batch-size 32 \
  --resume \
  --execute &

CUDA_VISIBLE_DEVICES=1 python -m certgen.generation.generate_cifar10_diffusers \
  --checkpoint-id FrankCCCCC/ddpm_ema_cifar10 \
  --seed-start 500 \
  --seed-end 1000 \
  --num-samples 500 \
  --out-dir /kaggle/working/samples/frank_ddpm_ema/gpu1 \
  --manifest-out /kaggle/working/manifests/frank_ddpm_ema_gpu1.jsonl \
  --device cuda \
  --batch-size 32 \
  --resume \
  --execute &

wait
```

### Frank CFM

```bash
mkdir -p /kaggle/working/samples/frank_cfm /kaggle/working/manifests

CUDA_VISIBLE_DEVICES=0 python -m certgen.generation.generate_cifar10_diffusers \
  --checkpoint-id FrankCCCCC/cfm-cifar10-32 \
  --seed-start 0 \
  --seed-end 500 \
  --num-samples 500 \
  --out-dir /kaggle/working/samples/frank_cfm/gpu0 \
  --manifest-out /kaggle/working/manifests/frank_cfm_gpu0.jsonl \
  --device cuda \
  --batch-size 32 \
  --resume \
  --execute &

CUDA_VISIBLE_DEVICES=1 python -m certgen.generation.generate_cifar10_diffusers \
  --checkpoint-id FrankCCCCC/cfm-cifar10-32 \
  --seed-start 500 \
  --seed-end 1000 \
  --num-samples 500 \
  --out-dir /kaggle/working/samples/frank_cfm/gpu1 \
  --manifest-out /kaggle/working/manifests/frank_cfm_gpu1.jsonl \
  --device cuda \
  --batch-size 32 \
  --resume \
  --execute &

wait
```

## Merge and Validate Generated Manifests

```bash
python -m certgen.generation.merge_sample_manifests \
  --manifest /kaggle/working/manifests/google_ddpm_gpu0.jsonl \
  --manifest /kaggle/working/manifests/google_ddpm_gpu1.jsonl \
  --manifest /kaggle/working/manifests/frank_ddpm_ema_gpu0.jsonl \
  --manifest /kaggle/working/manifests/frank_ddpm_ema_gpu1.jsonl \
  --manifest /kaggle/working/manifests/frank_cfm_gpu0.jsonl \
  --manifest /kaggle/working/manifests/frank_cfm_gpu1.jsonl \
  --out-manifest /kaggle/working/manifests/cifar10_r1_generated_pilot_1000.jsonl \
  --out-summary /kaggle/working/manifests/cifar10_r1_generated_pilot_1000_summary.json \
  --check-image-hashes
```

The merge detects duplicate seeds per checkpoint, duplicate paths, and duplicate image hashes when `--check-image-hashes` is set.

## Medium and Full Modes

For 10,000 samples per model, use seed ranges `0-5000` and `5000-10000` per model. For 50,000 samples per model, use seed ranges `0-25000` and `25000-50000` per model. Do not run full mode until the 1,000-sample pilot has produced complete manifests and validated hashes.

## Outputs

Each generated manifest row records:

- `sample_id`
- `checkpoint_id`
- `seed`
- `image_path`
- `image_hash`
- width, height, channels
- `generation_status`
- `evidence_status`
- `claim_allowed=false`

Copy generated samples and merged manifests back to the local workspace before feature extraction. Feature extraction remains a separate Kaggle step after the combined reference/generated sample manifest validates.
