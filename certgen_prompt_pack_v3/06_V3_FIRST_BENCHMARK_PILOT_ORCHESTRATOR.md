# Prompt 06 — First-Benchmark Pilot Orchestrator

Implement a first-benchmark pilot orchestrator that can run clean-core certificates on validated real feature caches, or dry-run safely when real features are absent.

## Goal

Create a single orchestration command:

```bash
python3 -m certgen.cli.run_first_pilot \
  --pilot-config configs/first_pilot_v3.yaml \
  --out-dir data/results/first_pilot_v3 \
  --report docs/FIRST_PILOT_V3_REPORT.md \
  --json-out data/results/first_pilot_v3/summary.json
```

## Pilot config

Example:

```yaml
pilot_id: first_pilot_v3
benchmark_id: cifar10_generation_candidate
metric_family: clean_core
metrics: [kid, cmmd]
alpha: 0.05
max_samples: 5000
batch_size: 128
seed: 0
mode: dry_run  # dry_run | real_features
reference_cache:
  npz: data/features/reference/inception.npz
  sidecar: data/features/reference/inception.json
comparisons:
  - comparison_id: modelA_vs_modelB
    model_a_cache:
      npz: data/features/model_a/inception.npz
      sidecar: data/features/model_a/inception.json
    model_b_cache:
      npz: data/features/model_b/inception.npz
      sidecar: data/features/model_b/inception.json
    reported_claim:
      metric: fid
      model_a_value: 2.1
      model_b_value: 2.3
      source: "manual ledger row id"
claim_policy:
  allow_claims: false
```

## Behavior

In `dry_run` mode:
- validate config structure;
- check local paths existence if requested;
- produce planned comparison table;
- do not load features;
- produce `evidence_status=dry_run_only`;
- `claim_allowed=false`.

In `real_features` mode:
- validate feature caches;
- validate provenance ledger rows;
- validate preprocessing compatibility;
- compute clean-core contribution streams;
- run clean certificate API;
- produce certificate JSON per comparison and metric;
- render report;
- compute undecided fraction only if all gates pass;
- still keep `claim_allowed=false` unless explicit gate allows non-paper pilot summary.

## Strict no-claim behavior

Even in real mode, V3 should default to:

```yaml
claim_policy:
  allow_claims: false
```

Thus reports may say:

- `pilot_result_computed=true`
- `paper_claim_allowed=false`
- `claim_blockers=["V3 pilot defaults to non-claim mode"]`

## Outputs

- `summary.json`
- per-comparison certificates
- per-metric cards
- `FIRST_PILOT_V3_REPORT.md`
- failure/warning ledger

## Tests

- dry-run config passes;
- missing feature path in dry-run warns/fails depending flag;
- real_features mode with synthetic caches produces certificates;
- claim policy defaults false;
- undecided fraction only computed when valid results exist;
- unsupported FID certificate request fails or demotes to descriptive.

## Verification

Run pytest and a dry-run pilot command using template config.
