# R0 Command Index

`NO_REAL_EVIDENCE`

## Technical Audit

`python3 -m certgen.cli.r0_technical_audit --out docs/R0_TECHNICAL_CORRECTION_REPORT.md --json-out data/results/r0_technical_correction_audit.json --command-index docs/R0_COMMAND_INDEX.md --r1-status-json data/results/r1_cifar10_status.json --r1-report docs/R1_CIFAR10_REAL_PILOT_READINESS.md`

## CIFAR-10 R1 Readiness

`python3 -m certgen.cli.run_cifar10_real_pilot --provenance-ledger registry/provenance/cifar10_r1_ledger.csv --sample-manifest registry/manifests/cifar10_r1_samples.jsonl --preprocessing-lock configs/preprocessing_locks/cifar10_inception_bilinear_299.json --feature-cache-dir data/features/cifar10_r1 --metric-reproduction-audit data/results/cifar10_r1_metric_reproduction.json --out-json data/results/r1_cifar10_status.json --report docs/R1_CIFAR10_REAL_PILOT_READINESS.md`

## Rigorous Certificate Template

`python3 -m certgen.cli.certify_clean_metric --features-a <model_a_features.npz> --features-b <model_b_features.npz> --features-r <reference_features.npz> --metric mmd_rbf --comparison-id <comparison_id> --alpha 0.05 --budget-units <units> --method betting --block-size <units> --metric-reproduction-audit data/results/cifar10_r1_metric_reproduction.json --out data/results/certificates/<comparison_id>_mmd_rbf.json --evidence-status real_pilot_non_claim`

Polynomial KID, FID, and FD-style metrics are descriptive-only in R0.
