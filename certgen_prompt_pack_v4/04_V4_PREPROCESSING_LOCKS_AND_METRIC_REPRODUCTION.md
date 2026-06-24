# 04 — V4 Preprocessing Locks and Metric Reproduction

Upgrade preprocessing and metric reproduction into a gate strong enough for CVPR review.

## Goal

Generative metrics are sensitive to resize, interpolation, crop, feature extractor, dtype, and sample count. V4 should introduce preprocessing lockfiles and a metric reproduction gate before any comparison can become a real pilot candidate.

## Implement

Create or update:

- `certgen/preprocess/locks.py`
- `certgen/audit/preprocessing_lock_audit.py`
- `certgen/audit/metric_reproduction.py`
- `certgen/cli/lock_preprocessing.py`
- `certgen/cli/audit_metric_reproduction.py`
- `configs/preprocessing_locks/*.json`
- `docs/PREPROCESSING_LOCKS_V4.md`
- tests.

## Preprocessing lock fields

A lock should include:

- `lock_id`
- `image_size`
- `resize_policy`
- `interpolation`
- `center_crop`
- `normalization`
- `color_mode`
- `feature_extractor`
- `feature_extractor_version`
- `batch_size`
- `dtype`
- `sample_order_policy`
- `reference_set_policy`
- `hash`

## Metric reproduction gate

For each reported comparison, before CertGen audit:

1. Recompute or validate the reported metric point estimate.
2. Compare against reported value within a tolerance policy.
3. If mismatch is large, mark comparison `reproduction_failed` or `preprocessing_unknown`, not evidence.
4. Save reproduction report.

## Tolerance policy

Define a configurable policy:

- exact match not expected;
- tolerance depends on metric and sample size;
- unknown preprocessing gives warning/blocker;
- if sample count differs from reported sample size, block claim.

## CLI examples

```bash
python3 -m certgen.cli.lock_preprocessing \
  --name cifar10_inception_bilinear_299 \
  --out configs/preprocessing_locks/cifar10_inception_bilinear_299.json

python3 -m certgen.cli.audit_metric_reproduction \
  --comparison-plan data/results/v4/real_run_plan.json \
  --features-a data/features/model_a_inception.npz \
  --features-b data/features/model_b_inception.npz \
  --features-ref data/features/cifar10_ref_inception.npz \
  --out data/results/v4/metric_reproduction.json \
  --report docs/V4_METRIC_REPRODUCTION.md
```

## Acceptance criteria

- Lock validator catches missing/unknown policies.
- Metric reproduction report is generated from synthetic features in tests.
- Real comparison is blocked if preprocessing is unknown and strict mode is on.
- Reports clearly distinguish reproduced, approximated, descriptive, and failed.
