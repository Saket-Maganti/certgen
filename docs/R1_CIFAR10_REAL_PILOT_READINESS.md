# CERTGEN_R1_CIFAR10_REAL_PILOT Readiness

`NO_REAL_EVIDENCE`

Status: `blocked`
Claim allowed: `False`

## Blockers
- provenance ledger missing: registry/provenance/cifar10_r1_ledger.csv
- manifest: sample manifest missing: registry/manifests/cifar10_r1_samples.jsonl
- features: feature cache missing for reference_inception: reference_inception.npz and/or reference_inception.sidecar.json
- features: feature cache missing for model_a_inception: model_a_inception.npz and/or model_a_inception.sidecar.json
- features: feature cache missing for model_b_inception: model_b_inception.npz and/or model_b_inception.sidecar.json
- features: feature cache missing for reference_clip: reference_clip.npz and/or reference_clip.sidecar.json
- features: feature cache missing for model_a_clip: model_a_clip.npz and/or model_a_clip.sidecar.json
- features: feature cache missing for model_b_clip: model_b_clip.npz and/or model_b_clip.sidecar.json
- metric reproduction audit missing: data/results/cifar10_r1_metric_reproduction.json

## Candidate Pairs
- `cifar10_null_real_split`: null_calibration_pair (candidate_requires_real_manifest)
- `cifar10_obvious_gap_corruption_sanity`: obvious_gap_sanity_pair (candidate_requires_real_reference_manifest)
- `cifar10_medium_gap_public_baseline_pair`: medium_gap_pair (candidate_requires_source_selection)
- `cifar10_close_gap_two_strong_models`: close_gap_pair (candidate_requires_source_selection)
- `cifar10_preprocessing_sensitivity_pair`: preprocessing_sensitivity_pair (candidate_requires_primary_ready_path)

## Exact Next Command

`python3 -m certgen.cli.run_cifar10_real_pilot --provenance-ledger registry/provenance/cifar10_r1_ledger.csv --sample-manifest registry/manifests/cifar10_r1_samples.jsonl --preprocessing-lock configs/preprocessing_locks/cifar10_inception_bilinear_299.json --feature-cache-dir data/features/cifar10_r1 --metric-reproduction-audit data/results/cifar10_r1_metric_reproduction.json --out-json data/results/r1_cifar10_status.json --report docs/R1_CIFAR10_REAL_PILOT_READINESS.md`
