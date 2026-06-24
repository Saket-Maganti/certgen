# 05 — V5 Result Contracts, Tables, and Figure Manifests

## Goal

Define every paper table/figure before real runs, with strict schemas and no-result placeholders.

## Add Files

Create:

- `data/contracts/result_contracts_v5.json`
- `docs/paper/TABLE_MANIFEST_V5.md`
- `docs/paper/FIGURE_MANIFEST_V5.md`
- `certgen/reporting/result_contracts.py`
- `certgen/audit/result_contract_audit.py`
- `tests/test_v5_result_contracts.py`

## Required Main Paper Tables

### Table 1 — Audit Summary

Columns:

- benchmark
- metric
- number_of_model_pairs
- decided_A_better
- decided_B_better
- not_decided_at_budget
- invalid_or_rejected
- undecided_fraction
- claim_status

All values must be placeholder until real run.

### Table 2 — Samples-to-Decision

Columns:

- benchmark
- model_A
- model_B
- metric
- reported_sample_size
- budget
- samples_to_decision
- verdict
- alpha_policy
- preprocessing_lock_id

### Table 3 — Metric Agreement / Disagreement

Columns:

- benchmark
- model_pair
- FID_direction_descriptive
- KID_certificate_verdict
- CMMD_certificate_verdict
- DINO_or_other_verdict
- disagreement_flag
- claim_status

### Table 4 — Ranking Stability

Columns:

- benchmark
- metric
- naive_rank_order
- certified_partial_order
- number_of_rank_changes
- undecided_edges
- claim_status

## Required Figures

### Figure 1 — Conceptual Pipeline

No result numbers. Shows:

released samples → feature cache → metric stream → CS/e-process → decision certificate → audit/report.

### Figure 2 — Optional-Stopping Validity Lab

Can use synthetic/simulation data if clearly marked as methodological validation, not real benchmark evidence.

### Figure 3 — Samples-to-Decision Curves

Placeholder until real runs.

### Figure 4 — Decidedness/Raking Stability Heatmap

Placeholder until real runs.

### Figure 5 — Metric Disagreement / Comparison Cards

Placeholder until real runs.

## Result Placeholder Token

Use the exact placeholder token:

`TBD_REAL_RUN_REQUIRED`

The audit should fail if numeric-looking placeholders appear in result tables without evidence.

## Contract Fields

Every result contract item should include:

- `artifact_id`
- `artifact_type`: `table|figure|card|appendix_table`
- `required_inputs`
- `required_evidence_status`
- `allowed_pre_run`
- `placeholder_required_before_run`
- `claim_allowed_condition`
- `validation_command`

## Tests

Tests should confirm:

- all required tables/figures are registered;
- placeholders are present before run;
- numeric fake values fail;
- `claim_allowed=true` fails without evidence;
- result contracts can be loaded by reporting code.
