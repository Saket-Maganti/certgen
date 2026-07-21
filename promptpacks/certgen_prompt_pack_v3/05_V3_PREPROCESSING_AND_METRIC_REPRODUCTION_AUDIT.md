# Prompt 05 — Preprocessing and Metric Reproduction Audit

Implement a metric-reproduction audit that checks whether computed point estimates match expected/reference values under declared preprocessing.

## Goal

Before any certificate is trusted, CertGen must prove the feature caches and metric code reproduce known point estimates or internally consistent reference values.

Create:

- `certgen/audit/metric_reproduction.py`
- `certgen/cli/audit_metric_reproduction.py`
- `docs/METRIC_REPRODUCTION_AUDIT_GUIDE.md`

## Inputs

A JSON/YAML config:

```yaml
audit_id: first_pilot_reproduction
metric: kid
reference_features:
  npz: path/to/real_features.npz
  sidecar: path/to/real_features.json
model_features:
  npz: path/to/model_features.npz
  sidecar: path/to/model_features.json
expected:
  source: "published|internal_fixture|none"
  value: 0.00123
  tolerance_abs: 0.0005
  tolerance_rel: 0.10
preprocessing_id: inception_v3_pool3_299_bicubic_center
sample_count: 5000
seed: 0
```

## Behavior

The audit should:
- validate both feature caches;
- verify preprocessing compatibility;
- compute requested metric point estimate;
- compare to expected value if provided;
- produce a pass/warn/fail status;
- record exact sample count and seed;
- reject if metric is unsupported for rigorous certification;
- mark FID/FD results as descriptive.

## No expected value mode

If `expected.source=none`, emit:
- `reproduction_status="not_applicable_no_expected_value"`
- warning: no published reproduction claim possible
- still compute point estimate for internal sanity.

## Outputs

Markdown and JSON.

JSON:

```json
{
  "audit_name": "metric_reproduction",
  "metric": "kid",
  "computed_value": 0.0,
  "expected_value": null,
  "within_tolerance": null,
  "preprocessing_match": true,
  "feature_caches_validated": true,
  "evidence_status": "real_features_validated",
  "claim_allowed": false
}
```

## Tests

Use synthetic feature fixtures:
- identical distributions;
- shifted distributions;
- expected value within tolerance;
- expected value outside tolerance;
- preprocessing mismatch;
- FID descriptive-only flag.

## Docs

Explain why preprocessing/reproduction matters and why mismatch blocks pilot claims.

## Verification

Run pytest and a synthetic audit command.
