# 03 — Kaggle T4x2 Generation: 1,000 Samples Per Model

Implement/execute `CERTGEN_R1B_KAGGLE_GENERATION_1K_PER_MODEL`.

Goal:

> Generate a small 1,000-sample pilot for each selected CIFAR-10 checkpoint using Kaggle T4x2, then copy back samples and manifests for CPU validation.

This is a GPU step. Do not run locally unless explicitly using CPU dry-run.

## Checkpoints

Generate 1,000 samples each:

- `google/ddpm-cifar10-32`
- `FrankCCCCC/ddpm_ema_cifar10`
- `FrankCCCCC/cfm-cifar10-32`

## T4x2 strategy

No NCCL. No distributed training. Use simple two-process seed sharding:

- GPU 0: seeds 0–499
- GPU 1: seeds 500–999

## Command file

Ensure this file exists and is executable:

`commands/r1b_kaggle_generation/00_generate_1000_per_model_t4x2.sh`

It should contain/log the compact form:

```bash
set -euo pipefail
mkdir -p /kaggle/working/samples /kaggle/working/manifests /kaggle/working/logs

for spec in "google/ddpm-cifar10-32 google_ddpm" "FrankCCCCC/ddpm_ema_cifar10 frank_ddpm_ema" "FrankCCCCC/cfm-cifar10-32 frank_cfm"; do
  set -- $spec
  CHECKPOINT_ID="$1"
  SHORT_ID="$2"

  CUDA_VISIBLE_DEVICES=0 python -m certgen.generation.generate_cifar10_diffusers \
    --checkpoint-id "$CHECKPOINT_ID" \
    --seed-start 0 \
    --seed-end 500 \
    --num-samples 500 \
    --out-dir "/kaggle/working/samples/$SHORT_ID/gpu0" \
    --manifest-out "/kaggle/working/manifests/${SHORT_ID}_gpu0.jsonl" \
    --device cuda \
    --batch-size 32 \
    --resume \
    --execute > "/kaggle/working/logs/${SHORT_ID}_gpu0.log" 2>&1 &

  CUDA_VISIBLE_DEVICES=1 python -m certgen.generation.generate_cifar10_diffusers \
    --checkpoint-id "$CHECKPOINT_ID" \
    --seed-start 500 \
    --seed-end 1000 \
    --num-samples 500 \
    --out-dir "/kaggle/working/samples/$SHORT_ID/gpu1" \
    --manifest-out "/kaggle/working/manifests/${SHORT_ID}_gpu1.jsonl" \
    --device cuda \
    --batch-size 32 \
    --resume \
    --execute > "/kaggle/working/logs/${SHORT_ID}_gpu1.log" 2>&1 &

  wait
done
```

## After generation

Copy back:

- `/kaggle/working/samples/`
- `/kaggle/working/manifests/`
- `/kaggle/working/logs/`

Recommended local destination:

- `data/sources/cifar10_r1/generated_pilot_1000/`
- `registry/manifests/generated_raw/r1b/`
- `logs/kaggle/r1b_generation_1000/`

## Runtime estimates

Planning estimates only:

- Google DDPM 1k: ~10–45 min
- Frank DDPM EMA 1k: ~10–60 min
- Frank CFM 1k: ~5–45 min

## Failure policy

If any checkpoint fails to load or generate:

- stop;
- record exact error;
- mark that source `BLOCKED_GENERATION_ADAPTER_UNSUPPORTED` or `BLOCKED_GENERATION_FAILED`;
- do not proceed to feature extraction for that model;
- do not fake replacement samples.
