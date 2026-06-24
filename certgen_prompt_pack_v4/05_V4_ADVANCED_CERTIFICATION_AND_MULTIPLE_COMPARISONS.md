# 05 — V4 Advanced Certification and Multiple Comparisons

Upgrade the certificate layer from single-comparison smoke functionality to a multi-comparison audit engine.

## Goal

A CVPR paper will not compare only one pair. It will audit many model pairs, metrics, datasets, and sample budgets. V4 should add conservative handling for multiple comparisons, ranking stability, dependence diagnostics, and sensitivity reports.

## Implement

Create or update:

- `certgen/certs/batch_certificate.py`
- `certgen/certs/multiple_comparisons.py`
- `certgen/certs/sensitivity.py`
- `certgen/stats/dependence_diagnostics.py`
- `certgen/cli/run_batch_certificates.py`
- `docs/V4_ADVANCED_CERTIFICATION.md`
- tests.

## Required features

### Batch certificates

Run certificates over:

- multiple model pairs,
- multiple metrics,
- multiple sample budgets,
- multiple seeds/orderings if available.

### Multiple-comparison policy

Implement at least two conservative policies:

1. Bonferroni / alpha spending across comparisons.
2. Report-only unadjusted mode with explicit “exploratory/non-claim” flag.

Optional: anytime alpha-investing/e-value aggregation only if implemented correctly and clearly labeled.

### Sensitivity analysis

For each comparison, output:

- decision under metric A/B/C;
- decision under different sample order seeds;
- decision under different max budgets;
- decision under adjusted vs unadjusted alpha;
- samples-to-decision distribution if repeated streams exist.

### Dependence diagnostics

Add diagnostics for:

- overlapping reference samples;
- shared generated samples across comparisons;
- same model appearing in many pairs;
- reused feature cache;
- cluster/correlation warning.

Do not overclaim independent comparisons when dependence exists.

## Batch result schema

Each row should contain:

- `comparison_id`
- `metric_name`
- `alpha_policy`
- `alpha_used`
- `n_max`
- `n_decision`
- `decision` (`A_better`, `B_better`, `undecided`)
- `cs_lower`
- `cs_upper`
- `adjusted_for_multiplicity`
- `dependence_warning`
- `evidence_status`
- `claim_allowed`

## Acceptance criteria

- Batch certificate works on synthetic fixtures.
- Multiple-comparison policy is visible in report.
- Claim gate blocks unadjusted exploratory results from becoming paper claims.
- Dependence warnings appear when samples/reference caches are reused.
- Tests cover adjusted and unadjusted modes.
