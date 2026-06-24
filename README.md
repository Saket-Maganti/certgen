# CertGen

CertGen is an anytime-valid, metric-agnostic decision-certificate scaffold for generative-model comparison.

This repository currently contains contracts, smoke/synthetic fixtures, conservative clean-metric certificate scaffolding, real-pilot readiness tools, V4 paper-facing infrastructure, claim gates, and reproducibility docs. It does not contain paper evidence or empirical conclusions.

## Quick Start

```bash
python -m pytest -q
python -m certgen.cli.validate_config --config configs/certgen_v1_smoke.yaml
python -m certgen.cli.make_smoke_artifacts --config configs/certgen_v1_smoke.yaml --out-dir data/smoke/v1 --compute-metrics --make-certificate
python -m certgen.cli.validate_registry --benchmarks registry/candidate_benchmarks_template.csv --pairs registry/candidate_model_pairs_template.csv
python -m certgen.cli.plan_first_pilot --pairs registry/candidate_model_pairs_template.csv --out docs/FIRST_PILOT_PLAN.md
python -m certgen.cli.v1_audit --out docs/V1_FINAL_AUDIT.md --json-out data/results/v1_final_audit.json
```

All V1-generated artifacts are smoke, mock, planned, synthetic, or descriptive-only. They are not paper evidence.

## V3 Status

V3 adds real-pilot readiness infrastructure: provenance ledgers, strict feature-cache validation, dry-run extraction planning, metric reproduction audits, first-pilot orchestration, certificate replay, pilot report cards, V3 registry availability tables, and a final V3 audit.

V3 still produces no paper evidence by default. Reports remain `claim_allowed: false` unless a future explicit claim-eligibility gate passes.

## V4 Status

V4 adds CVPR-facing run infrastructure: V4 state intake, provenance-to-real-run planning, feature notebook generation, preprocessing locks, batch certificates, decidedness/ranking reports, first-real-pilot control, literature claim traces, paper artifact scaffolds, reviewer attacks, reproducibility capsule validation, release safety scanning, and a final V4 audit.

V4 still produces no paper evidence by default. The next required step is one bounded real non-claim pilot, not more infrastructure.

## V5 Status

V5 makes the repository CVPR-ready-except-runs: paper identity, claim contract, related-work board, preregistration lock, result contracts, main paper scaffold, supplement/proof scaffold, release capsule, command bundles, result-injection protocol, reviewer simulator, CVPR readiness scorecard, kill list, stop condition, and final V5 audit.

V5 is not submission-ready. The next step is real execution, not generic V6 infrastructure.
