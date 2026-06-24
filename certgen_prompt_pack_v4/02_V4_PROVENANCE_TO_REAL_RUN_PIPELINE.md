# 02 — V4 Provenance-to-Real-Run Pipeline

Build the bridge from a released-sample/provenance row to a validated real-run plan.

## Goal

V3 added a provenance ledger validator. V4 should make provenance operational: a real comparison cannot enter a pilot unless all required provenance, license, sample availability, preprocessing, reference set, and metric-reproduction fields are present.

## Implement

Create or update:

- `certgen/provenance/ledger.py`
- `certgen/provenance/real_run_plan.py`
- `certgen/cli/build_real_run_plan.py`
- `registry/released_sample_ledger_template.csv`
- `registry/real_run_plan_template.json`
- `docs/REAL_RUN_PROVENANCE_PIPELINE_V4.md`
- tests.

## Required ledger fields

At minimum:

- `comparison_id`
- `benchmark_id`
- `dataset_name`
- `dataset_split`
- `reference_set_source`
- `model_a_name`
- `model_b_name`
- `model_a_sample_source`
- `model_b_sample_source`
- `sample_source_type` (`released_samples`, `checkpoint_generated_later`, `precomputed_features`)
- `sample_license_status`
- `sample_count_available_a`
- `sample_count_available_b`
- `reported_metric_name`
- `reported_metric_value_a`
- `reported_metric_value_b`
- `reported_sample_size`
- `reported_preprocessing`
- `paper_or_source_citation`
- `download_required` (`yes/no/manual`)
- `external_data_required` (`yes/no`)
- `provenance_status` (`template`, `candidate`, `verified`, `blocked`)
- `claim_allowed` default `false`

## Real-run plan gate

A real-run plan may be emitted only if:

- provenance is `verified`,
- license/sample status is acceptable,
- sample counts meet the requested budget,
- preprocessing policy is locked or explicitly marked unknown,
- reference set source exists or is manually supplied,
- metric is supported by the current clean-core certificate or descriptive policy,
- no row has `claim_allowed=true` before results.

If any condition fails, emit a blocked plan with reasons.

## CLI behavior

Example:

```bash
python3 -m certgen.cli.build_real_run_plan \
  --ledger registry/released_sample_ledger.csv \
  --comparison-id cifar10_modelA_vs_modelB \
  --out data/results/v4/real_run_plan.json \
  --report docs/V4_REAL_RUN_PLAN.md
```

The CLI must not download anything. It only validates metadata and emits a plan.

## Outputs

Real-run plan JSON should include:

- run id,
- comparison id,
- benchmark,
- metric list,
- sample budgets,
- preprocessing lock id,
- feature cache targets,
- evidence status `planned_only` or `real_verified_nonclaim`,
- blockers,
- warnings,
- next commands.

## Acceptance criteria

- Passing ledger row emits a non-claim real-run plan.
- Incomplete row emits blocked plan.
- Tests cover pass, missing license, insufficient sample count, unsupported metric, unknown preprocessing.
- No real claim is possible from this step alone.
