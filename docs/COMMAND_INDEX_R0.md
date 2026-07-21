# R0 Command Index

`NO_REAL_EVIDENCE`

## Local CPU Validation

```bash
commands/r0_cpu/07_run_r0_audit_cpu.sh
```

Equivalent direct command:

```bash
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES="" python3 -m certgen.audit.r0_cpu_gpu_audit --out docs/R0_CPU_GPU_AUDIT.md --json-out data/results/r0_cpu_gpu_audit.json
```

## External Test Verification

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q
```

## Kaggle T4x2 Feature Extraction

```bash
CUDA_VISIBLE_DEVICES=0 python -m certgen.features.extract --input-manifest /kaggle/input/certgen/cifar10_r1_samples.jsonl --provenance-ledger /kaggle/input/certgen/cifar10_r1_ledger.csv --preprocessing-lock /kaggle/input/certgen/cifar10_inception_bilinear_299.json --extractor inception_v3_pool3 --out-dir /kaggle/working/features/inception --device cuda --batch-size 64 --shard-id 0 --num-shards 2 --resume --execute &
CUDA_VISIBLE_DEVICES=1 python -m certgen.features.extract --input-manifest /kaggle/input/certgen/cifar10_r1_samples.jsonl --provenance-ledger /kaggle/input/certgen/cifar10_r1_ledger.csv --preprocessing-lock /kaggle/input/certgen/cifar10_inception_bilinear_299.json --extractor inception_v3_pool3 --out-dir /kaggle/working/features/inception --device cuda --batch-size 64 --shard-id 1 --num-shards 2 --resume --execute &
wait
```

## Local CPU Certificate Pilot After Cached Features Exist

```bash
commands/r0_cpu/01_validate_provenance.sh
commands/r0_cpu/02_validate_feature_caches.sh
commands/r0_cpu/03_reproduce_metric_from_features.sh
commands/r0_cpu/04_run_clean_core_certificates_cpu.sh
commands/r0_cpu/06_generate_pilot_report_cpu.sh
```
