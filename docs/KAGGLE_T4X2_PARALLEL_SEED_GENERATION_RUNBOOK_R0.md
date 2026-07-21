# Kaggle T4x2 Parallel Seed Generation Runbook R0

`NO_REAL_EVIDENCE`

Prefer released samples. Generate samples only when license, checkpoint, config, and seed provenance are clear.

Sample generation is optional and should be used only when released samples are unavailable. Generated samples are not evidence until provenance, manifest, feature-cache, metric reproduction, and CPU-side certificate gates pass.

## Inputs

- open checkpoint path;
- model config path;
- dataset or conditioning spec, for example `cifar10`;
- seed range;
- per-GPU output directories;
- manifest output paths;
- resume flag.

## Parallel Seed Pattern

Use independent GPU processes with disjoint seed ranges. Do not use distributed training or NCCL.

```bash
# GPU 0
CUDA_VISIBLE_DEVICES=0 python -m certgen.generation.generate_samples \
  --checkpoint <CHECKPOINT> \
  --config <CONFIG> \
  --dataset cifar10 \
  --seed-start 0 \
  --seed-end 24999 \
  --out-dir /kaggle/working/samples/gpu0 \
  --manifest-out /kaggle/working/manifests/gpu0_samples.jsonl \
  --resume &

# GPU 1
CUDA_VISIBLE_DEVICES=1 python -m certgen.generation.generate_samples \
  --checkpoint <CHECKPOINT> \
  --config <CONFIG> \
  --dataset cifar10 \
  --seed-start 25000 \
  --seed-end 49999 \
  --out-dir /kaggle/working/samples/gpu1 \
  --manifest-out /kaggle/working/manifests/gpu1_samples.jsonl \
  --resume &

wait
```

The current placeholder command exits with:

```text
Sample generation is not implemented. Use released samples or implement model-specific generator with provenance first.
```

That is intentional. Do not fake model-specific generation.

## Required Generator Behavior When Implemented

A model-specific generator must support:

- parallel seed ranges;
- resume without duplicating completed seeds;
- deterministic file names derived from model ID and seed;
- per-GPU output directories;
- duplicate detection;
- failed seed retry;
- output manifest generation;
- checkpoint hash, config hash, seed range, prompt/conditioning metadata, device info, and generation timestamp;
- `claim_allowed=false`.

## Post-Generation CPU Steps

After sample generation:

1. Merge manifests deterministically.
2. Detect duplicate seeds and duplicate output hashes.
3. Validate license and checkpoint provenance.
4. Run Kaggle T4x2 feature extraction on generated samples if needed.
5. Copy samples/features back.
6. Run CPU-side CertGen validation, metric reproduction, certificates, reports, and audits.

No generated sample may be promoted to paper evidence in R0.
